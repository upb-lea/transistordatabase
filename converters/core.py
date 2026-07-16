"""
converters/core.py
------------------
Self-contained device wrapper that reads transistor JSON files directly
and provides the interpolation primitives needed by the topology modules.

No dependency on the external 'transistordatabase' library.
"""

import json
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ConverterError(Exception):
    """Raised when required curve data is missing or interpolation fails."""


# ---------------------------------------------------------------------------
# ConverterDevice
# ---------------------------------------------------------------------------

class ConverterDevice:
    """
    Wraps a transistor JSON file and exposes the interpolation methods
    required by the boost / buck / buck-boost topology modules.

    Attributes exposed (read-only after __init__):
        name            str
        device_type     str   e.g. 'IGBT', 'SiC-MOSFET'
        i_abs_max       float
        v_abs_max       float
        r_th_cs         float   case-to-sink thermal resistance [K/W]
        r_th_switch_cs  float
        r_th_diode_cs   float
        r_th_switch_jc  float   from thermal_foster (switch)
        r_th_diode_jc   float   from thermal_foster (diode), or 0 if absent
        has_e_on        bool
        has_e_off       bool
        has_e_rr        bool
        has_diode_tf    bool
    """

    def __init__(self, json_path: str):
        with open(json_path, "r", encoding="utf-8") as fh:
            self._d = json.load(fh)

        self.name        = self._d.get("name", "Unknown")
        self.device_type = self._d.get("type", "Unknown")
        self.json_path   = json_path

        def _float(key, default=0.0):
            v = self._d.get(key)
            try:    return float(v) if v not in (None, "") else default
            except: return default

        self.i_abs_max      = _float("i_abs_max", 9999.0)
        self.v_abs_max      = _float("v_abs_max", 9999.0)
        self.r_th_cs        = _float("r_th_cs",   0.0)
        self.r_th_switch_cs = _float("r_th_switch_cs", 0.0)
        self.r_th_diode_cs  = _float("r_th_diode_cs",  0.0)

        sw = self._d.get("switch", {})
        di = self._d.get("diode",  {})

        # ---- Foster thermal (switch) ----
        tf_sw = sw.get("thermal_foster", {}) or {}
        self.r_th_switch_jc = self._foster_r_total(tf_sw)

        # ---- Foster thermal (diode) ----
        tf_di = di.get("thermal_foster", {}) or {}
        self.r_th_diode_jc  = self._foster_r_total(tf_di)
        self.has_diode_tf   = self.r_th_diode_jc > 0.0

        # ---- Pre-build lookup tables for channel linearisation ----
        self._sw_channels = self._parse_channels(sw.get("channel", []))
        self._di_channels = self._parse_channels(di.get("channel", []))

        # ---- Switching energy curves ----
        self._e_on  = self._parse_energy(sw.get("e_on",  []))
        self._e_off = self._parse_energy(sw.get("e_off", []))
        self._e_rr  = self._parse_energy(di.get("e_rr",  []))

        # ---- Gate-resistor rescaling curves (graph_r_e) ----
        self._e_on_re  = self._parse_r_e(sw.get("e_on",  []))
        self._e_off_re = self._parse_r_e(sw.get("e_off", []))
        self._e_rr_re  = self._parse_r_e(di.get("e_rr",  []))

        self.has_e_on  = len(self._e_on)  > 0
        self.has_e_off = len(self._e_off) > 0
        self.has_e_rr  = len(self._e_rr)  > 0

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _foster_r_total(tf: dict) -> float:
        """Return R_th_total from a thermal_foster dict (switch or diode)."""
        if not tf:
            return 0.0
        # prefer pre-computed total
        r_tot = tf.get("r_th_total")
        if r_tot not in (None, ""):
            try: return float(r_tot)
            except: pass
        # fall back to sum of vector
        r_vec = tf.get("r_th_vector")
        if isinstance(r_vec, list) and r_vec:
            try: return float(sum(r_vec))
            except: pass
        return 0.0

    @staticmethod
    def _parse_channels(channel_list: list) -> list:
        """Return list of dicts with keys t_j, v_g, v_pts, i_pts (numpy arrays)."""
        out = []
        for ch in channel_list:
            if not isinstance(ch, dict):
                continue
            gvi = ch.get("graph_v_i")
            if not (isinstance(gvi, list) and len(gvi) == 2
                    and isinstance(gvi[0], list) and len(gvi[0]) > 1):
                continue
            out.append({
                "t_j":   float(ch.get("t_j", 25)),
                "v_g":   float(ch.get("v_g", 0)) if ch.get("v_g") is not None else 0.0,
                "v_pts": np.asarray(gvi[0], dtype=float),
                "i_pts": np.asarray(gvi[1], dtype=float),
            })
        return out

    @staticmethod
    def _parse_energy(energy_list: list) -> list:
        """Return list of dicts for graph_i_e entries only."""
        out = []
        for e in energy_list:
            if not isinstance(e, dict):
                continue
            if e.get("dataset_type") != "graph_i_e":
                continue
            gie = e.get("graph_i_e")
            if not (isinstance(gie, list) and len(gie) == 2
                    and isinstance(gie[0], list) and len(gie[0]) > 1):
                continue
            out.append({
                "t_j":      float(e.get("t_j",      25)),
                "v_g":      float(e.get("v_g",       0)) if e.get("v_g") is not None else 0.0,
                "v_supply": float(e.get("v_supply",  0)) if e.get("v_supply") is not None else 0.0,
                "r_g":      float(e.get("r_g",       0)) if e.get("r_g") is not None else 0.0,
                "i_pts":    np.asarray(gie[0], dtype=float),
                "e_pts":    np.asarray(gie[1], dtype=float),
            })
        return out

    @staticmethod
    def _parse_r_e(energy_list: list) -> list:
        """Return list of dicts for graph_r_e entries only.
        Used to rescale a graph_i_e curve to a non-datasheet gate resistor,
        mirroring transistordatabase.calc_i_e_curve_using_r_e_curve."""
        out = []
        for e in energy_list:
            if not isinstance(e, dict):
                continue
            if e.get("dataset_type") != "graph_r_e":
                continue
            gre = e.get("graph_r_e")
            if not (isinstance(gre, list) and len(gre) == 2
                    and isinstance(gre[0], list) and len(gre[0]) > 1):
                continue
            out.append({
                "t_j":      float(e.get("t_j",      25)),
                "v_g":      float(e.get("v_g",       0)) if e.get("v_g") is not None else 0.0,
                "v_supply": float(e.get("v_supply",  0)) if e.get("v_supply") is not None else 0.0,
                "r_pts":    np.asarray(gre[0], dtype=float),
                "e_pts":    np.asarray(gre[1], dtype=float),
            })
        return out

    # ------------------------------------------------------------------
    # Channel linearisation  (matches transistordatabase.calc_lin_channel)
    # ------------------------------------------------------------------

    def _best_channel(self, channels: list, t_j: float, v_g: float) -> dict:
        """Return the channel entry closest to (t_j, v_g) in Euclidean space."""
        if not channels:
            raise ConverterError(f"{self.name}: no channel data available.")
        norm = 10.0   # 10 °C ≡ 1 V  (same as reference library)
        node = np.array([t_j / norm, v_g])
        dists = [np.linalg.norm(np.array([c["t_j"] / norm, c["v_g"]]) - node)
                 for c in channels]
        return channels[int(np.argmin(dists))]

    def calc_lin_channel(self, i_channel: float, t_j: float, v_g: float,
                         switch_or_diode: str) -> tuple[float, float]:
        """
        Return (v_channel, r_channel) linearised at i_channel.

        For MOSFET/SiC-MOSFET: v_channel = 0, r_channel = V(I)/I.
        For IGBT/diode: two-point slope to extract R and V_0.

        Returns (0.0, 0.0) if data is insufficient (safe fallback).
        """
        channels = (self._sw_channels if switch_or_diode == "switch"
                    else self._di_channels)
        if not channels:
            return 0.0, 0.0

        ch = self._best_channel(channels, t_j, v_g)
        v_pts, i_pts = ch["v_pts"], ch["i_pts"]

        if i_channel <= 0:
            return 0.0, 0.0

        i_channel = min(i_channel, i_pts[-1])
        v1 = float(np.interp(i_channel,       i_pts, v_pts))
        v2 = float(np.interp(i_channel * 0.9, i_pts, v_pts))
        di = 0.1 * i_channel

        is_mosfet = self.device_type in ("MOSFET", "SiC-MOSFET", "GaN-Transistor")

        if switch_or_diode == "switch" and is_mosfet:
            r_ch = v1 / i_channel if i_channel > 0 else 0.0
            v_ch = 0.0
        else:
            if di < 1e-9:
                return 0.0, v1 / i_channel if i_channel > 0 else 0.0
            r_ch = (v1 - v2) / di
            v_ch = v1 - r_ch * i_channel

        return round(max(v_ch, 0.0), 6), round(max(r_ch, 0.0), 9)

    def channel_voltage(self, i_channel: float, t_j: float, v_g: float,
                        switch_or_diode: str) -> float:
        """Return V = v_0 + r * I  (total forward voltage at i_channel)."""
        v0, r = self.calc_lin_channel(i_channel, t_j, v_g, switch_or_diode)
        return v0 + r * i_channel

    # ------------------------------------------------------------------
    # Gate-resistor rescaling  (matches transistordatabase.calc_object_i_e /
    # calc_i_e_curve_using_r_e_curve)
    # ------------------------------------------------------------------

    def rescale_energy_for_rg(self, which: str, r_g: float, t_j: float,
                              v_supply: Optional[float] = None) -> Optional[dict]:
        """
        Return a rescaled {'i_pts', 'e_pts', 'v_supply'} energy curve for a
        non-datasheet gate resistor, using the graph_r_e correction curve.

        Mirrors the reference algorithm exactly:
            factor = E_re(r_g_chosen) / E_re(r_g_nominal)
            E_new(I) = factor * E_nominal(I) * (v_supply_chosen / v_supply_nominal)

        which: 'e_on' | 'e_off' | 'e_rr'
        r_g: requested external gate resistor [Ohm]
        t_j: requested junction temperature (closest available curve is used)
        v_supply: requested supply voltage (defaults to the nominal curve's value)

        Returns None if graph_r_e data is unavailable (caller should fall
        back to the unscaled graph_i_e curve via interp_energy()).
        """
        ie_tbl = {"e_on": self._e_on, "e_off": self._e_off, "e_rr": self._e_rr}
        re_tbl = {"e_on": self._e_on_re, "e_off": self._e_off_re, "e_rr": self._e_rr_re}

        ie_entries = ie_tbl.get(which, [])
        re_entries = re_tbl.get(which, [])
        if not ie_entries or not re_entries:
            return None

        ie_entry = self._best_energy(ie_entries, t_j)
        re_entry = self._best_energy(re_entries, t_j)
        if ie_entry is None or re_entry is None:
            return None

        r_pts, e_re_pts = re_entry["r_pts"], re_entry["e_pts"]
        r_g_max = float(np.max(r_pts))
        if r_g > r_g_max:
            # mirror reference: clamp instead of raising, but flag via None upstream is too strict;
            # clamping keeps the converter usable while staying close to datasheet bounds
            r_g = r_g_max

        r_g_nominal = ie_entry["r_g"]
        loss_at_rg     = float(np.interp(r_g,         r_pts, e_re_pts))
        loss_at_rg_nom = float(np.interp(r_g_nominal, r_pts, e_re_pts))
        factor = loss_at_rg / loss_at_rg_nom if loss_at_rg_nom > 0 else 1.0

        v_supply_nominal = ie_entry["v_supply"]
        v_supply_chosen  = v_supply if v_supply else v_supply_nominal
        v_factor = v_supply_chosen / v_supply_nominal if v_supply_nominal > 0 else 1.0

        e_pts_new = ie_entry["e_pts"] * factor * v_factor

        return {
            "i_pts": ie_entry["i_pts"],
            "e_pts": e_pts_new,
            "v_supply": v_supply_chosen,
        }

    # ------------------------------------------------------------------
    # Energy interpolation
    # ------------------------------------------------------------------

    def _best_energy(self, energy_list: list, t_j: float) -> Optional[dict]:
        """Return the energy entry with t_j closest to requested value."""
        if not energy_list:
            return None
        diffs = [abs(e["t_j"] - t_j) for e in energy_list]
        return energy_list[int(np.argmin(diffs))]

    def interp_energy(self, which: str, i_channel: float, t_j: float,
                      v_out: float) -> float:
        """
        Return interpolated switching energy in Joules at i_channel.

        which: 'e_on' | 'e_off' | 'e_rr'
        v_out: operating output voltage (used for linear voltage scaling)

        Returns 0.0 when data is absent (non-fatal).
        """
        tbl = {"e_on": self._e_on, "e_off": self._e_off, "e_rr": self._e_rr}
        entries = tbl.get(which, [])
        entry = self._best_energy(entries, t_j)
        if entry is None:
            return 0.0

        i_pts, e_pts = entry["i_pts"], entry["e_pts"]
        i_clamp = float(np.clip(i_channel, i_pts[0], i_pts[-1]))
        e_j = float(np.interp(i_clamp, i_pts, e_pts))

        # Linear voltage scaling (same as reference library)
        v_supply = entry["v_supply"]
        if v_supply > 0 and v_out > 0:
            e_j *= v_out / v_supply

        return max(e_j, 0.0)

    # ------------------------------------------------------------------
    # Convenience properties for topology modules
    # ------------------------------------------------------------------

    def max_t_j_switch(self) -> float:
        """Highest t_j available in switch channel data."""
        if not self._sw_channels:
            return 25.0
        return max(c["t_j"] for c in self._sw_channels)

    def max_t_j_diode(self) -> float:
        """Highest t_j available in diode channel data."""
        if not self._di_channels:
            return 25.0
        return max(c["t_j"] for c in self._di_channels)

    def max_v_g_switch(self) -> float:
        """Highest gate voltage in switch channel data."""
        if not self._sw_channels:
            return 15.0
        return max(c["v_g"] for c in self._sw_channels)

    def max_t_j_e_on(self) -> float:
        if not self._e_on: return 25.0
        return max(e["t_j"] for e in self._e_on)

    def max_t_j_e_off(self) -> float:
        if not self._e_off: return 25.0
        return max(e["t_j"] for e in self._e_off)

    def max_t_j_e_rr(self) -> float:
        if not self._e_rr: return 25.0
        return max(e["t_j"] for e in self._e_rr)

    def __repr__(self) -> str:
        return (f"ConverterDevice('{self.name}', type={self.device_type}, "
                f"i_abs_max={self.i_abs_max} A, v_abs_max={self.v_abs_max} V)")