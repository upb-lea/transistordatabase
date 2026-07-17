# Transistor Database — Local Edition

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Status](https://img.shields.io/badge/status-alpha-yellow)
![License](https://img.shields.io/badge/license-GPLv3-lightgrey)

A local transistor database with a CLI backend (`szukaj.py`) and a graphical frontend (`GUI.py`).
Transistor data is stored as structured `.json` files and can be searched, filtered, compared, and exported — no internet required.

**Supported categories:** GaN · IGBT · SiC-MOSFET · Si-MOSFET

---

## Table of contents

- [Architecture](#architecture)
- [Requirements](#requirements)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [GUI — tab reference](#gui--tab-reference)
- [CLI — command reference](#cli--command-reference)
- [Search syntax](#search-syntax)
- [Data format](#data-format)
- [PLECS XML export and import](#plecs-xml-export-and-import)
- [Adding a new transistor](#adding-a-new-transistor)
- [Troubleshooting](#troubleshooting)

---

## Architecture

The project is split into two strictly separated layers — the GUI never implements data logic of its own.

| Layer | File | Role |
|---|---|---|
| Core engine | `szukaj.py` | All data operations: loading, querying, exporting, editing |
| Graphical frontend | `GUI.py` | Visual wrapper — delegates everything to `szukaj.py` |

**`szukaj.py`** loads all `.json` files into a flat `pandas.DataFrame`, preprocesses search queries (fuzzy matching, case-insensitive `==`, combined `&`), extracts chart series recursively, and handles all export formats. It can be used entirely standalone from the terminal.

**`GUI.py`** is a Tkinter-based wrapper. It adds a sortable table with per-column filters, inline `matplotlib` chart rendering, a side-by-side comparison view with highlighted differences, and file dialogs for import and export.

---

## Requirements

Python **3.11 or newer**.

```bash
pip install pandas matplotlib pillow
```

> `pypdf` (used for PDF import) and `pyreadline3` (terminal history on Windows) are installed automatically by `szukaj.py` on first run if missing.
> Standard library modules — `tkinter`, `os`, `json`, `xml`, `subprocess` — need no installation.

---

## Project structure

```
TRANSISTORDATABASE/
│
├── GUI.py                       # Graphical frontend
├── szukaj.py                    # CLI backend and data engine
│
├── GaN/                         # One folder per technology category
│   └── 650V/
│       └── GaNSystems_GS66506T.json
├── IGBT/
│   └── 1200V/
├── SiC-MOSFET/
│   └── 900V/
├── Si-MOSFET/
│   └── 650V/
│
├── Exported_Transistors/        # Created by the export command
└── Exported_Comparisons/        # Created by the compare command
```

> The four technology folders are created automatically on first startup if they do not exist.

---

## Getting started

> **Important:** always run from the directory that contains `GUI.py` and `szukaj.py`. Paths are resolved relative to the script location, not the working directory.

```bash
# Graphical interface
python GUI.py

# Interactive CLI
python szukaj.py

# Non-interactive / scripting mode
python szukaj.py --query "v_abs_max >= 1200"
python szukaj.py --query "manufacturer == 'Infineon' & i_abs_max > 50" --export
```

---

## GUI — tab reference

| Tab | What it does |
|---|---|
| 🔍 **Browser** | Sortable table of all loaded transistors. Toggle column visibility and apply per-column text/numeric filters in the side panel. Double-click any row to open its Profile. |
| 🔎 **Search** | Eight quick-filter fields (Name, Category, Manufacturer, V≥, I≥, I\_cont≥, Housing, Technology) plus a raw pandas query box. Uses the same fuzzy preprocessor as the CLI. Results sync back to the Browser. |
| 📋 **Profile** | Full parameter table for one device. Copy a selected value or all parameters as TSV. Choose a chart from the dropdown and open it in a matplotlib window. Open the raw JSON in your system editor. |
| 📊 **Compare** | Build a basket of 2 or more transistors. Renders a side-by-side parameter table — cells where values differ are highlighted. Chart series are shown as mini-plots inside the cells; click any to open the full interactive window. Export common chart series as CSV files. |
| ➕ **Create** | Form for entering scalar parameters with greyed-out placeholders. Attach curve data as CSV files for each graph field. Saves a fully structured JSON via `build_structured_json()`. |
| ✏️ **Edit** | Load a transistor from the dropdown, edit scalar fields and replace curve CSVs inline, then save. Alternatively, open the raw JSON directly in Notepad / gedit. |
| 📥 **Import** | Import a ready-made JSON file, or import a PLECS XML switch + diode pair. |
| 📤 **Export** | Export one transistor (selected from the dropdown) or multiple transistors (selected in the Browser) to JSON, CSV with chart CSVs, or PLECS XML. |

---

## CLI — command reference

At the `search >` prompt:

| Command | Description |
|---|---|
| `help` | Show the full help screen with syntax examples |
| `list` | List all transistors with key parameters |
| `list_params` | Show all active database columns with descriptions |
| `info <param>` | Show the label and description for a specific field |
| `full` | Show all 66 fields for the last single-result query |
| `compare` | Build a comparison basket interactively, then export common chart CSVs |
| `create` | Create a blank JSON template and open it in the system editor |
| `edit` | Pick a transistor and open its JSON in the system editor |
| `import` | Import from a PDF datasheet, a JSON file, or PLECS XML |
| `export` | Export the last query results to JSON, CSV, or PLECS XML |
| `exit` | Quit |

---

## Search syntax

Text fields use **fuzzy partial matching** — `==` is automatically converted to a case-insensitive substring check:

```
name == 'C3M'                            matches any name containing C3M
manufacturer == 'Fuji'                   matches "Fuji Electric"
Category == 'SiC'                        matches "SiC-MOSFET"
v_abs_max >= 1200                        numeric threshold
v_abs_max >= 900 & i_cont > 200          AND of two conditions
v_abs_max == 650 & Category == 'GaN'     combined text and numeric
```

If the query matches exactly one transistor, its profile is displayed immediately.
If it matches multiple, a numbered table is printed — enter a row number to inspect that device.

---

## Data format

Each transistor is stored as one `.json` file. Scalar parameters sit at the root level. Curve data lives inside `switch` and `diode` sub-objects as `[[X values], [Y values]]` pairs.

```json
{
  "name": "GaNSystems_GS66506T",
  "manufacturer": "GaN Systems",
  "type": "GaN-Transistor",
  "v_abs_max": 650,
  "i_cont": 22,
  "r_th_cs": 0.5,

  "switch": {
    "channel": [
      { "t_j": 25,  "v_g": 6, "graph_v_i": [[0.0, 1.0, 2.0], [0.0, 4.0, 9.0]] },
      { "t_j": 125, "v_g": 6, "graph_v_i": [[0.0, 1.0, 2.0], [0.0, 3.0, 7.0]] }
    ],
    "e_on": [
      {
        "t_j": 25, "v_supply": 400, "dataset_type": "graph_i_e",
        "graph_i_e": [[5, 10, 15], [1e-6, 2e-6, 4e-6]]
      }
    ],
    "e_off": [],
    "thermal_foster": {
      "r_th_vector": [0.1, 0.2],
      "tau_vector": [0.01, 0.05]
    }
  },

  "diode": {
    "channel": [],
    "e_rr": []
  }
}
```

All chart keys follow the pattern `"graph_<name>": [[X], [Y]]`. The function `deep_search_charts()` in `szukaj.py` finds every such series recursively, regardless of nesting depth.

---

## PLECS XML export and import

### Export

Reads `switch.channel`, `switch.e_on`, `switch.e_off`, `diode.channel`, `diode.e_rr`, and the Foster thermal network, and produces two files:

```
DeviceName_switch.xml
DeviceName_diode.xml
```

These follow the PLECS semiconductor XML format (v1.1) and can be loaded directly into a PLECS schematic. If energy loss data is absent, zero-filled tables are used so the file still loads without errors.

- **GUI:** Export tab → select transistor → choose **PLECS XML** → click Export
- **CLI:** run `export` after a search → option `[3]`

### Import

Reads `ConductionLoss`, `TurnOnLoss`, `TurnOffLoss`, and the Foster `ThermalModel` section from a PLECS XML file and saves a structured JSON into the correct category folder.

Fields that PLECS XML does not carry (`v_abs_max`, `housing_type`, etc.) are left blank. Fill them in afterwards using the **Edit** tab or the `edit` command.

---

## Adding a new transistor

1. Digitize datasheet curves using [WebPlotDigitizer](https://apps.automeris.io/wpd/) and export each curve as a two-column CSV.
2. In the GUI, open the **Create** tab. Fill in all scalar fields and click **Add curves…** for each graph field to attach the CSVs.
3. Click **Save New Transistor**. The file is placed in `<Category>/<voltage>V/<name>.json`.
4. Switch to the **Edit** tab, load the record, and verify that all values were saved correctly.

Alternatively, use the `create` command in the CLI to generate a blank JSON template, then fill it in a text editor.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'pandas'`**
Run `pip install pandas matplotlib pillow`. If that does not help, make sure you are running pip for the same Python interpreter you use to launch the scripts.

**Database loads 0 transistors**
The four technology folders (`GaN/`, `IGBT/`, `SiC-MOSFET/`, `Si-MOSFET/`) must be in the same directory as `GUI.py` and `szukaj.py`. Always launch the application from inside the project folder.

**PLECS export skipped with "no channel data"**
The JSON must contain at least one entry with a `graph_v_i` key inside `switch.channel`. The diode XML is silently skipped if `diode.channel` is empty.

**JSON validation error after editing**
Notepad does not warn about JSON syntax errors. Common mistakes are trailing commas, unquoted strings, and mismatched brackets. Paste the file content into [jsonlint.com](https://jsonlint.com) to locate the problem.

**`SyntaxError` on startup**
Make sure the file starts with `import tkinter`, not with a bash command. If the file was generated incorrectly, re-download it.

---

## License

Local fork, based on **Transistordatabase** by LEA, University of Paderborn.
Original project licensed under [GPLv3](https://choosealicense.com/licenses/gpl-3.0/).
