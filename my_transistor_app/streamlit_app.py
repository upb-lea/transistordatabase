"""
Streamlit prototype for the Power Transistor Selector.

Run with:
    streamlit run streamlit_app.py

The app calls the selector library directly (no FastAPI intermediary needed),
so you can run it standalone without starting the API server.
"""
from __future__ import annotations

import math
import os
import sys
from typing import Optional

# ---------------------------------------------------------------------------
# Make the project root (one level up, where transistordatabase/ lives)
# importable, WITHOUT relying on the PYTHONPATH environment variable.
#
# Why: newer Streamlit versions run the app script inside a Uvicorn-managed
# worker process (multiprocessing "spawn" on Windows). That worker does not
# reliably inherit PYTHONPATH set by the launching process/shell, even
# though the launcher process itself sees it fine. Setting sys.path
# directly here executes inside the SAME process that actually runs this
# script, so it works regardless of how that process was spawned.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ---------------------------------------------------------------------------
# DIAGNOSTIC: write ground-truth facts about THIS exact process to a file,
# before attempting the imports that have been failing. This removes all
# guessing about which interpreter/site-packages this specific worker
# process actually uses - we read it directly from the process itself.
# Safe to remove once the underlying issue is confirmed and fixed.
# ---------------------------------------------------------------------------
try:
    import importlib.util as _ilu
    _diag_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runtime_diagnostics.log")
    with open(_diag_path, "w", encoding="utf-8") as _f:
        _f.write(f"sys.executable = {sys.executable}\n")
        _f.write(f"sys.version = {sys.version}\n")
        _f.write(f"os.getcwd() = {os.getcwd()}\n")
        _f.write(f"_PROJECT_ROOT = {_PROJECT_ROOT}\n")
        _f.write(f"PYTHONPATH env = {os.environ.get('PYTHONPATH', '<not set>')}\n")
        _f.write("sys.path =\n")
        for _p in sys.path:
            _f.write(f"    {_p}\n")
        _pymongo_spec = _ilu.find_spec("pymongo")
        _f.write(f"pymongo find_spec = {_pymongo_spec}\n")
        _f.write(f"transistordatabase find_spec = {_ilu.find_spec('transistordatabase')}\n")
except Exception as _diag_err:
    # If even the diagnostic write fails, don't block the app - just note it.
    print(f"[diagnostic write failed] {_diag_err}", file=sys.stderr)

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page config — must be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Power Transistor Selector",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Lazy-init the selector (cached for the session)
# ---------------------------------------------------------------------------
from selector.models import CircuitRequirements, Topology, TransistorType
from selector.selector import TransistorSelector


@st.cache_resource(show_spinner="Loading transistor database …")
def get_selector(db_path: Optional[str] = None) -> TransistorSelector:
    return TransistorSelector(db_path=db_path)


# ---------------------------------------------------------------------------
# Sidebar — user inputs
# ---------------------------------------------------------------------------
st.sidebar.title("⚡ Transistor Selector")
st.sidebar.caption("Power switch selection with loss estimation")

with st.sidebar.expander("🗄️ Database settings", expanded=False):
    db_path_input = st.text_input(
        "TDB JSON folder (blank = library default)",
        value=os.environ.get("TDB_PATH", ""),
        help="Path to a folder of .json transistor files from transistordatabase.",
    )
    db_path = db_path_input.strip() or None
    if st.button("Reload database"):
        st.cache_resource.clear()
        st.rerun()

# ------ Topology ------
st.sidebar.subheader("1 · Topology")
topology_map = {
    "Buck converter": Topology.BUCK,
    "Boost converter": Topology.BOOST,
    "Half-bridge / Inverter": Topology.HALF_BRIDGE,
}
topology_label = st.sidebar.selectbox("Topology", list(topology_map.keys()))
topology = topology_map[topology_label]

# ------ Electrical specs ------
st.sidebar.subheader("2 · Electrical specs")
v_bus = st.sidebar.number_input(
    "V_bus — DC bus voltage [V]",
    min_value=10.0, max_value=10000.0, value=400.0, step=10.0,
    help="For Boost: the output (high) side. For Buck/Half-bridge: the input.",
)
i_load = st.sidebar.number_input(
    "I_load [A]  (DC avg or peak sinusoidal)",
    min_value=0.1, max_value=5000.0, value=20.0, step=1.0,
)
f_sw_khz = st.sidebar.number_input(
    "f_sw — switching frequency [kHz]",
    min_value=0.1, max_value=3000.0, value=50.0, step=1.0,
)
f_sw = f_sw_khz * 1e3

