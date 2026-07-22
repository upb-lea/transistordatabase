"""
TransistorSelector: loads the TDB, filters candidates, estimates losses,
ranks results.

Usage
-----
    from selector.selector import TransistorSelector
    from selector.models import CircuitRequirements, Topology

    sel = TransistorSelector()          # loads DB once
    req = CircuitRequirements(
        topology=Topology.BUCK,
        v_bus=400, v_out=200, i_load=20, f_sw=50_000,
    )
    response = sel.select(req)
    for r in response.results[:5]:
        print(r.name, r.losses.p_total_w)
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import transistordatabase as tdb

from .loss_engine import (
    compute_waveform,
    data_confidence,
    estimate_losses,
    missing_data_notes,
)
from .models import (
    CircuitRequirements,
    CurrentWaveform,
    SelectionResponse,
    TransistorResult,
)

logger = logging.getLogger(__name__)


class TransistorSelector:
    """
    Stateful selector that keeps the TDB loaded in memory.

    Parameters
    ----------
    db_path : str | Path | None
        Path to the JSON transistor database folder.
        Defaults to the library's built-in database location.
    """

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self._db = tdb.DatabaseManager()

        if db_path is not None:
            resolved = Path(db_path).expanduser().resolve()
            if not resolved.is_dir():
                raise FileNotFoundError(
                    f"Transistor database folder not found: {resolved}"
                )
            self._db.set_operation_mode_json(str(resolved))
        else:
            # Library default: <site-packages>/transistordatabase/../database/
            self._db.set_operation_mode_json()

        self._db_path = str(
            self._db.json_folder if hasattr(self._db, "json_folder") else db_path or "default"
        )

        # Eager-load all transistors once
        logger.info("Loading all transistors from %s …", self._db_path)
        self._transistors: list[tdb.Transistor] = self._load_all()
        logger.info("Loaded %d transistors.", len(self._transistors))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_all(self) -> list[tdb.Transistor]:
        """Return all transistors from the database, skipping broken entries."""
        names = self._db.get_transistor_names_list()
        result: list[tdb.Transistor] = []
        for name in names:
            try:
                t = self._db.load_transistor(name)
                result.append(t)
            except Exception as exc:
                logger.warning("Skipping %s — load error: %s", name, exc)
        return result

    def _passes_filters(
        self,
        t: tdb.Transistor,
        req: CircuitRequirements,
        wf: CurrentWaveform,
    ) -> tuple[bool, str]:
        """
        Return (True, '') if the transistor meets hard constraints, else
        (False, reason).
        """
        # Voltage margin
        if t.v_abs_max < req.v_bus * req.v_margin:
            return False, (
                f"V_abs_max={t.v_abs_max:.0f}V < {req.v_bus:.0f}·{req.v_margin}={req.v_bus * req.v_margin:.0f}V"
            )
        # Current margin
        if t.i_abs_max < wf.i_peak * req.i_margin:
            return False, (
                f"I_abs_max={t.i_abs_max:.0f}A < {wf.i_peak:.1f}·{req.i_margin}={wf.i_peak * req.i_margin:.1f}A"
            )
        # Junction temperature headroom
        t_j_max = getattr(t.switch, "t_j_max", None) or getattr(t, "t_c_max", None)
        if t_j_max is not None and req.t_j_op > t_j_max:
            return False, (
                f"t_j_op={req.t_j_op:.0f}°C > t_j_max={t_j_max:.0f}°C"
            )
        # Type filter
        if req.allowed_types:
            allowed_strs = {tt.value for tt in req.allowed_types}
            if t.type not in allowed_strs:
                return False, f"type={t.type} not in allowed_types"

        return True, ""

    @staticmethod
    def _ranking_key(r: TransistorResult) -> tuple[float, float]:
        """
        Primary sort: total estimated loss (W), ascending.
        Secondary sort: data confidence (%), descending → negate.

        Transistors with zero estimable data end up at the bottom.
        """
        if r.data_confidence_pct == 0.0:
            return (1e9, -r.data_confidence_pct)
        return (r.losses.p_total_w, -r.data_confidence_pct)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def transistor_count(self) -> int:
        """Number of transistors currently loaded."""
        return len(self._transistors)

    @property
    def db_path(self) -> str:
        return self._db_path

    def list_names(self) -> list[str]:
        """Return all transistor names in the database."""
        return [t.name for t in self._transistors]

    def get_transistor(self, name: str) -> Optional[tdb.Transistor]:
        """Look up a transistor by exact name."""
        for t in self._transistors:
            if t.name == name:
                return t
        return None

    def select(self, req: CircuitRequirements) -> SelectionResponse:
        """
        Main selection pipeline.

        1. Compute current waveform for the topology.
        2. Filter transistors that pass hard constraints (V/I/T margins, type).
        3. Estimate losses for each candidate.
        4. Rank by (total loss ↑, data confidence ↓).
        5. Return top ``req.max_results`` with full breakdown.

        Parameters
        ----------
        req : CircuitRequirements

        Returns
        -------
        SelectionResponse
        """
        warnings: list[str] = []

        # 1. Waveform
        wf = compute_waveform(req)

        if wf.duty_cycle < 0.05 or wf.duty_cycle > 0.95:
            warnings.append(
                f"Duty cycle D={wf.duty_cycle:.2f} is extreme — "
                "CCM approximation may be inaccurate near D→0 or D→1."
            )

        # 2. Filter
        candidates: list[tdb.Transistor] = []
        for t in self._transistors:
            ok, reason = self._passes_filters(t, req, wf)
            if ok:
                candidates.append(t)
            else:
                logger.debug("Rejected %s: %s", t.name, reason)

        if not candidates:
            warnings.append(
                "No transistors passed the voltage/current/type filters. "
                "Try reducing v_margin or i_margin, or widening allowed_types."
            )

        # 3. Estimate losses
        ranked: list[TransistorResult] = []
        for t in candidates:
            try:
                losses = estimate_losses(t, wf, req)
            except Exception as exc:
                logger.warning("Loss estimation failed for %s: %s", t.name, exc)
                continue

            conf = data_confidence(t, losses)
            notes = missing_data_notes(t, losses)

            t_j_max = float(
                getattr(t.switch, "t_j_max", None)
                or getattr(t, "t_c_max", None)
                or 175.0
            )
            r_th_cs = float(t.r_th_cs) if t.r_th_cs else None

            ranked.append(
                TransistorResult(
                    rank=0,  # filled after sort
                    name=t.name,
                    transistor_type=t.type,
                    housing_type=t.housing_type or "unknown",
                    manufacturer=t.manufacturer or "unknown",
                    v_abs_max=t.v_abs_max,
                    i_abs_max=t.i_abs_max,
                    i_cont=t.i_cont,
                    t_j_max=t_j_max,
                    r_g_int=float(t.r_g_int) if t.r_g_int else 0.0,
                    r_th_cs=r_th_cs,
                    v_derating=round(t.v_abs_max / req.v_bus, 2),
                    i_derating=round(t.i_abs_max / wf.i_peak, 2),
                    losses=losses,
                    data_confidence_pct=conf,
                    missing_data_notes=notes,
                )
            )

        # 4. Sort & assign ranks
        ranked.sort(key=self._ranking_key)
        for idx, r in enumerate(ranked, start=1):
            r.rank = idx

        # 5. Truncate
        top_n = ranked[: req.max_results]

        return SelectionResponse(
            requirements=req,
            waveform=wf,
            results=top_n,
            total_candidates=len(candidates),
            total_in_db=len(self._transistors),
            warnings=warnings,
        )
