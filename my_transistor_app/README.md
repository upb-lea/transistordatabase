# Power Transistor Selector

A workflow application for power electronics engineers.
Enter converter specs → get a ranked, loss-estimated list of suitable switches
drawn from the [TransistorDatabase (TDB)](https://github.com/upb-lea/transistordatabase) v0.5.1.

---

## Architecture

```
transistor_selector/
├── selector/
│   ├── __init__.py
│   ├── models.py          # Pydantic V2 request / response schemas
│   ├── loss_engine.py     # Physics: waveforms, channel linearisation, loss sums
│   └── selector.py        # TransistorSelector class (DB load, filter, rank)
├── api.py                 # FastAPI REST application
├── streamlit_app.py       # Streamlit UI prototype (standalone)
├── requirements.txt
└── README.md
```

### Data-flow

```
CircuitRequirements (Pydantic)
        │
        ▼
compute_waveform()  ──►  CurrentWaveform
        │                 (D, I_rms, I_peak, …)
        ▼
TransistorSelector.select()
  │
  ├─ Filter: V_abs_max ≥ V_bus·v_margin, I_abs_max ≥ I_peak·i_margin
  │
  └─ For each candidate:
       estimate_losses()
         ├─ _linearise_channel()   → P_sw_cond, P_diode_cond
         └─ _best_energy()         → P_sw_on, P_sw_off, P_diode_rr
       data_confidence()
       Rank by (P_total ↑, confidence ↓)
        │
        ▼
SelectionResponse (Pydantic)
```

---

## Quick start

### 1 · Install dependencies

```bash
pip install -r requirements.txt
# If TDB is not on PyPI yet, install from source:
pip install -e /path/to/transistordatabase-main
```

### 2 · Populate the transistor database

```python
import transistordatabase as tdb

db = tdb.DatabaseManager()
db.set_operation_mode_json("/path/to/my/db")   # any writable folder
db.update_from_fileexchange(overwrite=True)     # downloads ~100 devices
```

Or point `TDB_PATH` at an existing JSON folder:
```bash
export TDB_PATH=/path/to/my/db
```

### 3a · Streamlit UI (prototype)

```bash
TDB_PATH=/path/to/my/db streamlit run streamlit_app.py
```

### 3b · FastAPI server

```bash
TDB_PATH=/path/to/my/db uvicorn api:app --reload --host 0.0.0.0 --port 8000
# Docs at http://localhost:8000/docs
```

### 3c · Python library usage

```python
from selector.selector import TransistorSelector
from selector.models import CircuitRequirements, Topology

sel = TransistorSelector(db_path="/path/to/my/db")
req = CircuitRequirements(
    topology=Topology.BUCK,
    v_bus=400.0,
    v_out=200.0,
    i_load=20.0,
    f_sw=50_000,
    t_j_op=125.0,
    v_g=15.0,
    v_margin=1.5,
    i_margin=1.5,
)
resp = sel.select(req)
for r in resp.results[:5]:
    print(f"{r.rank:2d}. {r.name:<30} {r.losses.p_total_w:8.3f} W  ({r.data_confidence_pct:.0f}%)")
```

---

## Loss model

### Topology → current waveform (CCM, low ripple)

| Quantity | Buck | Boost | Half-bridge |
|---|---|---|---|
| D | V_out / V_bus | 1 – V_in / V_bus | 0.5 |
| I_peak | I_load | I_in = I_out/(1–D) | I_load |
| I_sw_rms | I_load·√D | I_in·√D | I_load/2 |
| I_diode_rms | I_load·√(1–D) | I_out·√(1–D) | I_load/2 |

### Loss equations

| Component | Formula |
|---|---|
| Switch conduction | P = V₀·I_mean + R_ch·I_rms² |
| Switch turn-on | P = E_on(I_peak, V_bus)·f_sw |
| Switch turn-off | P = E_off(I_peak, V_bus)·f_sw |
| Diode conduction | P = V_f·I_mean + R_d·I_rms² |
| Diode RR | P = E_rr(I_peak, V_bus)·f_sw |

Voltage scaling: `E(V_bus) ≈ E_meas(V_supply_meas) · V_bus / V_supply_meas`
(linear proportionality — acceptable within ±30 % of V_supply_meas).

### Data lookup strategy

`calc_lin_channel` requires an **exact** `(t_j, v_g)` match in the TDB
channel list.  We avoid this trap by:

1. Finding the **nearest** `(t_j, v_g)` operating point using a
   Euclidean distance metric (T normalised by 10 °C/V).
2. Calling `calc_lin_channel` with those exact values.
3. Wrapping all calls in `try/except` — channel data absence is
   common in the database.

For switching energy:
1. Prefer `graph_i_e` datasets (full I–E curve at known R_g).
2. Fall back to `single` scalar measurements.
3. Skip `graph_r_e` (requires an external R_g choice).

---

## Data-confidence score

| Data available | Weight |
|---|---|
| Switch channel (conduction) | 30 % |
| E_on (turn-on energy) | 25 % |
| E_off (turn-off energy) | 25 % |
| Diode channel (conduction) | 10 % |
| E_rr (reverse recovery) | 10 % |

A transistor with only channel data (no switching curves) scores 30–40 %.
Treat results below 50 % as incomplete — switching losses dominate at high
frequency and will be underestimated.

---

## Known TDB pitfalls

| Pitfall | How we handle it |
|---|---|
| `calc_lin_channel` raises `ValueError` if `(t_j, v_g)` not in data | Use `_linearise_channel()` which finds nearest point first |
| `find_approx_wp` raises `KeyError` if `e_on` or `e_off` is empty | Don't call `update_wp`; access `.e_on`/`.e_off` lists directly |
| `MissingDataError` from export functions | Caught and logged; result recorded as `None` |
| Energy `graph_r_e` datasets need an R_g assumption | Skipped; noted in `missing_data_notes` |
| Linear V-scaling breaks for very different V_supply vs V_bus | V-scale factor flagged in response when > 2× |
| SiC body-diode `v_g` is negative (e.g. −2 V) | Default `diode_v_g = −2 V` for SiC-MOSFET/GaN |
| Transistor JSON load errors (malformed files) | Skipped with a `WARNING` log entry |