v_out: Optional[float] = None
if topology in (Topology.BUCK, Topology.BOOST):
    label = (
        "V_out — output voltage [V]" if topology == Topology.BUCK
        else "V_in — input (low) voltage [V]"
    )
    v_out = st.sidebar.number_input(
        label,
        min_value=1.0, max_value=v_bus - 1.0, value=min(200.0, v_bus * 0.5),
        step=5.0,
    )

# ------ Operating point ------
st.sidebar.subheader("3 · Operating point")
t_j_op = st.sidebar.slider(
    "T_j operating [°C]",
    min_value=25, max_value=175, value=125, step=5,
    help="Junction temperature for data lookup. Not the same as T_j_max.",
)
v_g = st.sidebar.number_input(
    "V_gate on [V]",
    min_value=5.0, max_value=25.0, value=15.0, step=0.5,
    help="Gate drive voltage. Use 15 V for Si/SiC MOSFET, ~18 V for IGBT.",
)

# ------ Safety / filters ------
st.sidebar.subheader("4 · Derating & filters")
v_margin = st.sidebar.slider(
    "Voltage margin (V_abs_max / V_bus)",
    min_value=1.1, max_value=5.0, value=1.5, step=0.1,
    help="Minimum ratio. 1.5× is typical engineering practice.",
)
i_margin = st.sidebar.slider(
    "Current margin (I_abs_max / I_peak)",
    min_value=1.1, max_value=5.0, value=1.5, step=0.1,
)
type_options = {
    "All types": None,
    "SiC-MOSFET only": [TransistorType.SIC_MOSFET],
    "Si MOSFET only": [TransistorType.MOSFET],
    "IGBT only": [TransistorType.IGBT],
    "GaN only": [TransistorType.GAN],
    "SiC-MOSFET + IGBT": [TransistorType.SIC_MOSFET, TransistorType.IGBT],
}
type_label = st.sidebar.selectbox("Transistor types", list(type_options.keys()))
allowed_types = type_options[type_label]

max_results = st.sidebar.slider("Max results", 5, 50, 20)

