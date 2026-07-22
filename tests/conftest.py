"""
Shared fixtures for the transistor database test suite.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import types
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Fake ConverterDevice — known, simple linear characteristics
# ---------------------------------------------------------------------------
class FakeDevice:
    """
    Stand-in for converters.core.ConverterDevice.

    Switch:  MOSFET model — V0 = 0 V,   R = R_sw Ω
    Diode:   Diode model  — V0 = V0_d V, R = R_d  Ω
    """
    device_type = "SiC-MOSFET"
    i_abs_max   = 200.0
    v_abs_max   = 1200.0
    r_th_cs = r_th_switch_cs = r_th_diode_cs = 0.0
    r_th_switch_jc = 0.10
    r_th_diode_jc  = 0.05
    has_e_on = has_e_off = has_e_rr = False
    has_diode_tf = True

    def __init__(self, v0_sw=0.0, r_sw=0.016, v0_d=1.2, r_d=0.015, name="FakeDevice"):
        self.name  = name
        self._v0_sw, self._r_sw = v0_sw, r_sw
        self._v0_d,  self._r_d  = v0_d,  r_d

    def max_t_j_switch(self): return 175.0
    def max_t_j_diode(self):  return 175.0
    def max_t_j_e_on(self):   return 175.0
    def max_t_j_e_off(self):  return 175.0
    def max_t_j_e_rr(self):   return 175.0

    def calc_lin_channel(self, i: float, t_j: float, v_g: float, side: str):
        """Return (V_0, R) for the requested side."""
        if side == "switch":
            return (self._v0_sw, self._r_sw)
        return (self._v0_d, self._r_d)


@pytest.fixture
def mosfet_diode_pair():
    """(t1, t2) with V0_sw=0, R_sw=16mΩ, V0_d=1.2V, R_d=15mΩ."""
    t1 = FakeDevice(v0_sw=0.0, r_sw=0.016, v0_d=1.2, r_d=0.015, name="T1")
    t2 = FakeDevice(v0_sw=0.0, r_sw=0.016, v0_d=1.2, r_d=0.015, name="T2")
    return t1, t2


@pytest.fixture(scope="session")
def szukaj_mod():
    """
    Import szukaj.py with its side-effectful module-level code neutralised:
      - subprocess.check_call (pip auto-install) is mocked out
      - readline / pyreadline3 are stubbed if unavailable
    Returns the loaded module.
    """
    fake_readline = MagicMock()
    fake_pypdf    = MagicMock()
    fake_pypdf.PdfReader = MagicMock

    extra = {
        "pyreadline3": MagicMock(),
    }
    # Only stub readline if it's not natively available
    try:
        import readline  # noqa: F401
    except ImportError:
        extra["readline"] = fake_readline

    with patch.dict(sys.modules, extra):
        with patch("subprocess.check_call"):
            spec = importlib.util.spec_from_file_location(
                "szukaj", os.path.join(PROJECT_ROOT, "szukaj.py")
            )
            mod = importlib.util.module_from_spec(spec)
            sys.modules["szukaj"] = mod
            spec.loader.exec_module(mod)
    return mod