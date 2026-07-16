"""
converters/analysis.py
----------------------
Direct port of transistordatabase/gui/{boost,buck,buck_boost}_converter_functions.py
adapted to read from ConverterDevice (JSON) instead of MongoDB-backed Transistor objects.

Exposes:
  - ConverterParams          : all operating scalars + min/max ranges for axes
  - LossMapResult            : result of a Contour or Line calculation
  - compute(params, t1, t2)  : run one panel (Contour or Line) → LossMapResult

Axis variables  (x_axis / y_axis for Contour; x_axis for Line):
    "Vin [V]"            "Vout [V]"          "Output Power [W]"
    "Frequency [kHz]"    "Zeta = f*L"

Z-axis metrics (Contour) / Y-axis metrics (Line) – identical list:
    RMS Current Transistor1 [A]          RMS Current Diode Transistor2 [A]
    Mean Current Transistor1 [A]         Mean Current Diode Transistor2 [A]
    RMS Inductor Current [A]             Mean Inductor Current [A]
    Peak Current [A]
    Conduction Losses Transistor1 [W]    Conduction Losses Diode Transistor2 [W]
    Total Conduction Losses [W]
    Turn-on Switching Losses Transistor1 [W]
    Turn-off Switching Losses Transistor1 [W]
    Reverse Recovery Losses Diode Transistor2 [W]
    Total Switching Losses Transistor1 [W]
    Total Power Losses Transistor1 [W]
    Total Switching Losses [W]
    Temperature Switch Transistor1 [°C]
    Temperature Diode Transistor2 [°C]
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional

from .core import ConverterDevice

# ---------------------------------------------------------------------------
# Constants – match reference GUI exactly
# ---------------------------------------------------------------------------

AXIS_VARS = ["Vin [V]", "Vout [V]", "Output Power [W]", "Frequency [kHz]", "Zeta = f*L"]

METRICS = [
    "RMS Current Transistor1 [A]",
    "RMS Current Diode Transistor2 [A]",
    "Mean Current Transistor1 [A]",
    "Mean Current Diode Transistor2 [A]",
    "RMS Inductor Current [A]",
    "Mean Inductor Current [A]",
    "Peak Current [A]",
    "Conduction Losses Transistor1 [W]",
    "Conduction Losses Diode Transistor2 [W]",
    "Total Conduction Losses [W]",
    "Turn-on Switching Losses Transistor1 [W]",
    "Turn-off Switching Losses Transistor1 [W]",
    "Reverse Recovery Losses Diode Transistor2 [W]",
    "Total Switching Losses Transistor1 [W]",
    "Total Power Losses Transistor1 [W]",
    "Total Switching Losses [W]",
    "Temperature Switch Transistor1 [°C]",
    "Temperature Diode Transistor2 [°C]",
]

TOPOLOGIES = ["boost", "buck", "buck_boost"]

# ---------------------------------------------------------------------------
# Parameter container  (matches every field in the reference GUI)
# ---------------------------------------------------------------------------

@dataclass
class ConverterParams:
    # ---- topology ----
    topology:       str   = "buck_boost"   # "boost" | "buck" | "buck_boost"

    # ---- scalars (left panel) ----
    p_out:          float = 10000.0   # Output Power [W]
    v_in:           float = 700.0     # Vin [V]
    v_out:          float = 300.0     # Vout [V]
    frequency:      float = 10.0      # Frequency [kHz]  ← kHz, same as reference
    zeta:           float = 5.0       # Zeta = f*L
    t_heatsink:     float = 25.0      # Temperature Heatsink [°C]
    r_th_heatsink:  float = 1.0       # Thermal Resistance Heatsink [K/W]

    # ---- gate drive ----
    v_g_on:         float = 15.0      # Turn-on Gate Voltage [V]
    r_g_on:         float = 0.0       # Turn-on Gate Resistor [Ω]  (0 = datasheet nominal)
    r_g_off:        float = 0.0       # Turn-off Gate Resistor [Ω]

    # ---- axis ranges (right panel) ----
    p_out_min:      float = 1000.0
    p_out_max:      float = 10000.0
    v_in_min:       float = 300.0
    v_in_max:       float = 700.0
    v_out_min:      float = 100.0
    v_out_max:      float = 300.0
    frequency_min:  float = 1.0       # kHz
    frequency_max:  float = 10.0      # kHz
    zeta_min:       float = 1.0
    zeta_max:       float = 5.0

    # ---- plot selectors ----
    mode:           str   = "Contour"              # "Contour" | "Line"
    x_axis:         str   = "Vin [V]"
    y_axis:         str   = "Output Power [W]"     # in Line mode: the metric
    z_axis:         str   = "Total Switching Losses [W]"   # Contour metric
    n_points:       int   = 100                    # grid resolution (reference uses 100)


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class LossMapResult:
    mode:       str          # "Contour" | "Line"
    topology:   str
    t1_name:    str
    t2_name:    str
    x_label:    str
    y_label:    str
    x_data:     np.ndarray   # 1-D for Line, 1-D (vec_x_axis) for Contour
    y_data:     np.ndarray   # 1-D for Line, 1-D (vec_y_axis) for Contour
    z_data:     np.ndarray   # 1-D for Line (= y values), 2-D for Contour
    warnings:   list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Topology duty-cycle / current formulas
# ---------------------------------------------------------------------------

def _topo_formulas(topology: str) -> dict:
    topo = topology.lower().replace("-", "_").replace(" ", "_")
    if topo == "boost":
        def duty_ccm(v_in, v_out, v_ch1, v_ch2):
            return (-v_in + v_out + v_ch2) / (v_out - v_ch1 + v_ch2)
        def vsw(v_in, v_out, v_ch1): return v_in - v_ch1
        def duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
            den = v_out*(v_in-v_ch1)*(1+(v_in-v_ch1)/(-v_in+v_out+v_ch2))
            return np.sqrt(np.maximum(2*zeta*p_out/np.maximum(den,1e-12), 0.0))
        def duty_dcm2(d1, v_in, v_ch1, v_out, v_ch2):
            return d1*(v_in-v_ch1)/(-v_in+v_out+v_ch2)
        def boundary(v_out, d_ccm, v_in, v_ch1, zeta):
            return v_out*d_ccm*(v_in-v_ch1)/(2*zeta)
        e_scale = lambda v_in, v_out: v_out

    elif topo == "buck":
        def duty_ccm(v_in, v_out, v_ch1, v_ch2):
            return (v_ch2+v_out)/(v_in-v_ch1+v_ch2)
        def vsw(v_in, v_out, v_ch1): return v_in-v_out-v_ch1
        def duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
            s = v_in-v_out-v_ch1
            den = v_out*s*(1+s/np.maximum(v_out+v_ch2,1e-9))
            return np.sqrt(np.maximum(2*zeta*p_out/np.maximum(den,1e-12), 0.0))
        def duty_dcm2(d1, v_in, v_ch1, v_out, v_ch2):
            return d1*(v_in-v_out-v_ch1)/np.maximum(v_out+v_ch2,1e-9)
        def boundary(v_out, d_ccm, v_in, v_ch1, zeta):
            return v_out*d_ccm*(v_in-v_out-v_ch1)/(2*zeta)
        e_scale = lambda v_in, v_out: v_in

    elif topo == "buck_boost":
        def duty_ccm(v_in, v_out, v_ch1, v_ch2):
            return (v_out+v_ch2)/(v_in+v_out-v_ch1+v_ch2)
        def vsw(v_in, v_out, v_ch1): return v_in-v_ch1
        def duty_dcm(zeta, v_in, v_out, p_out, v_ch1, v_ch2):
            s = v_in-v_ch1
            den = v_out*s*(1+s/np.maximum(v_out+v_ch2,1e-9))
            return np.sqrt(np.maximum(2*zeta*p_out/np.maximum(den,1e-12), 0.0))
        def duty_dcm2(d1, v_in, v_ch1, v_out, v_ch2):
            return d1*(v_in-v_ch1)/np.maximum(v_out+v_ch2,1e-9)
        def boundary(v_out, d_ccm, v_in, v_ch1, zeta):
            return v_out*d_ccm*(v_in-v_ch1)/(2*zeta)
        e_scale = lambda v_in, v_out: v_in+v_out

    else:
        raise ValueError(f"Unknown topology '{topology}'")

    return dict(duty_ccm=duty_ccm, vsw=vsw, duty_dcm=duty_dcm,
                duty_dcm2=duty_dcm2, boundary=boundary, e_scale=e_scale)


# ---------------------------------------------------------------------------
# Channel linearisation – direct port of f_m_calc_channel
# ---------------------------------------------------------------------------

def _calc_channel(m_i, v_g_on1, t1, t2):
    vec = np.linspace(1, 1000, 1000)
    vc1s = np.zeros(1000); rc1s = np.zeros(1000)
    vc2d = np.zeros(1000); rc2d = np.zeros(1000)
    vc1  = np.zeros(1000); vc2  = np.zeros(1000)

    tj_sw = t1.max_t_j_switch(); tj_di = t2.max_t_j_diode()

    for i in range(1000):
        ic = vec[i]
        if ic <= t1.i_abs_max:
            v0, r0 = t1.calc_lin_channel(ic, tj_sw, v_g_on1, "switch")
            vc1s[i], rc1s[i] = v0, r0
        else:
            vc1s[i], rc1s[i] = vc1s[i-1], rc1s[i-1]
        if ic <= t2.i_abs_max:
            v0, r0 = t2.calc_lin_channel(ic, tj_di, 0.0, "diode")
            vc2d[i], rc2d[i] = v0, r0
        else:
            vc2d[i], rc2d[i] = vc2d[i-1], rc2d[i-1]
        vc1[i] = rc1s[i]*ic + vc1s[i]
        vc2[i] = vc2d[i]

    ok = ~np.isnan(m_i)
    def interp(src): return np.where(ok, np.interp(np.where(ok, m_i, 0), vec, src), 0.0)
    return (interp(vc1), interp(vc2), interp(rc1s), interp(vc1s), interp(vc2d), interp(rc2d))


# ---------------------------------------------------------------------------
# i_peak with 2-iteration channel correction  (f_m_i_peak)
# ---------------------------------------------------------------------------

def _i_peak(F, zeta, v_in, v_out, p_out, v_g_on1, t1, t2):
    vc1 = np.zeros_like(zeta); vc2 = np.zeros_like(zeta)
    for _ in range(2):
        d_ccm = F["duty_ccm"](v_in, v_out, vc1, vc2)
        d_dcm = F["duty_dcm"](zeta, v_in, v_out, p_out, vc1, vc2)
        sw    = F["vsw"](v_in, v_out, vc1)
        bnd   = F["boundary"](v_out, d_ccm, v_in, vc1, zeta)
        i_max = p_out/v_out + sw*d_ccm/(2*zeta)
        i_dcm = sw*d_dcm/zeta
        ip    = np.where(p_out >= bnd, i_max, i_dcm)
        ch    = _calc_channel(ip, v_g_on1, t1, t2)
        vc1, vc2 = ch[0], ch[1]
    return ip, vc1, vc2


# ---------------------------------------------------------------------------
# Energy helpers
# ---------------------------------------------------------------------------

def _max_v_supply(device, which):
    tbl = {"e_on": device._e_on, "e_off": device._e_off, "e_rr": device._e_rr}
    entries = tbl.get(which, [])
    vals = [e["v_supply"] for e in entries if e.get("v_supply")]
    return max(vals) if vals else 1.0


def _interp_energy(device, which, i_map, t_j, r_g=0.0, v_supply_target=None):
    tbl = {"e_on": device._e_on, "e_off": device._e_off, "e_rr": device._e_rr}
    entries = tbl.get(which, [])
    if not entries:
        return np.zeros_like(i_map)
    rescaled = device.rescale_energy_for_rg(which, r_g, t_j, v_supply_target) if r_g > 0 else None
    if rescaled:
        i_pts, e_pts = rescaled["i_pts"], rescaled["e_pts"]
    else:
        v_t = v_supply_target or _max_v_supply(device, which)
        cands = [e for e in entries if e.get("v_supply") == v_t] or entries
        entry = min(cands, key=lambda e: abs(e["t_j"] - t_j))
        i_pts, e_pts = entry["i_pts"], entry["e_pts"]
    fi = np.clip(i_map.ravel(), i_pts[0], i_pts[-1])
    return np.maximum(np.interp(fi, i_pts, e_pts).reshape(i_map.shape), 0.0)


# ---------------------------------------------------------------------------
# All metric computations  (operate on arbitrary-shaped numpy arrays)
# ---------------------------------------------------------------------------

def _compute_all(F, zeta, v_in, v_out, p_out, freq_hz,
                 v_g_on1, r_g_on, r_g_off,
                 t_heatsink, r_th_heatsink,
                 t1: ConverterDevice, t2: ConverterDevice) -> dict:
    """
    Compute all 18 metrics for given arrays.
    All inputs must be broadcastable numpy arrays.
    Returns dict mapping metric name → numpy array.
    """
    # -- i_peak + converged channel voltages --
    ip, vc1, vc2 = _i_peak(F, zeta, v_in, v_out, p_out, v_g_on1, t1, t2)
    ch = _calc_channel(ip, v_g_on1, t1, t2)
    rc1s = ch[2]; vc1s_lin = ch[3]; vc2d = ch[4]

    d_ccm  = F["duty_ccm"](v_in, v_out, vc1, vc2)
    d_dcm1 = F["duty_dcm"](zeta, v_in, v_out, p_out, vc1, vc2)
    d_dcm2 = F["duty_dcm2"](d_dcm1, v_in, vc1, v_out, vc2)
    sw     = F["vsw"](v_in, v_out, vc1)
    bnd    = F["boundary"](v_out, d_ccm, v_in, vc1, zeta)
    is_ccm = p_out >= bnd

    i_min  = p_out/v_out - sw*d_ccm/(2*zeta)
    i_max  = p_out/v_out + sw*d_ccm/(2*zeta)
    i_pk_d = sw*d_dcm1/zeta

    def safe_sqrt(x): return np.sqrt(np.maximum(x, 0.0))

    # RMS / Mean currents  (direct ports of f_m_i1_rms, f_m_i2_rms, etc.)
    i1_rms = np.where(is_ccm,
        safe_sqrt(d_ccm*(i_min**2+i_max*i_min+i_max**2)/3),
        safe_sqrt(d_dcm1*i_pk_d**2/3))
    i1_mean = np.where(is_ccm,
        d_ccm*(i_min+i_max)/2,
        d_dcm1*i_pk_d/2)
    i2_rms = np.where(is_ccm,
        safe_sqrt((1-d_ccm)*(i_min**2+i_max*i_min+i_max**2)/3),
        safe_sqrt(d_dcm2*i_pk_d**2/3))
    i2_mean = np.where(is_ccm,
        (1-d_ccm)*(i_min+i_max)/2,
        d_dcm2*i_pk_d/2)

    # Inductor RMS  (f_m_i_l_rms)
    il_rms_ccm = safe_sqrt(
        (d_ccm*(i_min**2+i_max*i_min+i_max**2)/3) +
        (-(d_ccm-1)*(i_min**2+i_max*i_min+i_max**2)/3))
    il_rms_dcm = safe_sqrt(d_dcm1*i_pk_d**2/3 + d_dcm2*i_pk_d**2/3)
    il_rms = np.where(is_ccm, il_rms_ccm, il_rms_dcm)

    # Inductor Mean  (f_m_i_l_mean) = p_out/v_out
    il_mean = p_out / v_out

    # Conduction losses
    cond1 = i1_rms**2 * rc1s + i1_mean * vc1s_lin
    cond2 = i2_rms * vc2d

    # Switching currents
    i_on1  = np.where(is_ccm, np.maximum(i_min, 0.0), 0.0)   # turn-on = i_min_ccm / 0 in DCM
    i_off1 = ip                                                # turn-off = i_peak always
    i_rr2  = i_on1                                             # reverse recovery = same as turn-on

    # Switching energy scale voltage (topology-specific)
    ev = F["e_scale"](v_in, v_out)

    # Turn-on losses T1
    if t1.has_e_on:
        tj_on  = t1.max_t_j_e_on()
        vs_on  = _max_v_supply(t1, "e_on")
        E_on   = _interp_energy(t1, "e_on",  i_on1,  tj_on,  r_g=r_g_on,  v_supply_target=vs_on)
        p_on1  = E_on  * freq_hz * ev / max(vs_on,  1e-9)
    else:
        p_on1  = np.zeros_like(ip)

    # Turn-off losses T1
    if t1.has_e_off:
        tj_off = t1.max_t_j_e_off()
        vs_off = _max_v_supply(t1, "e_off")
        E_off  = _interp_energy(t1, "e_off", i_off1, tj_off, r_g=r_g_off, v_supply_target=vs_off)
        p_off1 = E_off * freq_hz * ev / max(vs_off, 1e-9)
    else:
        p_off1 = np.zeros_like(ip)

    # Reverse recovery losses T2
    if t2.has_e_rr:
        tj_rr  = t2.max_t_j_e_rr()
        vs_rr  = _max_v_supply(t2, "e_rr")
        E_rr   = _interp_energy(t2, "e_rr",  i_rr2,  tj_rr,  r_g=0.0,    v_supply_target=vs_rr)
        p_rr2  = E_rr  * freq_hz * ev / max(vs_rr,  1e-9)
    else:
        p_rr2  = np.zeros_like(ip)

    sw_t1  = p_on1 + p_off1
    sw_all = sw_t1 + p_rr2
    p1     = cond1 + sw_t1
    p2     = cond2 + p_rr2
    p_tot  = p1 + p2

    # Junction temperatures
    rth1 = t1.r_th_switch_jc + t1.r_th_switch_cs + t1.r_th_cs + r_th_heatsink
    t_j1 = t_heatsink + p1 * rth1
    if t2.has_diode_tf:
        rth2 = t2.r_th_diode_jc + t2.r_th_diode_cs + t2.r_th_cs + r_th_heatsink
        t_j2 = t_heatsink + p2 * rth2
    else:
        t_j2 = np.full_like(ip, np.nan)

    return {
        "RMS Current Transistor1 [A]":                 i1_rms,
        "RMS Current Diode Transistor2 [A]":           i2_rms,
        "Mean Current Transistor1 [A]":                i1_mean,
        "Mean Current Diode Transistor2 [A]":          i2_mean,
        "RMS Inductor Current [A]":                    il_rms,
        "Mean Inductor Current [A]":                   il_mean,
        "Peak Current [A]":                            ip,
        "Conduction Losses Transistor1 [W]":           cond1,
        "Conduction Losses Diode Transistor2 [W]":     cond2,
        "Total Conduction Losses [W]":                 cond1 + cond2,
        "Turn-on Switching Losses Transistor1 [W]":    p_on1,
        "Turn-off Switching Losses Transistor1 [W]":   p_off1,
        "Reverse Recovery Losses Diode Transistor2 [W]": p_rr2,
        "Total Switching Losses Transistor1 [W]":      sw_t1,
        "Total Power Losses Transistor1 [W]":          p1,
        "Total Switching Losses [W]":                  sw_all,
        "Temperature Switch Transistor1 [°C]":         t_j1,
        "Temperature Diode Transistor2 [°C]":          t_j2,
    }


# ---------------------------------------------------------------------------
# Variable vector builder  (matches lineEdit_topology_* ranges in reference)
# ---------------------------------------------------------------------------

def _make_vec(var: str, params: ConverterParams, n: int) -> np.ndarray:
    ranges = {
        "Vin [V]":           (params.v_in_min,       params.v_in_max),
        "Vout [V]":          (params.v_out_min,       params.v_out_max),
        "Output Power [W]":  (params.p_out_min,       params.p_out_max),
        "Frequency [kHz]":   (params.frequency_min,   params.frequency_max),
        "Zeta = f*L":        (params.zeta_min,        params.zeta_max),
    }
    lo, hi = ranges[var]
    return np.linspace(lo, hi, n)


def _scalar_arrays(params: ConverterParams, shape) -> dict:
    """Build constant arrays for all 5 variables from the scalar panel fields."""
    return {
        "Vin [V]":          np.full(shape, params.v_in),
        "Vout [V]":         np.full(shape, params.v_out),
        "Output Power [W]": np.full(shape, params.p_out),
        "Frequency [kHz]":  np.full(shape, params.frequency),
        "Zeta = f*L":       np.full(shape, params.zeta),
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def compute(params: ConverterParams,
            t1: ConverterDevice,
            t2: ConverterDevice) -> LossMapResult:
    """
    Run one panel computation (Contour or Line) exactly as in the reference GUI.

    Contour: X and Y axes are swept; all other variables are scalar constants.
    Line:    X axis is swept; all other variables are scalar constants.
             The metric to plot is given by params.y_axis (same list as z_axis).
    """
    F = _topo_formulas(params.topology)
    warnings_list = []

    if not t1.has_e_on or not t1.has_e_off:
        warnings_list.append(f"T1 ({t1.name}): no e_on/e_off – switching losses T1 = 0.")
    if not t2.has_e_rr:
        warnings_list.append(f"T2 ({t2.name}): no e_rr – reverse-recovery losses = 0.")
    if not t2.has_diode_tf:
        warnings_list.append(f"T2 ({t2.name}): no diode thermal – T_j T2 = NaN.")

    freq_hz = params.frequency * 1e3  # reference uses kHz in GUI, Hz in formulas

    if params.mode == "Contour":
        vec_x = _make_vec(params.x_axis, params, params.n_points)
        vec_y = _make_vec(params.y_axis, params, params.n_points)
        m_x, m_y = np.meshgrid(vec_x, vec_y)

        # Build constant arrays then override the two axis variables
        arrs = _scalar_arrays(params, m_x.shape)
        arrs[params.x_axis] = m_x
        arrs[params.y_axis] = m_y

        freq_arr = arrs["Frequency [kHz]"] * 1e3  # convert kHz→Hz for the math

        results = _compute_all(
            F,
            zeta     = arrs["Zeta = f*L"],
            v_in     = arrs["Vin [V]"],
            v_out    = arrs["Vout [V]"],
            p_out    = arrs["Output Power [W]"],
            freq_hz  = freq_arr,
            v_g_on1  = params.v_g_on,
            r_g_on   = params.r_g_on,
            r_g_off  = params.r_g_off,
            t_heatsink    = params.t_heatsink,
            r_th_heatsink = params.r_th_heatsink,
            t1=t1, t2=t2,
        )
        z = results[params.z_axis]
        return LossMapResult(
            mode="Contour", topology=params.topology,
            t1_name=t1.name, t2_name=t2.name,
            x_label=params.x_axis, y_label=params.y_axis,
            x_data=vec_x, y_data=vec_y, z_data=z,
            warnings=warnings_list,
        )

    else:  # Line
        vec_x = _make_vec(params.x_axis, params, params.n_points)
        arrs  = _scalar_arrays(params, vec_x.shape)
        arrs[params.x_axis] = vec_x

        freq_arr = arrs["Frequency [kHz]"] * 1e3

        results = _compute_all(
            F,
            zeta     = arrs["Zeta = f*L"],
            v_in     = arrs["Vin [V]"],
            v_out    = arrs["Vout [V]"],
            p_out    = arrs["Output Power [W]"],
            freq_hz  = freq_arr,
            v_g_on1  = params.v_g_on,
            r_g_on   = params.r_g_on,
            r_g_off  = params.r_g_off,
            t_heatsink    = params.t_heatsink,
            r_th_heatsink = params.r_th_heatsink,
            t1=t1, t2=t2,
        )
        vec_y = results[params.y_axis]
        return LossMapResult(
            mode="Line", topology=params.topology,
            t1_name=t1.name, t2_name=t2.name,
            x_label=params.x_axis, y_label=params.y_axis,
            x_data=vec_x, y_data=vec_y, z_data=vec_y,
            warnings=warnings_list,
        )


# ---------------------------------------------------------------------------
# Legacy compatibility shim  (keeps CLI working without changes)
# ---------------------------------------------------------------------------

@dataclass
class _LegacyResult:
    """Wraps compute() output to look like the old LossMapResult."""
    topology: str; t1_name: str; t2_name: str
    v_in_vec: np.ndarray; p_out_vec: np.ndarray
    P_cond_T1: np.ndarray; P_cond_T2: np.ndarray
    P_sw_T1: np.ndarray; P_rr_T2: np.ndarray; P_total: np.ndarray
    T_j_T1: np.ndarray; T_j_T2: np.ndarray
    duty: np.ndarray; i_peak: np.ndarray
    warnings: list = field(default_factory=list)


def run_loss_map(topology, t1, t2, params_legacy) -> _LegacyResult:
    """
    Backward-compatible wrapper used by the CLI (_run_converter_cli).
    params_legacy has: v_in_range, p_out_range, v_out, frequency (Hz!),
                       zeta, v_g_on, r_g_on, r_g_off, t_heatsink,
                       r_th_heatsink, n_points.
    """
    # Build new-style params in Contour mode with Vin × Pout axes
    p = ConverterParams(
        topology       = topology,
        p_out          = (params_legacy.p_out_range[0] + params_legacy.p_out_range[1]) / 2,
        v_in           = (params_legacy.v_in_range[0]  + params_legacy.v_in_range[1])  / 2,
        v_out          = params_legacy.v_out,
        frequency      = params_legacy.frequency / 1e3,   # Hz → kHz
        zeta           = params_legacy.zeta,
        t_heatsink     = params_legacy.t_heatsink,
        r_th_heatsink  = params_legacy.r_th_heatsink,
        v_g_on         = params_legacy.v_g_on,
        r_g_on         = params_legacy.r_g_on,
        r_g_off        = params_legacy.r_g_off,
        v_in_min       = params_legacy.v_in_range[0],
        v_in_max       = params_legacy.v_in_range[1],
        p_out_min      = params_legacy.p_out_range[0],
        p_out_max      = params_legacy.p_out_range[1],
        v_out_min      = params_legacy.v_out,
        v_out_max      = params_legacy.v_out,
        mode           = "Contour",
        x_axis         = "Vin [V]",
        y_axis         = "Output Power [W]",
        z_axis         = "Total Power Losses Transistor1 [W]",
        n_points       = params_legacy.n_points,
    )

    # Run all metrics by calling _compute_all once
    F = _topo_formulas(topology)
    freq_hz = p.frequency * 1e3
    vec_v = np.linspace(p.v_in_min, p.v_in_max, p.n_points)
    vec_p = np.linspace(p.p_out_min, p.p_out_max, p.n_points)
    V_IN, P_OUT = np.meshgrid(vec_v, vec_p)

    res = _compute_all(
        F,
        zeta=np.full_like(V_IN, p.zeta),
        v_in=V_IN, v_out=np.full_like(V_IN, p.v_out),
        p_out=P_OUT, freq_hz=freq_hz,
        v_g_on1=p.v_g_on, r_g_on=p.r_g_on, r_g_off=p.r_g_off,
        t_heatsink=p.t_heatsink, r_th_heatsink=p.r_th_heatsink,
        t1=t1, t2=t2,
    )

    warns = []
    if not t1.has_e_on or not t1.has_e_off:
        warns.append(f"T1 ({t1.name}): no e_on/e_off – switching losses T1 = 0.")
    if not t2.has_e_rr:
        warns.append(f"T2 ({t2.name}): no e_rr – reverse-recovery = 0.")
    if not t2.has_diode_tf:
        warns.append(f"T2 ({t2.name}): no diode thermal – T_j T2 = NaN.")

    # topology validity mask
    topo = topology.lower().replace("-","_").replace(" ","_")
    if topo == "boost":
        mask = V_IN >= np.full_like(V_IN, p.v_out)
    elif topo == "buck":
        mask = V_IN <= np.full_like(V_IN, p.v_out)
    else:
        mask = np.zeros_like(V_IN, dtype=bool)
    for arr in res.values():
        if isinstance(arr, np.ndarray): arr[mask] = np.nan

    return _LegacyResult(
        topology=topology, t1_name=t1.name, t2_name=t2.name,
        v_in_vec=vec_v, p_out_vec=vec_p,
        P_cond_T1 = res["Conduction Losses Transistor1 [W]"],
        P_cond_T2 = res["Conduction Losses Diode Transistor2 [W]"],
        P_sw_T1   = res["Total Switching Losses Transistor1 [W]"],
        P_rr_T2   = res["Reverse Recovery Losses Diode Transistor2 [W]"],
        P_total   = res["Total Power Losses Transistor1 [W]"],
        T_j_T1    = res["Temperature Switch Transistor1 [°C]"],
        T_j_T2    = res["Temperature Diode Transistor2 [°C]"],
        duty      = np.full_like(V_IN, np.nan),
        i_peak    = res["Peak Current [A]"],
        warnings  = warns,
    )