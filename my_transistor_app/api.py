"""
FastAPI application for the power transistor selector.

Start with:
    uvicorn api:app --reload --host 0.0.0.0 --port 8000

Endpoints
---------
GET  /health                          – liveness + DB stats
GET  /transistors                     – list all transistor names
GET  /transistors/{name}              – single transistor detail
POST /select                          – ranked selection (main endpoint)
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from selector.models import (
    CircuitRequirements,
    HealthResponse,
    SelectionResponse,
    TransistorResult,
)
from selector.selector import TransistorSelector

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# App lifespan: create selector once, reuse across requests
# ---------------------------------------------------------------------------
_selector: TransistorSelector | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load DB on startup; clean up on shutdown."""
    global _selector
    db_path = os.environ.get("TDB_PATH")  # override with env var if needed
    logger.info("Initialising TransistorSelector (db_path=%s) …", db_path or "default")
    _selector = TransistorSelector(db_path=db_path)
    logger.info("Ready. %d transistors loaded.", _selector.transistor_count)
    yield
    logger.info("Shutting down.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Power Transistor Selector",
    description=(
        "Enter circuit requirements (topology, V_bus, I_load, f_sw) "
        "and receive a ranked list of suitable power switches with "
        "estimated conduction and switching losses."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_selector() -> TransistorSelector:
    if _selector is None:
        raise HTTPException(status_code=503, detail="Database not yet loaded.")
    return _selector


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    """Liveness check and database statistics."""
    sel = _get_selector()
    return HealthResponse(
        status="ok",
        transistors_loaded=sel.transistor_count,
        db_path=sel.db_path,
    )


@app.get("/transistors", response_model=list[str], tags=["database"])
def list_transistors(
    q: str | None = Query(default=None, description="Optional name substring filter"),
) -> list[str]:
    """Return all (or filtered) transistor names in the database."""
    sel = _get_selector()
    names = sel.list_names()
    if q:
        q_lower = q.lower()
        names = [n for n in names if q_lower in n.lower()]
    return sorted(names)


@app.get("/transistors/{name}", response_model=dict[str, Any], tags=["database"])
def get_transistor(name: str) -> dict[str, Any]:
    """
    Return basic metadata for a single transistor.

    Raises 404 if the name is not in the database.
    """
    sel = _get_selector()
    t = sel.get_transistor(name)
    if t is None:
        raise HTTPException(status_code=404, detail=f"Transistor '{name}' not found.")
    return {
        "name": t.name,
        "type": t.type,
        "manufacturer": t.manufacturer,
        "housing_type": t.housing_type,
        "v_abs_max": t.v_abs_max,
        "i_abs_max": t.i_abs_max,
        "i_cont": t.i_cont,
        "r_g_int": t.r_g_int,
        "r_th_cs": t.r_th_cs,
        "r_th_switch_cs": t.r_th_switch_cs,
        "t_j_max_switch": getattr(t.switch, "t_j_max", None),
        "t_j_max_diode": getattr(t.diode, "t_j_max", None),
        "switch_channel_count": len(t.switch.channel) if t.switch.channel else 0,
        "e_on_dataset_count": len(t.switch.e_on) if t.switch.e_on else 0,
        "e_off_dataset_count": len(t.switch.e_off) if t.switch.e_off else 0,
        "diode_channel_count": len(t.diode.channel) if t.diode.channel else 0,
        "e_rr_dataset_count": len(t.diode.e_rr) if t.diode.e_rr else 0,
    }


@app.post("/select", response_model=SelectionResponse, tags=["selection"])
def select_transistors(req: CircuitRequirements) -> SelectionResponse:
    """
    Rank transistors for the given circuit requirements.

    The response includes:
    * The computed current waveform (D, I_rms, I_peak, …)
    * A ranked list of transistors with per-component loss breakdown
    * Data-confidence percentage per transistor
    * Notes on missing or extrapolated data

    **Loss model assumptions**
    - CCM (continuous conduction mode), low current ripple.
    - Linear voltage scaling: E(V) ≈ E_meas · (V / V_meas).
    - Single phase-leg (one switch + one anti-parallel diode).
    - Junction temperature is fixed at `t_j_op` (no thermal iteration).
    """
    sel = _get_selector()
    return sel.select(req)