run_btn = st.sidebar.button("🔍 Find transistors", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------
st.title("⚡ Power Transistor Selector")

# Waveform preview card
with st.expander("📐 Computed waveform parameters", expanded=False):
    from selector.loss_engine import compute_waveform
    from selector.models import CircuitRequirements as CR

    try:
        _req_prev = CR(
            topology=topology,
            v_bus=v_bus,
            i_load=i_load,
            f_sw=f_sw,
            v_out=v_out,
            t_j_op=t_j_op,
            v_g=v_g,
            v_margin=v_margin,
            i_margin=i_margin,
            allowed_types=allowed_types,
            max_results=max_results,
        )
        wf = compute_waveform(_req_prev)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Duty cycle D", f"{wf.duty_cycle:.3f}")
        c2.metric("I_sw_rms", f"{wf.i_sw_rms:.2f} A")
        c3.metric("I_diode_rms", f"{wf.i_diode_rms:.2f} A")
        c4.metric("I_peak (sw)", f"{wf.i_peak:.2f} A")
        c5.metric("Min V_abs_max", f"{v_bus * v_margin:.0f} V")
    except Exception as e:
        st.warning(f"Waveform preview error: {e}")

# ---------------------------------------------------------------------------
# Run selection
# ---------------------------------------------------------------------------
if run_btn:
    try:
        sel = get_selector(db_path)
    except FileNotFoundError as e:
        st.error(f"Database path error: {e}")
        st.stop()

    try:
        req = CircuitRequirements(
            topology=topology,
            v_bus=v_bus,
            i_load=i_load,
            f_sw=f_sw,
            v_out=v_out,
            t_j_op=t_j_op,
            v_g=v_g,
            v_margin=v_margin,
            i_margin=i_margin,
            allowed_types=allowed_types,
            max_results=max_results,
        )
    except Exception as e:
        st.error(f"Input validation error: {e}")
        st.stop()

    with st.spinner("Scanning database and estimating losses …"):
        resp = sel.select(req)

    # Warnings
    for w in resp.warnings:
        st.warning(w)

    # Stats
    st.info(
        f"**{resp.total_candidates}** candidates passed filters out of "
        f"**{resp.total_in_db}** transistors in the database."
    )

    if not resp.results:
        st.error("No transistors found. Try relaxing the derating margins or expanding the type filter.")
        st.stop()

    # ----------------------------------------------------------------
    # Results table
    # ----------------------------------------------------------------
    st.subheader("🏆 Ranked results")

    rows = []
    for r in resp.results:
        rows.append({
            "Rank": r.rank,
            "Name": r.name,
            "Type": r.transistor_type,
            "Housing": r.housing_type,
            "V_max [V]": r.v_abs_max,
            "I_max [A]": r.i_abs_max,
            "V margin": f"{r.v_derating:.1f}×",
            "I margin": f"{r.i_derating:.1f}×",
            "P_cond_sw [W]": r.losses.p_sw_cond_w,
            "P_on [W]": r.losses.p_sw_on_w,
            "P_off [W]": r.losses.p_sw_off_w,
            "P_cond_D [W]": r.losses.p_diode_cond_w,
            "P_rr [W]": r.losses.p_diode_rr_w,
            "P_total [W]": r.losses.p_total_w,
            "Confidence": f"{r.data_confidence_pct:.0f}%",
        })

    df = pd.DataFrame(rows).set_index("Rank")

    def _color_confidence(val: str) -> str:
        try:
            pct = float(val.rstrip("%"))
        except ValueError:
            return ""
        if pct >= 80:
            return "background-color: #d4edda"
        if pct >= 50:
            return "background-color: #fff3cd"
        return "background-color: #f8d7da"

    styled = df.style.format(
        {
            "P_cond_sw [W]": lambda x: f"{x:.3f}" if x is not None else "—",
            "P_on [W]": lambda x: f"{x:.3f}" if x is not None else "—",
            "P_off [W]": lambda x: f"{x:.3f}" if x is not None else "—",
            "P_cond_D [W]": lambda x: f"{x:.3f}" if x is not None else "—",
            "P_rr [W]": lambda x: f"{x:.3f}" if x is not None else "—",
            "P_total [W]": lambda x: f"{x:.3f}",
        }
    ).map(_color_confidence, subset=["Confidence"])  # type: ignore

    st.dataframe(styled, use_container_width=True, height=400)

    # ----------------------------------------------------------------
    # Loss comparison bar chart (top-N)
    # ----------------------------------------------------------------
    st.subheader("📊 Loss breakdown — top candidates")

    top = resp.results[:min(12, len(resp.results))]
    names = [r.name for r in top]
    components = {
        "P_sw_cond": [r.losses.p_sw_cond_w or 0 for r in top],
        "P_on": [r.losses.p_sw_on_w or 0 for r in top],
        "P_off": [r.losses.p_sw_off_w or 0 for r in top],
        "P_diode_cond": [r.losses.p_diode_cond_w or 0 for r in top],
        "P_rr": [r.losses.p_diode_rr_w or 0 for r in top],
    }
    colors = ["#2196F3", "#FF9800", "#F44336", "#4CAF50", "#9C27B0"]
    fig = go.Figure()
    for (label, vals), color in zip(components.items(), colors):
        fig.add_trace(go.Bar(name=label, x=names, y=vals, marker_color=color))
    fig.update_layout(
        barmode="stack",
        xaxis_title="Transistor",
        yaxis_title="Power loss [W]",
        legend_title="Component",
        height=420,
        margin=dict(l=0, r=0, t=30, b=120),
        xaxis_tickangle=-40,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ----------------------------------------------------------------
    # Detailed transistor view
    # ----------------------------------------------------------------
    st.subheader("🔎 Transistor detail")
    detail_name = st.selectbox(
        "Select transistor for details",
        [r.name for r in resp.results],
    )
    detail = next((r for r in resp.results if r.name == detail_name), None)
    if detail:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Ratings**")
            st.table(
                pd.DataFrame(
                    {
                        "Parameter": [
                            "Type", "Manufacturer", "Housing",
                            "V_abs_max", "I_abs_max", "I_cont",
                            "T_j_max", "R_g_int", "R_th_cs",
                        ],
                        "Value": [
                            detail.transistor_type, detail.manufacturer, detail.housing_type,
                            f"{detail.v_abs_max:.0f} V",
                            f"{detail.i_abs_max:.0f} A",
                            f"{detail.i_cont:.0f} A" if detail.i_cont else "—",
                            f"{detail.t_j_max:.0f} °C",
                            f"{detail.r_g_int:.2f} Ω",
                            f"{detail.r_th_cs:.4f} K/W" if detail.r_th_cs else "—",
                        ],
                    }
                ).set_index("Parameter")
            )

        with col2:
            st.markdown("**Loss estimate**")
            loss_df = pd.DataFrame(
                {
                    "Component": [
                        "Switch conduction",
                        "Turn-on (E_on·f_sw)",
                        "Turn-off (E_off·f_sw)",
                        "Diode conduction",
                        "Diode reverse rec.",
                        "**Total**",
                    ],
                    "Power [W]": [
                        f"{detail.losses.p_sw_cond_w:.4f}" if detail.losses.p_sw_cond_w is not None else "—",
                        f"{detail.losses.p_sw_on_w:.4f}" if detail.losses.p_sw_on_w is not None else "—",
                        f"{detail.losses.p_sw_off_w:.4f}" if detail.losses.p_sw_off_w is not None else "—",
                        f"{detail.losses.p_diode_cond_w:.4f}" if detail.losses.p_diode_cond_w is not None else "—",
                        f"{detail.losses.p_diode_rr_w:.4f}" if detail.losses.p_diode_rr_w is not None else "—",
                        f"**{detail.losses.p_total_w:.4f}**",
                    ],
                }
            ).set_index("Component")
            st.table(loss_df)

        with col3:
            st.markdown("**Data provenance**")
            prov = {
                "Confidence": f"{detail.data_confidence_pct:.0f} %",
                "Ch. source": detail.losses.sw_channel_source or "—",
                "E_on source": detail.losses.e_on_source or "—",
                "E_off source": detail.losses.e_off_source or "—",
                "E_rr source": detail.losses.e_rr_source or "—",
                "E_on V-scale": f"{detail.losses.e_on_v_scale:.2f}×" if detail.losses.e_on_v_scale else "—",
                "E_off V-scale": f"{detail.losses.e_off_v_scale:.2f}×" if detail.losses.e_off_v_scale else "—",
            }
            st.table(pd.DataFrame.from_dict(prov, orient="index", columns=["Value"]))

        if detail.missing_data_notes:
            st.markdown("**⚠️ Data gaps**")
            for note in detail.missing_data_notes:
                st.caption(f"• {note}")

    # ----------------------------------------------------------------
    # Loss-confidence scatter plot
    # ----------------------------------------------------------------
    st.subheader("📈 Loss vs. data confidence")
    scatter_data = pd.DataFrame(
        {
            "Name": [r.name for r in resp.results],
            "P_total_W": [r.losses.p_total_w for r in resp.results],
            "Confidence_%": [r.data_confidence_pct for r in resp.results],
            "Type": [r.transistor_type for r in resp.results],
            "V_max": [r.v_abs_max for r in resp.results],
        }
    )
    type_colors = {
        "SiC-MOSFET": "#2196F3",
        "MOSFET": "#4CAF50",
        "IGBT": "#FF9800",
        "GaN-Transistor": "#9C27B0",
    }
    fig2 = go.Figure()
    for t_type, color in type_colors.items():
        mask = scatter_data["Type"] == t_type
        subset = scatter_data[mask]
        if subset.empty:
            continue
        fig2.add_trace(
            go.Scatter(
                x=subset["Confidence_%"],
                y=subset["P_total_W"],
                mode="markers+text",
                name=t_type,
                marker=dict(color=color, size=10, opacity=0.8),
                text=subset["Name"],
                textposition="top center",
                textfont=dict(size=9),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "P_total = %{y:.3f} W<br>"
                    "Confidence = %{x:.0f}%<extra></extra>"
                ),
            )
        )
    fig2.update_layout(
        xaxis_title="Data confidence [%]",
        yaxis_title="Estimated total loss [W]",
        height=450,
        margin=dict(l=0, r=0, t=30, b=40),
    )
    st.plotly_chart(fig2, use_container_width=True)

else:
    # Landing page
    st.markdown(
        """
        ### How it works

        1. **Choose a topology** — Buck, Boost, or Half-bridge/Inverter
        2. **Enter circuit specs** — bus voltage, load current, switching frequency
        3. **Set derating margins** — standard practice is 1.5× on both V and I
        4. **Click "Find transistors"**

        The app queries the [TransistorDatabase](https://github.com/upb-lea/transistordatabase)
        library and estimates losses using:

        | Component | Method |
        |---|---|
        | Switch conduction | Channel linearisation at nearest (T_j, V_g) |
        | Turn-on / Turn-off | Interpolation on E vs I curves, scaled by V_bus/V_supply |
        | Diode conduction | Body-diode channel linearisation |
        | Reverse recovery | E_rr vs I curves (if available) |

        Results are ranked by **total estimated loss** (ascending).
        The **confidence** column shows what fraction of loss components
        could be estimated from available data — treat results with
        < 50 % confidence as incomplete.

        > **Note:** The database must contain transistors. Use
        > `db.update_from_fileexchange()` in Python to download devices
        > from the UPB LEA file exchange, or point "Database folder"
        > at a local folder of JSON files.
        """
    )