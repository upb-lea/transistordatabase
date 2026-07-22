"""
converters/formulas.py
----------------------
Duty-cycle and current waveform formulas for boost, buck and buck-boost
converters in CCM and DCM, vectorised over numpy arrays.

All functions accept numpy arrays so results can be plotted as heat-maps.
Scalar inputs are promoted automatically by numpy.

Conventions
-----------
zeta        = L * f / R_load   (normalised inductance, dimensionless)
v_ch1       = total forward voltage across T1 (switch)
v_ch2       = total forward voltage across T2 (diode / second switch)
All voltages in V, currents in A, power in W.
"""

import numpy as np


# ============================================================
# CCM / DCM boundary helpers  (topology-independent)
# ============================================================

def _safe_sqrt(x):
    """sqrt clamped to 0 for negative inputs (unphysical operating points
    that will be masked later by mask_invalid in analysis.py)."""
    return np.sqrt(np.maximum(x, 0.0))

def _ccm_boundary(duty_ccm, v_switch, zeta, v_out):
    """Power level that marks the CCM/DCM boundary."""
    return v_out * duty_ccm * (v_switch / (2.0 * zeta))


# ============================================================
# BOOST
# ============================================================

class Boost:
    """Static methods for the boost converter waveform formulas."""

    @staticmethod
    def duty_ccm(v_in, v_out, v_ch1, v_ch2):
        return (-v_in + v_out + v_ch2) / (v_out - v_ch1 + v_ch2)

    @staticmethod
    def duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        num = 2.0 * zeta * p_out
        den = v_out * (v_in - v_ch1) * (1.0 + (v_in - v_ch1) / (-v_in + v_out + v_ch2))
        return np.sqrt(np.maximum(num / np.maximum(den, 1e-12), 0.0))

    @staticmethod
    def v_switch(v_in, v_ch1):          # voltage stress on switch element
        return v_in - v_ch1

    @staticmethod
    def i_peak(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = Boost.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = Boost.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = Boost.v_switch(v_in, v_ch1)

        i_max_ccm  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_peak_dcm = v_sw * d_dcm / zeta
        boundary   = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        out = np.where(p_out >= boundary, i_max_ccm, i_peak_dcm)
        return np.maximum(out, 0.0)

    @staticmethod
    def i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm = Boost.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        v_sw  = Boost.v_switch(v_in, v_ch1)
        return p_out / v_out - v_sw * d_ccm / (2.0 * zeta)

    @staticmethod
    def i1_rms(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = Boost.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = Boost.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = Boost.v_switch(v_in, v_ch1)
        i_min  = Boost.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        i_max  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_pk_d = v_sw * d_dcm / zeta
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        rms_ccm = _safe_sqrt(d_ccm * (i_min**2 + i_min*i_max + i_max**2) / 3.0)
        rms_dcm = _safe_sqrt(d_dcm * i_pk_d**2 / 3.0)
        return np.where(p_out >= boundary, rms_ccm, rms_dcm)

    @staticmethod
    def i1_mean(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = Boost.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = Boost.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = Boost.v_switch(v_in, v_ch1)
        i_min  = Boost.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        i_max  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_pk_d = v_sw * d_dcm / zeta
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        mean_ccm = d_ccm * (i_min + i_max) / 2.0
        mean_dcm = d_dcm * i_pk_d / 2.0
        return np.where(p_out >= boundary, mean_ccm, mean_dcm)

    @staticmethod
    def i2_rms(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = Boost.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = Boost.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = Boost.v_switch(v_in, v_ch1)
        d_dcm2 = d_dcm * v_sw / np.maximum(-v_in + v_out + v_ch2, 1e-9)
        i_min  = Boost.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        i_max  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_pk_d = v_sw * d_dcm / zeta
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        rms_ccm = _safe_sqrt((1 - d_ccm) * (i_min**2 + i_min*i_max + i_max**2) / 3.0)
        rms_dcm = _safe_sqrt(d_dcm2 * i_pk_d**2 / 3.0)
        return np.where(p_out >= boundary, rms_ccm, rms_dcm)

    @staticmethod
    def i2_mean(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = Boost.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = Boost.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = Boost.v_switch(v_in, v_ch1)
        d_dcm2 = d_dcm * v_sw / np.maximum(-v_in + v_out + v_ch2, 1e-9)
        i_min  = Boost.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        i_max  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_pk_d = v_sw * d_dcm / zeta
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        mean_ccm = (1 - d_ccm) * (i_min + i_max) / 2.0
        mean_dcm = d_dcm2 * i_pk_d / 2.0
        return np.where(p_out >= boundary, mean_ccm, mean_dcm)

    # Turn-on current = i_min (CCM) or 0 (DCM)
    @staticmethod
    def i_on_t1(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm    = Boost.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        v_sw     = Boost.v_switch(v_in, v_ch1)
        i_min    = Boost.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)
        return np.where(p_out >= boundary, np.maximum(i_min, 0.0), 0.0)

    # Turn-off current = i_peak (always)
    @staticmethod
    def i_off_t1(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        return Boost.i_peak(zeta, v_in, v_out, p_out, v_ch1, v_ch2)

    # Diode reverse-recovery current = i_min (CCM) or 0 (DCM)
    @staticmethod
    def i_rr_t2(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        return Boost.i_on_t1(zeta, v_in, v_out, p_out, v_ch1, v_ch2)


# ============================================================
# BUCK
# ============================================================

class Buck:
    @staticmethod
    def duty_ccm(v_in, v_out, v_ch1, v_ch2):
        return (v_ch2 + v_out) / (v_in - v_ch1 + v_ch2)

    @staticmethod
    def duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        v_sw = v_in - v_out - v_ch1
        num  = 2.0 * zeta * p_out
        den  = v_out * v_sw * (1.0 + v_sw / np.maximum(v_out + v_ch2, 1e-9))
        return np.sqrt(np.maximum(num / np.maximum(den, 1e-12), 0.0))

    @staticmethod
    def v_switch(v_in, v_out, v_ch1):
        return v_in - v_out - v_ch1

    @staticmethod
    def i_peak(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = Buck.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = Buck.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = Buck.v_switch(v_in, v_out, v_ch1)

        i_max_ccm  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_peak_dcm = v_sw * d_dcm / zeta
        boundary   = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        return np.where(p_out >= boundary, i_max_ccm, i_peak_dcm)

    @staticmethod
    def i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm = Buck.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        v_sw  = Buck.v_switch(v_in, v_out, v_ch1)
        return p_out / v_out - v_sw * d_ccm / (2.0 * zeta)

    @staticmethod
    def i1_rms(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = Buck.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = Buck.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = Buck.v_switch(v_in, v_out, v_ch1)
        i_min  = Buck.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        i_max  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_pk_d = v_sw * d_dcm / zeta
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        rms_ccm = _safe_sqrt(d_ccm * (i_min**2 + i_min*i_max + i_max**2) / 3.0)
        rms_dcm = _safe_sqrt(d_dcm * i_pk_d**2 / 3.0)
        return np.where(p_out >= boundary, rms_ccm, rms_dcm)

    @staticmethod
    def i1_mean(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = Buck.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = Buck.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = Buck.v_switch(v_in, v_out, v_ch1)
        i_min  = Buck.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        i_max  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_pk_d = v_sw * d_dcm / zeta
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        mean_ccm = d_ccm * (i_min + i_max) / 2.0
        mean_dcm = d_dcm * i_pk_d / 2.0
        return np.where(p_out >= boundary, mean_ccm, mean_dcm)

    @staticmethod
    def i2_rms(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = Buck.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = Buck.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = Buck.v_switch(v_in, v_out, v_ch1)
        d_dcm2 = d_dcm * v_sw / np.maximum(v_out + v_ch2, 1e-9)
        i_min  = Buck.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        i_max  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_pk_d = v_sw * d_dcm / zeta
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        rms_ccm = _safe_sqrt((1 - d_ccm) * (i_min**2 + i_min*i_max + i_max**2) / 3.0)
        rms_dcm = _safe_sqrt(d_dcm2 * i_pk_d**2 / 3.0)
        return np.where(p_out >= boundary, rms_ccm, rms_dcm)

    @staticmethod
    def i2_mean(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = Buck.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = Buck.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = Buck.v_switch(v_in, v_out, v_ch1)
        d_dcm2 = d_dcm * v_sw / np.maximum(v_out + v_ch2, 1e-9)
        i_min  = Buck.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        i_max  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_pk_d = v_sw * d_dcm / zeta
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        mean_ccm = (1 - d_ccm) * (i_min + i_max) / 2.0
        mean_dcm = d_dcm2 * i_pk_d / 2.0
        return np.where(p_out >= boundary, mean_ccm, mean_dcm)

    @staticmethod
    def i_on_t1(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm    = Buck.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        v_sw     = Buck.v_switch(v_in, v_out, v_ch1)
        i_min    = Buck.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)
        return np.where(p_out >= boundary, np.maximum(i_min, 0.0), 0.0)

    @staticmethod
    def i_off_t1(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        return Buck.i_peak(zeta, v_in, v_out, p_out, v_ch1, v_ch2)

    @staticmethod
    def i_rr_t2(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        return Buck.i_on_t1(zeta, v_in, v_out, p_out, v_ch1, v_ch2)


# ============================================================
# BUCK-BOOST
# ============================================================

class BuckBoost:
    @staticmethod
    def duty_ccm(v_in, v_out, v_ch1, v_ch2):
        return (v_out + v_ch2) / (v_in + v_out - v_ch1 + v_ch2)

    @staticmethod
    def duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        v_sw = v_in - v_ch1
        num  = 2.0 * zeta * p_out
        den  = v_out * v_sw * (1.0 + v_sw / np.maximum(v_out + v_ch2, 1e-9))
        return np.sqrt(np.maximum(num / np.maximum(den, 1e-12), 0.0))

    @staticmethod
    def v_switch(v_in, v_ch1):
        return v_in - v_ch1

    @staticmethod
    def i_peak(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = BuckBoost.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = BuckBoost.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = BuckBoost.v_switch(v_in, v_ch1)

        i_max_ccm  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_peak_dcm = v_sw * d_dcm / zeta
        boundary   = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        return np.where(p_out >= boundary, i_max_ccm, i_peak_dcm)

    @staticmethod
    def i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm = BuckBoost.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        v_sw  = BuckBoost.v_switch(v_in, v_ch1)
        return p_out / v_out - v_sw * d_ccm / (2.0 * zeta)

    @staticmethod
    def i1_rms(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = BuckBoost.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = BuckBoost.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = BuckBoost.v_switch(v_in, v_ch1)
        i_min  = BuckBoost.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        i_max  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_pk_d = v_sw * d_dcm / zeta
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        rms_ccm = _safe_sqrt(d_ccm * (i_min**2 + i_min*i_max + i_max**2) / 3.0)
        rms_dcm = _safe_sqrt(d_dcm * i_pk_d**2 / 3.0)
        return np.where(p_out >= boundary, rms_ccm, rms_dcm)

    @staticmethod
    def i1_mean(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = BuckBoost.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = BuckBoost.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = BuckBoost.v_switch(v_in, v_ch1)
        i_min  = BuckBoost.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        i_max  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_pk_d = v_sw * d_dcm / zeta
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        mean_ccm = d_ccm * (i_min + i_max) / 2.0
        mean_dcm = d_dcm * i_pk_d / 2.0
        return np.where(p_out >= boundary, mean_ccm, mean_dcm)

    @staticmethod
    def i2_rms(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = BuckBoost.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = BuckBoost.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = BuckBoost.v_switch(v_in, v_ch1)
        d_dcm2 = d_dcm * v_sw / np.maximum(v_out + v_ch2, 1e-9)
        i_min  = BuckBoost.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        i_max  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_pk_d = v_sw * d_dcm / zeta
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        rms_ccm = _safe_sqrt((1 - d_ccm) * (i_min**2 + i_min*i_max + i_max**2) / 3.0)
        rms_dcm = _safe_sqrt(d_dcm2 * i_pk_d**2 / 3.0)
        return np.where(p_out >= boundary, rms_ccm, rms_dcm)

    @staticmethod
    def i2_mean(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm  = BuckBoost.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        d_dcm  = BuckBoost.duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        v_sw   = BuckBoost.v_switch(v_in, v_ch1)
        d_dcm2 = d_dcm * v_sw / np.maximum(v_out + v_ch2, 1e-9)
        i_min  = BuckBoost.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        i_max  = p_out / v_out + v_sw * d_ccm / (2.0 * zeta)
        i_pk_d = v_sw * d_dcm / zeta
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)

        mean_ccm = (1 - d_ccm) * (i_min + i_max) / 2.0
        mean_dcm = d_dcm2 * i_pk_d / 2.0
        return np.where(p_out >= boundary, mean_ccm, mean_dcm)

    @staticmethod
    def i_on_t1(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        d_ccm    = BuckBoost.duty_ccm(v_in, v_out, v_ch1, v_ch2)
        v_sw     = BuckBoost.v_switch(v_in, v_ch1)
        i_min    = BuckBoost.i_min_ccm(zeta, v_in, v_out, p_out, v_ch1, v_ch2)
        boundary = _ccm_boundary(d_ccm, v_sw, zeta, v_out)
        return np.where(p_out >= boundary, np.maximum(i_min, 0.0), 0.0)

    @staticmethod
    def i_off_t1(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        return BuckBoost.i_peak(zeta, v_in, v_out, p_out, v_ch1, v_ch2)

    @staticmethod
    def i_rr_t2(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
        return BuckBoost.i_on_t1(zeta, v_in, v_out, p_out, v_ch1, v_ch2)