import os
import json
import re
import sys
import argparse
import datetime
import subprocess
import shutil
import platform
import atexit
import xml.etree.ElementTree as ET
import pandas as pd


# Base directory of this module. Use this instead of the current working
# directory so the app behaves the same no matter how it is launched.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# AUTOMATYCZNE INSTALACJE I KONFIGURACJA HISTORII (UP/DOWN ARROWS)
# ---------------------------------------------------------------------------

# Automatyczna instalacja pypdf
try:
    from pypdf import PdfReader
except ModuleNotFoundError:
    print("Missing 'pypdf' library. Installing automatically inside your virtual environment...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf"])
        from pypdf import PdfReader

        print("'pypdf' installed successfully!\n")
    except Exception as e:
        print(f"[WARNING] Automatic installation failed: {e}")
        print("Please run: pip install pypdf manually in your terminal.\n")

# Konfiguracja historii poleceń (strzałki góra/dół) dla Windows / Linux / macOS
try:
    import readline
except ImportError:
    if platform.system() == "Windows":
        print("Missing 'pyreadline3' library for command history on Windows. Installing automatically...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyreadline3"])
            import readline

            print("'pyreadline3' installed successfully!\n")
        except Exception as e:
            print(f"[WARNING] Automatic pyreadline3 installation failed: {e}")
            print("Command history (up/down arrows) might not work. Run: pip install pyreadline3\n")
    else:
        pass

# Trwałe zapisywanie historii do pliku, żeby pamiętał polecenia po restarcie
HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".transistor_db_history")
if 'readline' in sys.modules:
    try:
        readline.read_history_file(HISTORY_FILE)
        readline.set_history_length(1000)  # pamiętaj 1000 ostatnich poleceń
    except FileNotFoundError:
        pass


    def save_history():
        try:
            readline.write_history_file(HISTORY_FILE)
        except Exception:
            pass


    atexit.register(save_history)

# ---------------------------------------------------------------------------
# GLOBALNY SŁOWNIK METADANYCH PARAMETRÓW
# ---------------------------------------------------------------------------
FIELD_META = {
    "Category": {"label": "Category", "desc": "Transistor family (e.g., MOSFET, IGBT, GaN)"},
    "type": {"label": "Type", "desc": "Component configuration type"},
    "technology": {"label": "Technology", "desc": "Main semiconductor material"},
    "manufacturer": {"label": "Manufacturer", "desc": "Manufacturer of the complete component"},
    "author": {"label": "Author", "desc": "Name of the person who created this entry"},
    "comment": {"label": "Comment", "desc": "General comments regarding the database entry"},
    "housing_type": {"label": "Housing Type", "desc": "Package type (e.g., TO-247, TO-220)"},
    "housing_area": {"label": "Housing Area [m2]", "desc": "Total physical footprint area"},
    "cooling_area": {"label": "Cooling Area [m2]", "desc": "Thermal contact surface area"},
    "v_abs_max": {"label": "V_abs_max [V]", "desc": "Absolute maximum blocking voltage"},
    "i_abs_max": {"label": "I_abs_max [A]", "desc": "Absolute maximum peak/pulsed current"},
    "i_cont": {"label": "I_cont [A]", "desc": "Maximum continuous conduction current"},
    "t_c_max": {"label": "T_c_max [°C]", "desc": "Maximum allowable case temperature"},
    "r_g_int": {"label": "R_g_int [Ω]", "desc": "Internal gate resistance"},
    "r_g_on_recommended": {"label": "R_g_on_recommended [Ω]", "desc": "Recommended external turn-on gate resistor"},
    "r_g_off_recommended": {"label": "R_g_off_recommended [Ω]", "desc": "Recommended external turn-off gate resistor"},
    "r_th_cs": {"label": "R_th_cs [K/W]", "desc": "Case-to-sink thermal resistance"},
    "r_th_switch_cs": {"label": "R_th_switch_cs [K/W]", "desc": "Thermal resistance for the switch"},
    "r_th_diode_cs": {"label": "R_th_diode_cs [K/W]", "desc": "Thermal resistance for the diode"},
    "c_iss_fix": {"label": "C_iss_fix [F]", "desc": "Fixed input capacitance"},
    "c_oss_fix": {"label": "C_oss_fix [F]", "desc": "Fixed output capacitance"},
    "c_rss_fix": {"label": "C_rss_fix [F]", "desc": "Fixed reverse transfer capacitance"},
    "datasheet_date": {"label": "Datasheet Date", "desc": "Publication date of the datasheet"},
    "datasheet_version": {"label": "Datasheet Version", "desc": "Document version of the datasheet"},
    "datasheet_hyperlink": {"label": "Datasheet Hyperlink", "desc": "URL to the official datasheet PDF"},
    "template_version": {"label": "Template Version", "desc": "Version of the JSON template"},
    "template_date": {"label": "Template Date", "desc": "Version date of the JSON template"},
    "last_modified": {"label": "Last Modified", "desc": "Date of the last update"},
    "raw_measurement_data": {"label": "Raw Measurement Data", "desc": "Unprocessed laboratory test data"},
    "c_iss": {"label": "C_iss Curves", "desc": "Input capacitance vs. voltage"},
    "c_oss": {"label": "C_oss Curves", "desc": "Output capacitance vs. voltage"},
    "c_rss": {"label": "C_rss Curves", "desc": "Reverse transfer capacitance vs. voltage"},
    "graph_v_ecoss": {"label": "Graph V_E_oss", "desc": "Energy stored in C_oss vs. V_DS"},
    "c_oss_er": {"label": "C_oss_er Plot", "desc": "Energy-related effective C_oss"},
    "c_oss_er_c_o": {"label": "C_oss_er_c_o", "desc": "Capacitance values for energy plot"},
    "c_oss_er_v_ds": {"label": "C_oss_er_v_ds", "desc": "V_DS for energy plot"},
    "c_oss_er_v_gs": {"label": "C_oss_er_v_gs", "desc": "V_GS for energy plot"},
    "c_oss_tr": {"label": "C_oss_tr Plot", "desc": "Time-related effective C_oss"},
    "c_oss_tr_c_o": {"label": "C_oss_tr_c_o", "desc": "Capacitance values for time plot"},
    "c_oss_tr_v_ds": {"label": "C_oss_tr_v_ds", "desc": "V_DS for time plot"},
    "c_oss_tr_v_gs": {"label": "C_oss_tr_v_gs", "desc": "V_GS for time plot"},
    "diode_manufacturer": {"label": "Diode Manufacturer", "desc": "Manufacturer of the diode"},
    "diode_technology": {"label": "Diode Technology", "desc": "Diode material/type"},
    "diode_comment": {"label": "Diode Comment", "desc": "Comments on the diode"},
    "diode_t_j_max": {"label": "Diode T_j_max [°C]", "desc": "Max junction temperature (diode)"},
    "diode_channel": {"label": "Diode Channel (I-V)", "desc": "Diode I-V conduction characteristics"},
    "diode_linearized_diode": {"label": "Linearized Diode", "desc": "Piecewise-linear diode model"},
    "diode_thermal_foster": {"label": "Diode Thermal Foster", "desc": "Foster RC network for diode"},
    "diode_soa": {"label": "Diode SOA", "desc": "Safe Operating Area (diode)"},
    "diode_e_rr": {"label": "Diode E_rr Data", "desc": "Diode reverse recovery energy"},
    "switch_manufacturer": {"label": "Switch Manufacturer", "desc": "Manufacturer of the switch"},
    "switch_technology": {"label": "Switch Technology", "desc": "Transistor technology type"},
    "switch_comment": {"label": "Switch Comment", "desc": "Comments on the switch"},
    "switch_t_j_max": {"label": "Switch T_j_max [°C]", "desc": "Max junction temperature (switch)"},
    "switch_channel": {"label": "Switch Channel (I-V)", "desc": "Transistor output I-V characteristics"},
    "switch_linearized_switch": {"label": "Linearized Switch", "desc": "Piecewise-linear switch model"},
    "switch_r_channel_th": {"label": "Switch R_channel_th", "desc": "Thermal resistance channel data"},
    "switch_thermal_foster": {"label": "Switch Thermal Foster", "desc": "Foster RC network for switch"},
    "switch_soa": {"label": "Switch SOA", "desc": "Safe Operating Area (switch)"},
    "switch_charge_curve": {"label": "Switch Charge Curve", "desc": "Gate charge characteristics"},
    "switch_e_on": {"label": "Switch E_on Data", "desc": "Turn-on switching energy loss"},
    "switch_e_on_meas": {"label": "Switch E_on_meas", "desc": "Measured turn-on energy loss"},
    "switch_e_off": {"label": "Switch E_off Data", "desc": "Turn-off switching energy loss"},
    "switch_e_off_meas": {"label": "Switch E_off_meas", "desc": "Measured turn-off energy loss"}
}


# ---------------------------------------------------------------------------
# HELP
# ---------------------------------------------------------------------------

def print_help():
    print("""
┌──────────────────────────────────────────────────────────────────┐
│              TRANSISTOR DATABASE  –  HELP                        │
├──────────────────────────────────────────────────────────────────┤
│ SPECIAL COMMANDS:                                                │
│   help        – show this help screen                            │
│   list        – list all transistors with key parameters         │
│   list_params – list all active properties with descriptions     │
│   info <param>– show description of a specific parameter         │
│   compare     – overlay chart data from multiple transistors     │
│   create      – create a new blank record (opens editor)         │
│   edit        – open an existing record in the system editor     │
│   import      – import PDF / JSON / PLECS XML files             │
│   export      – export results: JSON / CSV / PLECS XML           │
│   converter   – run converter loss-map analysis (boost/buck/buck-boost)  │
│   exit        – quit the application                             │
├──────────────────────────────────────────────────────────────────┤
│ SEARCH  (Text fields are matched partially & case-insensitive!): │
│   name == 'C3M'                  matches any name with 'C3M'     │
│   manufacturer == 'Fuji'         matches 'Fuji Electric'         │
│   v_abs_max >= 1200              voltage ≥ 1200 V                │
│   i_abs_max > 100                current > 100 A                 │
│   Category == 'SiC'              matches 'SiC-MOSFET'            │
│   v_abs_max >= 900 & manufacturer == 'ROHM'  combined filter     │
├──────────────────────────────────────────────────────────────────┤
│ PROFILE VIEW:                                                    │
│   By default only filled (non-empty) fields are shown.           │
│   Append  'full'  after a single-result query to see all 66:     │
│     search > name == 'CREE'                                      │
│     then at the prompt: full                                     │
│                                                                  │
│ CLI ONE-SHOT MODE (non-interactive):                             │
│   python szukaj.py --query "v_abs_max >= 1200"                   │
│   python szukaj.py --query "Category == 'IGBT'" --export         │
└──────────────────────────────────────────────────────────────────┘
""")


# ---------------------------------------------------------------------------
# QUERY PREPROCESSOR (Text Fuzzy Matching)
# ---------------------------------------------------------------------------

def preprocess_query(q):
    """
    Translates basic == and != string comparisons into pandas substring checks
    so the user doesn't have to type the exact full name (case-insensitive).
    """
    # Convert: col == 'val'  ->  col.str.contains('val', case=False, na=False)
    q = re.sub(r"([a-zA-Z0-9_]+)\s*==\s*(['\"])(.*?)\2",
               r"\1.str.contains(\2\3\2, case=False, na=False)", q)

    # Convert: col != 'val'  ->  (~ col.str.contains('val', case=False, na=False))
    q = re.sub(r"([a-zA-Z0-9_]+)\s*!=\s*(['\"])(.*?)\2",
               r"(~ \1.str.contains(\2\3\2, case=False, na=False))", q)
    return q


# ---------------------------------------------------------------------------
# DATABASE LOADER
# ---------------------------------------------------------------------------

def load_full_database():
    """Scans folders and loads core transistor data for searching, remembering original file paths."""
    transistor_list = []
    tech_folders = ['GaN', 'IGBT', 'SiC-MOSFET', 'Si-MOSFET']

    print("Loading database, please wait...")

    for main_folder in tech_folders:
        main_folder_path = os.path.join(BASE_DIR, main_folder)
        if not os.path.exists(main_folder_path):
            os.makedirs(main_folder_path, exist_ok=True)
            continue

        for root_path, _, files in os.walk(main_folder_path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root_path, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                            flattened_data = {}
                            # Unroll nested json structure for searching while keeping compatibility
                            for key, value in data.items():
                                if isinstance(value, dict):
                                    for k, v in value.items():
                                        if isinstance(v, dict) and 'value' in v:
                                            flattened_data[f"{key}_{k}"] = v['value']
                                        else:
                                            flattened_data[f"{key}_{k}"] = v
                                elif isinstance(value, list):
                                    flattened_data[key] = value
                                else:
                                    flattened_data[key] = value

                            # Standardized fallback injection if root keys were flat
                            for k in ['name', 'manufacturer', 'type', 'housing_type', 'author', 'v_abs_max',
                                      'i_abs_max', 'r_th_cs']:
                                if k in data and k not in flattened_data:
                                    flattened_data[k] = data[k]

                            flattened_data['Category'] = main_folder
                            flattened_data['Subfolder'] = os.path.basename(root_path)
                            flattened_data['_original_file_path'] = file_path

                            transistor_list.append(flattened_data)
                    except Exception:
                        continue

    if not transistor_list:
        print("Database is currently empty or no *.json files found.")
        return pd.DataFrame(columns=['name', 'manufacturer', 'Category', 'Subfolder'])

    df = pd.DataFrame(transistor_list)
    print(f"Success! Loaded {len(df)} transistors.")

    # Automatic conversion of text columns to numeric for query filtering
    num_cols = ['v_abs_max', 'i_abs_max', 'i_cont', 't_c_max', 'r_g_int', 'r_th_cs']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df.columns = [c.replace('.', '_').replace('-', '_') if c != '_original_file_path' else c for c in df.columns]
    return df


# ---------------------------------------------------------------------------
# CHART SEARCH (deep recursive)
# ---------------------------------------------------------------------------

def deep_search_charts(obj, output_folder=None, name_path="", found_charts=None):
    """Recursively searches the ENTIRE JSON file for ANY chart series (X, Y).
    If output_folder is provided, saves them to files and returns count (int).
    If output_folder is None, populates and returns the found_charts dictionary."""

    if output_folder is None:
        # Collection mode: build a dictionary of charts (used by 'compare')
        if found_charts is None:
            found_charts = {}

        if isinstance(obj, dict):
            tj = obj.get('t_j', obj.get('T_j', ''))
            str_tj = f"_tj{tj}" if tj != '' else ""
            for k, v in obj.items():
                new_path = f"{name_path}_{k}" if name_path else k
                if k.startswith('graph_') and isinstance(v, list) and len(v) >= 2:
                    if isinstance(v[0], list) and isinstance(v[1], list) and len(v[0]) == len(v[1]) and len(v[0]) > 0:
                        chart_key = new_path
                        if chart_key not in found_charts:
                            found_charts[chart_key] = []
                        found_charts[chart_key].append({'tj': str_tj, 'data': v})
                        continue
                deep_search_charts(v, None, new_path, found_charts)
        elif isinstance(obj, list):
            for element in obj:
                deep_search_charts(element, None, name_path, found_charts)
        return found_charts

    else:
        # File-write mode: save charts as CSV files (used by 'export')
        counter = 0
        if isinstance(obj, dict):
            tj = obj.get('t_j', obj.get('T_j', ''))
            str_tj = f"_tj{tj}" if tj != '' else ""
            for k, v in obj.items():
                new_path = f"{name_path}_{k}" if name_path else k
                if k.startswith('graph_') and isinstance(v, list) and len(v) >= 2:
                    if isinstance(v[0], list) and isinstance(v[1], list) and len(v[0]) == len(v[1]) and len(v[0]) > 0:
                        try:
                            df_chart = pd.DataFrame({'X': v[0], 'Y': v[1]})
                            csv_name = f"Chart_{new_path}{str_tj}.csv".replace('__', '_').replace(' ', '_')
                            df_chart.to_csv(os.path.join(output_folder, csv_name), index=False, sep=';')
                            counter += 1
                        except Exception:
                            pass
                        continue
                counter += deep_search_charts(v, output_folder, new_path)
        elif isinstance(obj, list):
            for element in obj:
                counter += deep_search_charts(element, output_folder, name_path)
        return counter


# ---------------------------------------------------------------------------
# EXPORT
# ---------------------------------------------------------------------------

def export_folder_structure(results_df, data_format=None):
    """Creates a separate folder for each transistor with separate CSV charts and JSON/CSV data."""
    if results_df.empty:
        print("No data to export.")
        return

    print(f"\n--- Exporting folder structure for {len(results_df)} transistors ---")

    # Accept format as argument (passed from interactive_search) or ask
    if data_format is None:
        data_format = input("Choose technical data format (json / csv): ").strip().lower()

    if data_format not in ['json', 'csv']:
        print("Invalid format. Aborting.")
        return

    main_output_folder = os.path.join(BASE_DIR, "Exported_Transistors")
    os.makedirs(main_output_folder, exist_ok=True)

    for _, row in results_df.iterrows():
        transistor_name = str(row.get('name', row.get('id', 'Unknown'))).replace('/', '_').replace('\\', '_')

        transistor_folder = os.path.join(main_output_folder, transistor_name)
        os.makedirs(transistor_folder, exist_ok=True)

        source_path = row['_original_file_path']
        try:
            with open(source_path, 'r', encoding='utf-8') as f_src:
                original_json = json.load(f_src)
            chart_count = deep_search_charts(original_json, transistor_folder)
        except Exception as e:
            print(f"Error reading charts: {e}")
            chart_count = 0

        # Create clean dataset without full charts for data export file
        clean_data = {}
        for k, v in row.items():
            if k == '_original_file_path':
                continue
            if isinstance(v, (list, dict)) or (isinstance(v, str) and ("graph_" in v or "graph_i_v" in v)):
                clean_data[k] = f"[Chart/List Data - Extracted into separate CSV files]"
            else:
                clean_data[k] = v

        if chart_count == 0:
            with open(os.path.join(transistor_folder, "NO_CHART_DATA.txt"), "w") as f_info:
                f_info.write("This model did not contain any embedded data series for charts.")

        if data_format == 'json':
            data_path = os.path.join(transistor_folder, f"{transistor_name}.json")
            with open(data_path, 'w', encoding='utf-8') as f_out:
                json.dump(clean_data, f_out, indent=4, ensure_ascii=False)

        elif data_format == 'csv':
            data_path = os.path.join(transistor_folder, f"Data_{transistor_name}.csv")
            try:
                df_params = pd.DataFrame([clean_data])
                df_params.to_csv(data_path, index=False, sep=';', encoding='utf-8-sig')
            except Exception as e:
                print(f"Error saving CSV data for {transistor_name}: {e}")

    print(f"\n[SUCCESS] Export completed successfully!")
    print(f"Data can be found in: {os.path.abspath(main_output_folder)}\n")


# ---------------------------------------------------------------------------
# JSON BUILDER
# ---------------------------------------------------------------------------

def build_structured_json(flat_inputs):
    """Nests flat answers into a standard structured JSON object model."""

    def format_val(v):
        if v == "" or v is None: return ""
        if isinstance(v, (int, float)): return v
        if str(v).isdigit(): return int(v)
        if str(v).replace('.', '', 1).isdigit(): return float(v)
        return v

    structured = {
        "name": flat_inputs.get("name", ""),
        "manufacturer": flat_inputs.get("manufacturer", ""),
        "type": flat_inputs.get("type", ""),
        "technology": flat_inputs.get("technology", ""),
        "housing_type": flat_inputs.get("housing_type", ""),
        "housing_area": format_val(flat_inputs.get("housing_area")),
        "cooling_area": format_val(flat_inputs.get("cooling_area")),
        "author": flat_inputs.get("author", ""),
        "creation_date": flat_inputs.get("creation_date", ""),
        "last_modified": flat_inputs.get("last_modified", ""),
        "template_version": flat_inputs.get("template_version", ""),
        "template_date": flat_inputs.get("template_date", ""),
        "datasheet_version": flat_inputs.get("datasheet_version", ""),
        "datasheet_date": flat_inputs.get("datasheet_date", ""),
        "datasheet_hyperlink": flat_inputs.get("datasheet_hyperlink", ""),
        "comment": flat_inputs.get("comment", ""),

        "v_abs_max": format_val(flat_inputs.get("v_abs_max")),
        "i_abs_max": format_val(flat_inputs.get("i_abs_max")),
        "i_cont": format_val(flat_inputs.get("i_cont")),
        "t_c_max": format_val(flat_inputs.get("t_c_max")),
        "r_g_int": format_val(flat_inputs.get("r_g_int")),
        "r_g_on_recommended": format_val(flat_inputs.get("r_g_on_recommended")),
        "r_g_off_recommended": format_val(flat_inputs.get("r_g_off_recommended")),
        "r_th_cs": format_val(flat_inputs.get("r_th_cs")),
        "r_th_switch_cs": format_val(flat_inputs.get("r_th_switch_cs")),
        "r_th_diode_cs": format_val(flat_inputs.get("r_th_diode_cs")),

        "c_iss": format_val(flat_inputs.get("c_iss")),
        "c_iss_fix": format_val(flat_inputs.get("c_iss_fix")),
        "c_oss": format_val(flat_inputs.get("c_oss")),
        "c_oss_fix": format_val(flat_inputs.get("c_oss_fix")),
        "c_oss_tr": format_val(flat_inputs.get("c_oss_tr")),
        "c_oss_tr_c_o": format_val(flat_inputs.get("c_oss_tr_c_o")),
        "c_oss_tr_v_ds": format_val(flat_inputs.get("c_oss_tr_v_ds")),
        "c_oss_tr_v_gs": format_val(flat_inputs.get("c_oss_tr_v_gs")),
        "c_oss_er": format_val(flat_inputs.get("c_oss_er")),
        "c_oss_er_c_o": format_val(flat_inputs.get("c_oss_er_c_o")),
        "c_oss_er_v_ds": format_val(flat_inputs.get("c_oss_er_v_ds")),
        "c_oss_er_v_gs": format_val(flat_inputs.get("c_oss_er_v_gs")),
        "c_rss": format_val(flat_inputs.get("c_rss")),
        "c_rss_fix": format_val(flat_inputs.get("c_rss_fix")),

        "diode": {
            "manufacturer": flat_inputs.get("diode_manufacturer", ""),
            "technology": flat_inputs.get("diode_technology", ""),
            "t_j_max": format_val(flat_inputs.get("diode_t_j_max")),
            "comment": flat_inputs.get("diode_comment", ""),
            "channel": flat_inputs.get("diode_channel", []),
            "linearized_diode": flat_inputs.get("diode_linearized_diode", []),
            "thermal_foster": flat_inputs.get("diode_thermal_foster", {}),
            "soa": flat_inputs.get("diode_soa", []),
            "e_rr": flat_inputs.get("diode_e_rr", [])
        },

        "switch": {
            "manufacturer": flat_inputs.get("switch_manufacturer", ""),
            "technology": flat_inputs.get("switch_technology", ""),
            "t_j_max": format_val(flat_inputs.get("switch_t_j_max")),
            "comment": flat_inputs.get("switch_comment", ""),
            "channel": flat_inputs.get("switch_channel", []),
            "linearized_switch": flat_inputs.get("switch_linearized_switch", []),
            "r_channel_th": flat_inputs.get("switch_r_channel_th", []),
            "thermal_foster": flat_inputs.get("switch_thermal_foster", {}),
            "soa": flat_inputs.get("switch_soa", []),
            "charge_curve": flat_inputs.get("switch_charge_curve", []),
            "e_on": format_val(flat_inputs.get("switch_e_on")),
            "e_on_meas": format_val(flat_inputs.get("switch_e_on_meas")),
            "e_off": format_val(flat_inputs.get("switch_e_off")),
            "e_off_meas": format_val(flat_inputs.get("switch_e_off_meas"))
        },

        "graph_v_ecoss": flat_inputs.get("graph_v_ecoss", []),
        "raw_measurement_data": flat_inputs.get("raw_measurement_data", "")
    }
    return structured


# ---------------------------------------------------------------------------
# IMPORT: ready JSON file
# ---------------------------------------------------------------------------

def import_ready_json_file():
    """Reads an external JSON data structure, identifies categorization, and saves it into the repository."""
    print("\n--- Direct JSON File Import ---")
    json_path = input("Enter the full path to the JSON file: ").strip().strip('"\'')

    if not os.path.exists(json_path) or not json_path.endswith('.json'):
        print("[ERROR] Valid JSON file not found.")
        return False

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Could not parse JSON file: {e}")
        return False

    name = data.get("name", "").strip()
    if not name:
        print("[ERROR] The JSON structure must contain at least a non-empty 'name' field.")
        return False

    tech_folders = ['GaN', 'IGBT', 'SiC-MOSFET', 'Si-MOSFET']
    device_type = str(data.get('type', data.get('technology', 'SiC-MOSFET')))

    correct_tech = "SiC-MOSFET"
    for folder in tech_folders:
        if folder.upper() in device_type.upper():
            correct_tech = folder
            break

    v_abs = str(data.get("v_abs_max", "")).strip()
    if v_abs.replace('.', '', 1).isdigit():
        v_abs = str(int(float(v_abs)))

    subfolder_name = f"{v_abs}V" if v_abs else "Unsorted"

    dest_dir = os.path.join(correct_tech, subfolder_name)
    os.makedirs(dest_dir, exist_ok=True)

    clean_fn = "".join([c if c.isalnum() or c in ('_', '-') else '_' for c in name]) + ".json"
    dest_file_path = os.path.join(dest_dir, clean_fn)

    try:
        with open(dest_file_path, 'w', encoding='utf-8') as f_out:
            json.dump(data, f_out, indent=4, ensure_ascii=False)
        print(f"\n[SUCCESS] External JSON record imported and organized successfully!")
        print(f"Target Path: {os.path.normpath(dest_file_path)}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save JSON file into repository: {e}")
        return False


# ---------------------------------------------------------------------------
# IMPORT: PDF datasheet wizard
# ---------------------------------------------------------------------------

def parse_pdf_datasheet_comprehensive():
    """Reads a PDF, guesses core values via Regex heuristics, and runs an exhaustive data input wizard."""
    print("\n--- Comprehensive PDF Datasheet Parser & Data Entry Wizard ---")
    pdf_path = input("Enter the full path to the PDF file: ").strip().strip('"\'')

    if not os.path.exists(pdf_path) or not pdf_path.endswith('.pdf'):
        print("[ERROR] Valid PDF file not found.")
        return False

    print("Scanning PDF structure for basic keywords...")
    full_text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages[:3]:
            text = page.extract_text()
            if text: full_text += text + "\n"
    except Exception as e:
        print(f"[ERROR] Could not read PDF file: {e}")
        return False

    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    g_name = base_filename
    name_match = re.search(r'\b([A-Z0-9]{6,15})\b', full_text[:300])
    if name_match: g_name = name_match.group(1)

    g_manuf = "Unknown"
    for brand in ["Wolfspeed", "GaN Systems", "Infineon", "STMicroelectronics", "ROHM", "Cree", "Fuji Electric"]:
        if brand.lower() in full_text.lower():
            g_manuf = brand
            break

    g_type = "SiC-MOSFET"
    if "gan" in full_text.lower():
        g_type = "GaN-Transistor"
    elif "igbt" in full_text.lower():
        g_type = "IGBT"
    elif "silicon mosfet" in full_text.lower() or "si mosfet" in full_text.lower():
        g_type = "Si-MOSFET"

    g_vmax = ""
    v_matches = re.findall(r'\b(600|650|900|1200|1700)\s*V\b', full_text, re.IGNORECASE)
    if v_matches: g_vmax = v_matches[0]

    g_imax = ""
    i_matches = re.findall(r'\b(\d{1,3})\s*A\b', full_text)
    if i_matches: g_imax = i_matches[0]

    current_date_str = datetime.date.today().strftime("%Y-%m-%d")

    w_data = {}

    print("\n========================================================")
    print("  DATA ENTRY WIZARD: Press Enter to accept [Default].")
    print("========================================================\n")

    w_data["name"] = input(f"name [{g_name}]: ").strip() or g_name
    w_data["manufacturer"] = input(f"manufacturer [{g_manuf}]: ").strip() or g_manuf
    w_data["type"] = input(f"type [{g_type}]: ").strip() or g_type
    w_data["technology"] = input(f"technology [{g_type}]: ").strip() or g_type
    w_data["housing_type"] = input("housing_type [Unknown]: ").strip() or "Unknown"
    w_data["housing_area"] = input("housing_area []: ").strip() or ""
    w_data["cooling_area"] = input("cooling_area []: ").strip() or ""
    w_data["author"] = input("author [Local Wizard]: ").strip() or "Local Wizard"
    w_data["creation_date"] = input(f"creation_date [{current_date_str}]: ").strip() or current_date_str
    w_data["last_modified"] = current_date_str
    w_data["template_version"] = input("template_version [0.4.1]: ").strip() or "0.4.1"
    w_data["template_date"] = input(f"template_date [{current_date_str}]: ").strip() or current_date_str
    w_data["datasheet_version"] = input("datasheet_version [Rev. 0]: ").strip() or "Rev. 0"
    w_data["datasheet_date"] = input("datasheet_date []: ").strip() or ""
    w_data["datasheet_hyperlink"] = input("datasheet_hyperlink [Local PDF]: ").strip() or "Local PDF"
    w_data["comment"] = input("comment []: ").strip() or ""

    w_data["v_abs_max"] = input(f"v_abs_max [{g_vmax}]: ").strip() or g_vmax
    w_data["i_abs_max"] = input(f"i_abs_max [{g_imax}]: ").strip() or g_imax
    w_data["i_cont"] = input("i_cont []: ").strip() or ""
    w_data["t_c_max"] = input("t_c_max [150]: ").strip() or "150"
    w_data["r_g_int"] = input("r_g_int []: ").strip() or ""
    w_data["r_g_on_recommended"] = input("r_g_on_recommended []: ").strip() or ""
    w_data["r_g_off_recommended"] = input("r_g_off_recommended []: ").strip() or ""
    w_data["r_th_cs"] = input("r_th_cs [0.0]: ").strip() or "0.0"
    w_data["r_th_switch_cs"] = input("r_th_switch_cs []: ").strip() or ""
    w_data["r_th_diode_cs"] = input("r_th_diode_cs []: ").strip() or ""

    print("\n--- Capacitance Specifications ---")
    w_data["c_iss"] = input("c_iss []: ").strip() or ""
    w_data["c_iss_fix"] = input("c_iss_fix []: ").strip() or ""
    w_data["c_oss"] = input("c_oss []: ").strip() or ""
    w_data["c_oss_fix"] = input("c_oss_fix []: ").strip() or ""
    w_data["c_oss_tr"] = input("c_oss_tr []: ").strip() or ""
    w_data["c_oss_tr_c_o"] = input("c_oss_tr_c_o []: ").strip() or ""
    w_data["c_oss_tr_v_ds"] = input("c_oss_tr_v_ds []: ").strip() or ""
    w_data["c_oss_tr_v_gs"] = input("c_oss_tr_v_gs []: ").strip() or ""
    w_data["c_oss_er"] = input("c_oss_er []: ").strip() or ""
    w_data["c_oss_er_c_o"] = input("c_oss_er_c_o []: ").strip() or ""
    w_data["c_oss_er_v_ds"] = input("c_oss_er_v_ds []: ").strip() or ""
    w_data["c_oss_er_v_gs"] = input("c_oss_er_v_gs []: ").strip() or ""
    w_data["c_rss"] = input("c_rss []: ").strip() or ""
    w_data["c_rss_fix"] = input("c_rss_fix []: ").strip() or ""

    print("\n--- Embedded Diode Specifications ---")
    w_data["diode_manufacturer"] = input(f"diode_manufacturer [{w_data['manufacturer']}]: ").strip() or w_data[
        'manufacturer']
    w_data["diode_technology"] = input("diode_technology []: ").strip() or ""
    w_data["diode_t_j_max"] = input("diode_t_j_max [150]: ").strip() or "150"
    w_data["diode_comment"] = input("diode_comment []: ").strip() or ""
    w_data["diode_channel"] = []
    w_data["diode_linearized_diode"] = []
    w_data["diode_thermal_foster"] = {}
    w_data["diode_soa"] = []
    w_data["diode_e_rr"] = []

    print("\n--- Main Switch Specifications ---")
    w_data["switch_manufacturer"] = input(f"switch_manufacturer [{w_data['manufacturer']}]: ").strip() or w_data[
        'manufacturer']
    w_data["switch_technology"] = input(f"switch_technology [{w_data['technology']}]: ").strip() or w_data['technology']
    w_data["switch_t_j_max"] = input("switch_t_j_max [150]: ").strip() or "150"
    w_data["switch_comment"] = input("switch_comment []: ").strip() or ""
    w_data["switch_channel"] = []
    w_data["switch_linearized_switch"] = []
    w_data["switch_r_channel_th"] = []
    w_data["switch_thermal_foster"] = {}
    w_data["switch_soa"] = []
    w_data["switch_charge_curve"] = []
    w_data["switch_e_on"] = input("switch_e_on []: ").strip() or ""
    w_data["switch_e_on_meas"] = input("switch_e_on_meas []: ").strip() or ""
    w_data["switch_e_off"] = input("switch_e_off []: ").strip() or ""
    w_data["switch_e_off_meas"] = input("switch_e_off_meas []: ").strip() or ""

    print("\n--- Additional Charts & Data Series ---")
    w_data["graph_v_ecoss"] = []
    w_data["raw_measurement_data"] = input("raw_measurement_data []: ").strip() or ""

    # --- Confirmation before saving ---
    print("\n--- Summary of key fields ---")
    for k in ['name', 'manufacturer', 'type', 'v_abs_max', 'i_abs_max', 't_c_max']:
        print(f"  {k:25s}: {w_data.get(k, '-')}")
    confirm = input("\nSave this record? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Save cancelled.")
        return False

    tech_folders = ['GaN', 'IGBT', 'SiC-MOSFET', 'Si-MOSFET']
    correct_tech = "SiC-MOSFET"
    for folder in tech_folders:
        if folder.upper() in str(w_data['type']).upper():
            correct_tech = folder
            break

    v_folder_str = str(w_data['v_abs_max']).strip()
    if v_folder_str.replace('.', '', 1).isdigit():
        v_folder_str = str(int(float(v_folder_str)))

    default_sub = f"{v_folder_str}V" if v_folder_str else "Unsorted"
    subfolder_name = input(
        f"\nEnter target subfolder (Category: {correct_tech}) [Press Enter for '{default_sub}']: ").strip() or default_sub

    final_json_data = build_structured_json(w_data)

    dest_dir = os.path.join(correct_tech, subfolder_name)
    os.makedirs(dest_dir, exist_ok=True)
    clean_fn = "".join([c if c.isalnum() or c in ('_', '-') else '_' for c in final_json_data['name']]) + ".json"
    dest_file_path = os.path.join(dest_dir, clean_fn)

    try:
        with open(dest_file_path, 'w', encoding='utf-8') as f_out:
            json.dump(final_json_data, f_out, indent=4, ensure_ascii=False)
        print(f"\n[SUCCESS] Formatted comprehensive structure saved successfully!")
        print(f"Path: {os.path.normpath(dest_file_path)}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to compile and save JSON structure: {e}")
        return False


# ---------------------------------------------------------------------------
# DISPLAY PROFILE
# ---------------------------------------------------------------------------

def display_transistor_profile(row, show_all=False):
    """Displays transistor parameters.
    By default only filled (non-empty/non-chart) fields are shown.
    Pass show_all=True to display all 66 fields."""

    print("\n" + "=" * 65)
    print(f"  MODEL PROFILE: {row.get('name', 'Unknown')}")
    if not show_all:
        print("  (showing filled fields only – type 'full' to see all 66)")
    print("=" * 65)

    requested_fields = [
        "Category", "Subfolder", "author", "c_iss", "c_iss_fix", "c_oss", "c_oss_er",
        "c_oss_er_c_o", "c_oss_er_v_ds", "c_oss_er_v_gs", "c_oss_fix", "c_oss_tr",
        "c_oss_tr_c_o", "c_oss_tr_v_ds", "c_oss_tr_v_gs", "c_rss", "c_rss_fix", "comment",
        "cooling_area", "creation_date", "datasheet_date", "datasheet_hyperlink",
        "datasheet_version", "diode_channel", "diode_comment", "diode_e_rr",
        "diode_linearized_diode", "diode_manufacturer", "diode_soa", "diode_t_j_max",
        "diode_technology", "diode_thermal_foster", "graph_v_ecoss", "housing_area",
        "housing_type", "i_abs_max", "i_cont", "last_modified", "manufacturer", "name",
        "r_g_int", "r_g_off_recommended", "r_g_on_recommended", "r_th_cs", "r_th_diode_cs",
        "r_th_switch_cs", "raw_measurement_data", "switch_channel", "switch_charge_curve",
        "switch_comment", "switch_e_off", "switch_e_off_meas", "switch_e_on", "switch_e_on_meas",
        "switch_linearized_switch", "switch_manufacturer", "switch_r_channel_th", "switch_soa",
        "switch_t_j_max", "switch_technology", "switch_thermal_foster", "t_c_max", "technology",
        "template_date", "template_version", "type", "v_abs_max"
    ]

    CHART_PLACEHOLDER = "[Chart/List Data - Use 'export' command to generate CSV]"

    for key in requested_fields:
        val = row.get(key, None)

        if isinstance(val, (list, dict)):
            val_str = "None" if len(val) == 0 else CHART_PLACEHOLDER
        elif "graph_" in key or "graph_i_v" in key or "thermal_foster" in key:
            val_str = CHART_PLACEHOLDER
        else:
            try:
                is_nan = pd.isna(val)
            except (TypeError, ValueError):
                is_nan = False
            if is_nan or str(val).strip() in ["", "N/A", "None"]:
                val_str = "None"
            else:
                val_str = str(val)

        # In compact mode: skip empty fields and chart placeholders
        if not show_all and val_str in ("None", CHART_PLACEHOLDER):
            continue

        print(f"  • {key.ljust(30)}: {val_str}")

    print("=" * 65)


# ---------------------------------------------------------------------------
# SYSTEM EDITOR
# ---------------------------------------------------------------------------

def open_system_editor(file_path):
    """Utility helper to invoke the native operating system's default text editor."""
    try:
        if sys.platform == "win32":
            subprocess.run(["notepad.exe", file_path])
        elif sys.platform == "darwin":
            subprocess.run(["open", "-w", file_path])
        else:
            opened = False
            for editor in ["xdg-open", "gedit", "nano"]:
                if shutil.which(editor):
                    subprocess.run([editor, file_path])
                    opened = True
                    break
            if not opened:
                print("[ERROR] Could not find any system text editor automatically.")
                return False
        return True
    except Exception as e:
        print(f"[ERROR] Failed to invoke editor system process: {e}")
        return False


# ---------------------------------------------------------------------------
# INTERACTIVE TRANSISTOR SELECTOR (SINGLE SEARCH - USED BY EDIT)
# ---------------------------------------------------------------------------

def select_transistors_interactively(df, min_count=1, prompt_label="transistor"):
    """Lets the user pick transistors from a numbered list filtered by a name fragment.
    Returns a list of selected name strings."""

    fragment = input(f"Filter by name fragment (Enter = show all): ").strip()
    if fragment:
        candidates = df[df['name'].str.contains(fragment, case=False, na=False)]['name'].tolist()
    else:
        candidates = df['name'].dropna().tolist()

    if not candidates:
        print("[INFO] No transistors match that fragment.")
        return []

    for i, name in enumerate(candidates, 1):
        print(f"  [{i:>3}] {name}")

    raw = input(
        f"\nEnter number(s) separated by commas (min {min_count}): "
    ).strip()

    selected = []
    for part in raw.split(','):
        part = part.strip()
        if part.isdigit():
            idx = int(part)
            if 1 <= idx <= len(candidates):
                name = candidates[idx - 1]
                if name not in selected:
                    selected.append(name)

    if len(selected) < min_count:
        print(f"[ERROR] At least {min_count} selection(s) required.")
        return []

    return selected


# ---------------------------------------------------------------------------
# EDIT
# ---------------------------------------------------------------------------

def edit_transistor_file(df):
    """Finds a transistor via interactive selection and opens its source JSON in the native OS editor."""
    print("\n--- Edit Transistor Record ---")

    names = select_transistors_interactively(df, min_count=1)
    if not names:
        return False
    t_name = names[0]

    matches = df[df['name'] == t_name]
    if matches.empty:
        print(f"[ERROR] No transistor found with name '{t_name}'.")
        return False

    file_path = matches.iloc[0]['_original_file_path']
    print(f"Found database file: {os.path.normpath(file_path)}")
    print("Opening system text editor... Please edit, SAVE, and CLOSE the editor window.")

    if open_system_editor(file_path):
        try:
            print("\n[INFO] Editor closed. Validation check initiated...")
            with open(file_path, "r", encoding="utf-8") as verify_f:
                json.load(verify_f)
            print("[SUCCESS] JSON structure validated! Reloading active repository records...")
            return True
        except json.JSONDecodeError as je:
            print(f"\n[CRITICAL ERROR] Failed to parse JSON after editing: {je}")
            return False
    return False


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def create_new_transistor_template():
    """Generates a comprehensive blank structural JSON file template and opens it in the OS editor."""
    print("\n--- Create New Transistor Template ---")
    name = input("Enter the unique name for the new transistor (e.g., Wolfspeed_C3M0015065D): ").strip()
    if not name:
        print("[ERROR] Name cannot be blank.")
        return False

    print("\nSelect Technology Class Category:")
    print("  [1] GaN")
    print("  [2] IGBT")
    print("  [3] SiC-MOSFET")
    print("  [4] Si-MOSFET")
    tech_choice = input("Choose category [1-4]: ").strip()

    tech_map = {"1": "GaN", "2": "IGBT", "3": "SiC-MOSFET", "4": "Si-MOSFET"}
    category = tech_map.get(tech_choice, "SiC-MOSFET")

    v_abs = input("Enter maximum absolute rating voltage (v_abs_max) [e.g. 1200]: ").strip()
    if v_abs.replace('.', '', 1).isdigit():
        v_abs = str(int(float(v_abs)))
    subfolder = f"{v_abs}V" if v_abs else "Unsorted"

    current_date = datetime.date.today().strftime("%Y-%m-%d")

    template_inputs = {
        "name": name, "manufacturer": "", "type": category, "technology": category,
        "housing_type": "", "housing_area": "", "cooling_area": "",
        "author": "Local Database Creator", "creation_date": current_date, "last_modified": current_date,
        "template_version": "0.4.1", "template_date": current_date, "datasheet_version": "",
        "datasheet_date": "", "datasheet_hyperlink": "", "comment": "",
        "v_abs_max": v_abs, "i_abs_max": "", "i_cont": "", "t_c_max": 150,
        "r_g_int": "", "r_g_on_recommended": "", "r_g_off_recommended": "",
        "r_th_cs": 0.0, "r_th_switch_cs": "", "r_th_diode_cs": "",
        "c_iss": "", "c_iss_fix": "", "c_oss": "", "c_oss_fix": "",
        "c_oss_tr": "", "c_oss_tr_c_o": "", "c_oss_tr_v_ds": "", "c_oss_tr_v_gs": "",
        "c_oss_er": "", "c_oss_er_c_o": "", "c_oss_er_v_ds": "", "c_oss_er_v_gs": "",
        "c_rss": "", "c_rss_fix": "",
        "diode_manufacturer": "", "diode_technology": "", "diode_t_j_max": 150, "diode_comment": "",
        "switch_manufacturer": "", "switch_technology": "", "switch_t_j_max": 150, "switch_comment": "",
        "switch_e_on": "", "switch_e_on_meas": "", "switch_e_off": "", "switch_e_off_meas": "",
        "raw_measurement_data": ""
    }

    structured_template = build_structured_json(template_inputs)

    target_dir = os.path.join(category, subfolder)
    os.makedirs(target_dir, exist_ok=True)

    clean_fn = "".join([c if c.isalnum() or c in ('_', '-') else '_' for c in name]) + ".json"
    file_path = os.path.join(target_dir, clean_fn)

    if os.path.exists(file_path):
        overwrite = input(f"[WARNING] File '{clean_fn}' already exists. Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Creation cancelled.")
            return False

    try:
        with open(file_path, "w", encoding="utf-8") as f_out:
            json.dump(structured_template, f_out, indent=4, ensure_ascii=False)

        print(f"\n[INFO] Blueprint template file saved to: {os.path.normpath(file_path)}")
        print("Opening system text editor... Fill in your values, SAVE, and CLOSE the editor window.")

        if open_system_editor(file_path):
            print("\n[INFO] Editor closed. Validating schema...")
            with open(file_path, "r", encoding="utf-8") as verify_f:
                json.load(verify_f)
            print("[SUCCESS] New transistor record established and validated successfully!")
            return True
    except json.JSONDecodeError as je:
        print(f"\n[CRITICAL ERROR] The template was saved, but you introduced a syntax error during modification: {je}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to properly compile and structure template file: {e}")
        return False


# ---------------------------------------------------------------------------
# COMPARE (Zaktualizowane do trybu "Koszyka")
# ---------------------------------------------------------------------------

def compare_transistor_charts(df, preselected_names=None):
    """Allows iteratively building a list of transistors to compare, then exports common chart CSVs."""
    print("\n--- Compare & Overlay Multiple Chart Datasets ---")
    print("Search for transistors to add them to your comparison list.")
    print("Press Enter on an empty search prompt to finish adding and proceed.\n")

    transistor_names = []
    if preselected_names:
        transistor_names.extend(preselected_names)

    # --- Pętla "Koszyka" ---
    while True:
        if transistor_names:
            print(f"\n--- Currently selected for comparison ({len(transistor_names)}) ---")
            for tn in transistor_names:
                print(f"  • {tn}")
        else:
            print("\n--- Currently selected: 0 ---")

        fragment = input("\nEnter name fragment to search (or press Enter to finish): ").strip()

        # Jeśli użytkownik wcisnął Enter bez wpisywania wyszukiwania
        if not fragment:
            if len(transistor_names) >= 2:
                break
            elif len(transistor_names) == 0:
                print("[INFO] Comparison cancelled (no transistors selected).")
                return
            else:
                print("[ERROR] You need at least 2 transistors to compare.")
                continue

        # Szukanie po nazwie (case insensitive)
        candidates = df[df['name'].str.contains(fragment, case=False, na=False)]['name'].tolist()

        if not candidates:
            print("[INFO] No transistors match that fragment.")
            continue

        print(f"\nFound {len(candidates)} matches:")
        for i, name in enumerate(candidates, 1):
            status = "[Already Selected]" if name in transistor_names else ""
            print(f"  [{i:>3}] {name} {status}")

        raw = input("\nEnter number(s) to add, separated by commas (or Enter to cancel this search): ").strip()
        if not raw:
            continue

        added_count = 0
        for part in raw.split(','):
            part = part.strip()
            if part.isdigit():
                idx = int(part)
                if 1 <= idx <= len(candidates):
                    selected_name = candidates[idx - 1]
                    if selected_name not in transistor_names:
                        transistor_names.append(selected_name)
                        added_count += 1

        if added_count > 0:
            print(f"[SUCCESS] Added {added_count} transistor(s) to comparison.")

    # --- Po uzbieraniu koszyka: Analiza plików ---
    all_charts = {}
    valid_names = []

    for t_name in transistor_names:
        match_df = df[df['name'] == t_name]
        if match_df.empty:
            print(f"[WARNING] Transistor '{t_name}' could not be found in active database. Skipping.")
            continue

        try:
            with open(match_df.iloc[0]['_original_file_path'], 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            # Extract charts; initialize a fresh dict for each transistor
            extracted = deep_search_charts(json_data, output_folder=None, name_path="", found_charts={})
            all_charts[t_name] = extracted
            valid_names.append(t_name)
        except Exception as e:
            print(f"[ERROR] Failed to read or parse file for '{t_name}': {e}")

    if len(all_charts) < 2:
        print("[ERROR] Not enough valid transistors found to perform comparison. Aborting.")
        return

    # Intersect chart keys across all selected transistors
    common_charts = None
    for t_name in valid_names:
        keys_set = set(all_charts[t_name].keys())
        if common_charts is None:
            common_charts = keys_set
        else:
            common_charts = common_charts.intersection(keys_set)

    common_charts = sorted(list(common_charts)) if common_charts else []

    if not common_charts:
        print("[INFO] No common chart data arrays found between ALL selected models.")
        return

    print("\nAvailable common charts for comparison:")
    for idx, c_key in enumerate(common_charts, 1):
        print(f"  [{idx}] {c_key}")

    print("\nYou can select MULTIPLE charts at once by separating numbers with a comma (e.g., 1,3,4)")
    choices_str = input(f"Select charts to export [1-{len(common_charts)}]: ").strip()

    selected_indices = []
    for part in choices_str.split(','):
        part = part.strip()
        if part.isdigit():
            idx = int(part)
            if 1 <= idx <= len(common_charts):
                selected_indices.append(idx)

    if not selected_indices:
        print("No valid choices selected. Aborting.")
        return

    output_dir = os.path.join(BASE_DIR, "Exported_Comparisons")
    os.makedirs(output_dir, exist_ok=True)

    print(f"\nProcessing {len(selected_indices)} selected chart(s)...")

    for idx in selected_indices:
        selected_chart_key = common_charts[idx - 1]
        clean_key = selected_chart_key.replace(' ', '_').replace('/', '_')

        devices_summary = f"{len(valid_names)}_devices"
        csv_filename = f"Comparison_{devices_summary}_{clean_key}.csv"
        csv_path = os.path.join(output_dir, csv_filename)

        combined_data = {}

        for t_name in valid_names:
            series_list = all_charts[t_name].get(selected_chart_key, [])

            for s_idx, s in enumerate(series_list):
                suffix = s['tj'] if s['tj'] else f"_series{s_idx + 1}"
                x_col = f"{t_name}{suffix}_X"
                y_col = f"{t_name}{suffix}_Y"
                combined_data[x_col] = s['data'][0]
                combined_data[y_col] = s['data'][1]

        # Standardize length using pandas index padding for side-by-side export
        df_comparison = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in combined_data.items()]))

        try:
            df_comparison.to_csv(csv_path, index=False, sep=';', encoding='utf-8-sig')
            print(f"  [SUCCESS] Saved: {csv_filename}")
        except Exception as e:
            print(f"  [ERROR] Failed to save {csv_filename}: {e}")

    print(f"\nAll operations done! Target folder: {os.path.abspath(output_dir)}")


# ---------------------------------------------------------------------------
# PLOTTING
# ---------------------------------------------------------------------------

def _get_plot_colors():
    """Return a list of distinct colors for multi-curve plots."""
    return ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e',
            '#9467bd', '#8c564b', '#e377c2', '#17becf',
            '#bcbd22', '#7f7f7f']


def plot_transistor(json_path: str) -> None:
    """
    Plot all available characteristics for a transistor JSON file,
    mirroring the chart set from the reference transistordatabase library:

      1. Switch Channel I-V  (graph_v_i, grouped by v_g or t_j)
      2. Switch E_on/E_off   vs Current  (graph_i_e)
      3. Switch E_on/E_off   vs Gate Resistor (graph_r_e)
      4. Switch E_on/E_off   vs Temperature   (graph_t_e)
      5. Switch On-resistance vs Temperature  (r_channel_th)
      6. Switch Gate Charge   (charge_curve)
      7. Switch SOA
      8. Diode Channel I-V
      9. Diode E_rr          vs Current  (graph_i_e)
     10. Diode E_rr          vs Gate Resistor (graph_r_e)
     11. Diode SOA
     12. C_iss / C_oss / C_rss vs Voltage
     13. V_E_oss  (graph_v_ecoss)
     14. Thermal Foster: Rth(t) transient – switch & diode

    Each chart type opens in its own figure window.
    Windows that have no data are silently skipped.

    :param json_path: Path to the transistor JSON file.
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('TkAgg' if 'TkAgg' in matplotlib.rcsetup.all_backends else 'Agg')
    except ImportError:
        print("[ERROR] matplotlib is not installed. Run: pip install matplotlib")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception as e:
        print(f"[ERROR] Cannot read JSON file: {e}")
        return

    name = d.get("name", "Unknown")
    sw   = d.get("switch", {})
    di   = d.get("diode",  {})
    colors = _get_plot_colors()
    plots_shown = 0

    # ------------------------------------------------------------------
    # Helper: safe list check
    # ------------------------------------------------------------------
    def _valid_list(obj):
        return isinstance(obj, list) and len(obj) > 0

    def _valid_curve(lst, key):
        """Return entries from lst that have a non-empty list at lst[key]."""
        return [e for e in lst
                if isinstance(e, dict)
                and _valid_list(e.get(key))
                and len(e[key]) == 2
                and _valid_list(e[key][0])]

    # ------------------------------------------------------------------
    # 1. Switch Channel I-V
    # ------------------------------------------------------------------
    sw_ch = [c for c in sw.get("channel", [])
             if isinstance(c, dict) and _valid_list(c.get("graph_v_i"))
             and len(c["graph_v_i"]) == 2 and _valid_list(c["graph_v_i"][0])]

    if sw_ch:
        # Group: if many curves per v_g -> plot by t_j per v_g;
        #        if many curves per t_j -> plot by v_g per t_j  (same logic as reference)
        by_tj  = {}
        by_vg  = {}
        for c in sw_ch:
            by_tj.setdefault(c.get("t_j"), []).append(c)
            by_vg.setdefault(c.get("v_g"), []).append(c)

        multi_per_tj = any(len(v) > 1 for v in by_tj.values())
        multi_per_vg = any(len(v) > 1 for v in by_vg.values())

        if multi_per_tj:
            # One figure per t_j, curves labelled by v_g
            for tj, curves in sorted(by_tj.items()):
                if len(curves) <= 1:
                    continue
                fig, ax = plt.subplots()
                for i, c in enumerate(curves):
                    ax.plot(c["graph_v_i"][0], c["graph_v_i"][1],
                            color=colors[i % len(colors)],
                            label=f"$V_g$ = {c.get('v_g')} V")
                ax.set_title(f"{name} – Switch Channel  ($T_j$ = {tj} °C)")
                ax.set_xlabel("Voltage in V")
                ax.set_ylabel("Current in A")
                ax.legend(fontsize=8)
                ax.grid(True)
                plt.tight_layout()
                plots_shown += 1

        if multi_per_vg:
            # One figure per v_g, curves labelled by t_j
            for vg, curves in sorted(by_vg.items(), key=lambda x: (x[0] is None, x[0])):
                if len(curves) <= 1 and multi_per_tj:
                    continue
                fig, ax = plt.subplots()
                for i, c in enumerate(curves):
                    ax.plot(c["graph_v_i"][0], c["graph_v_i"][1],
                            color=colors[i % len(colors)],
                            label=f"$T_j$ = {c.get('t_j')} °C")
                ax.set_title(f"{name} – Switch Channel  ($V_g$ = {vg} V)")
                ax.set_xlabel("Voltage in V")
                ax.set_ylabel("Current in A")
                ax.legend(fontsize=8)
                ax.grid(True)
                plt.tight_layout()
                plots_shown += 1

        if not multi_per_tj and not multi_per_vg:
            # Few curves – all on one figure
            fig, ax = plt.subplots()
            for i, c in enumerate(sw_ch):
                ax.plot(c["graph_v_i"][0], c["graph_v_i"][1],
                        color=colors[i % len(colors)],
                        label=f"$V_g$ = {c.get('v_g')} V,  $T_j$ = {c.get('t_j')} °C")
            ax.set_title(f"{name} – Switch Channel I-V")
            ax.set_xlabel("Voltage in V")
            ax.set_ylabel("Current in A")
            ax.legend(fontsize=8)
            ax.grid(True)
            plt.tight_layout()
            plots_shown += 1

    # ------------------------------------------------------------------
    # 2. Switch E_on / E_off  vs  Current  (graph_i_e)
    # ------------------------------------------------------------------
    eon_ie  = _valid_curve(sw.get("e_on",  []), "graph_i_e")
    eoff_ie = _valid_curve(sw.get("e_off", []), "graph_i_e")

    if eon_ie or eoff_ie:
        fig, ax = plt.subplots()
        for i, e in enumerate(eon_ie):
            lbl = (f"$E_{{on}}$: $V_{{supply}}$={e.get('v_supply')} V, "
                   f"$V_g$={e.get('v_g')} V, $T_j$={e.get('t_j')} °C, "
                   f"$R_g$={e.get('r_g')} Ω")
            ax.plot(e["graph_i_e"][0], e["graph_i_e"][1],
                    color=colors[i % len(colors)], label=lbl)
        for i, e in enumerate(eoff_ie):
            lbl = (f"$E_{{off}}$: $V_{{supply}}$={e.get('v_supply')} V, "
                   f"$V_g$={e.get('v_g')} V, $T_j$={e.get('t_j')} °C, "
                   f"$R_g$={e.get('r_g')} Ω")
            ax.plot(e["graph_i_e"][0], e["graph_i_e"][1],
                    color=colors[(i + len(eon_ie)) % len(colors)],
                    linestyle='--', label=lbl)
        ax.set_title(f"{name} – Switch Switching Losses vs Current")
        ax.set_xlabel("Current in A")
        ax.set_ylabel("Loss energy in J")
        ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.legend(fontsize=6)
        ax.grid(True)
        plt.tight_layout()
        plots_shown += 1

    # ------------------------------------------------------------------
    # 3. Switch E_on / E_off  vs  Gate Resistor  (graph_r_e)
    # ------------------------------------------------------------------
    eon_re  = _valid_curve(sw.get("e_on",  []), "graph_r_e")
    eoff_re = _valid_curve(sw.get("e_off", []), "graph_r_e")

    if eon_re or eoff_re:
        fig, ax = plt.subplots()
        for i, e in enumerate(eon_re):
            lbl = (f"$E_{{on}}$: $V_{{supply}}$={e.get('v_supply')} V, "
                   f"$V_g$={e.get('v_g')} V, $T_j$={e.get('t_j')} °C, "
                   f"$I_{{ch}}$={e.get('i_x')} A")
            ax.plot(e["graph_r_e"][0], e["graph_r_e"][1],
                    color=colors[i % len(colors)], label=lbl)
        for i, e in enumerate(eoff_re):
            lbl = (f"$E_{{off}}$: $V_{{supply}}$={e.get('v_supply')} V, "
                   f"$V_g$={e.get('v_g')} V, $T_j$={e.get('t_j')} °C, "
                   f"$I_{{ch}}$={e.get('i_x')} A")
            ax.plot(e["graph_r_e"][0], e["graph_r_e"][1],
                    color=colors[(i + len(eon_re)) % len(colors)],
                    linestyle='--', label=lbl)
        ax.set_title(f"{name} – Switch Switching Losses vs Gate Resistor")
        ax.set_xlabel("External Gate Resistor in Ω")
        ax.set_ylabel("Loss energy in J")
        ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.legend(fontsize=6)
        ax.grid(True)
        plt.tight_layout()
        plots_shown += 1

    # ------------------------------------------------------------------
    # 4. Switch E_on / E_off  vs  Temperature  (graph_t_e)
    # ------------------------------------------------------------------
    eon_te  = _valid_curve(sw.get("e_on",  []), "graph_t_e")
    eoff_te = _valid_curve(sw.get("e_off", []), "graph_t_e")

    if eon_te or eoff_te:
        fig, ax = plt.subplots()
        for i, e in enumerate(eon_te):
            lbl = (f"$E_{{on}}$: $V_{{supply}}$={e.get('v_supply')} V, "
                   f"$V_g$={e.get('v_g')} V, $R_g$={e.get('r_g')} Ω, "
                   f"$I_{{ch}}$={e.get('i_x')} A")
            ax.plot(e["graph_t_e"][0], e["graph_t_e"][1],
                    color=colors[i % len(colors)], label=lbl)
        for i, e in enumerate(eoff_te):
            lbl = (f"$E_{{off}}$: $V_{{supply}}$={e.get('v_supply')} V, "
                   f"$V_g$={e.get('v_g')} V, $R_g$={e.get('r_g')} Ω, "
                   f"$I_{{ch}}$={e.get('i_x')} A")
            ax.plot(e["graph_t_e"][0], e["graph_t_e"][1],
                    color=colors[(i + len(eon_te)) % len(colors)],
                    linestyle='--', label=lbl)
        ax.set_title(f"{name} – Switch Switching Losses vs Junction Temperature")
        ax.set_xlabel("Junction Temperature in °C")
        ax.set_ylabel("Loss energy in J")
        ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.legend(fontsize=6)
        ax.grid(True)
        plt.tight_layout()
        plots_shown += 1

    # ------------------------------------------------------------------
    # 5. Switch On-resistance vs Temperature  (r_channel_th)
    # ------------------------------------------------------------------
    r_th_list = [e for e in sw.get("r_channel_th", [])
                 if isinstance(e, dict)]
    # dataset_type = 't_r': graph axes are [T_j, R_on]
    # dataset_type = 't_r_norm': same but normalised
    tr_curves = [e for e in r_th_list
                 if e.get("dataset_type") in ("t_r", "t_r_norm")
                 and _valid_list(e.get("graph_t_r"))
                 and len(e["graph_t_r"]) == 2]
    if tr_curves:
        fig, ax = plt.subplots()
        ylabel = ("On-resistance (normalised)" if tr_curves[0].get("dataset_type") == "t_r_norm"
                  else "On-resistance in Ω")
        for i, e in enumerate(tr_curves):
            lbl = (f"$V_g$={e.get('v_g')} V,  $I_{{ch}}$={e.get('i_channel')} A")
            ax.plot(e["graph_t_r"][0], e["graph_t_r"][1],
                    color=colors[i % len(colors)], label=lbl)
        ax.set_title(f"{name} – Switch On-resistance vs Temperature")
        ax.set_xlabel("Junction Temperature in °C")
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=8)
        ax.grid(True)
        plt.tight_layout()
        plots_shown += 1

    # ------------------------------------------------------------------
    # 6. Switch Gate Charge  (charge_curve)
    # ------------------------------------------------------------------
    qg_curves = [e for e in sw.get("charge_curve", [])
                 if isinstance(e, dict)
                 and _valid_list(e.get("graph_q_v"))
                 and len(e["graph_q_v"]) == 2]
    if qg_curves:
        fig, ax = plt.subplots()
        for i, e in enumerate(qg_curves):
            lbl = (f"$I_{{ch}}$={e.get('i_channel')} A, "
                   f"$V_{{supply}}$={e.get('v_supply')} V, "
                   f"$T_j$={e.get('t_j')} °C")
            ax.plot(e["graph_q_v"][0], e["graph_q_v"][1],
                    color=colors[i % len(colors)], label=lbl)
        ax.set_title(f"{name} – Switch Gate Charge")
        ax.set_xlabel("Gate Charge $Q_G$ in nC")
        ax.set_ylabel("Gate-source Voltage $V_{gs}$ in V")
        ax.legend(fontsize=8)
        ax.grid(True)
        plt.tight_layout()
        plots_shown += 1

    # ------------------------------------------------------------------
    # 7. Switch SOA
    # ------------------------------------------------------------------
    sw_soa = [e for e in sw.get("soa", [])
              if isinstance(e, dict)
              and _valid_list(e.get("graph_i_v"))
              and len(e["graph_i_v"]) == 2]
    if sw_soa:
        fig, ax = plt.subplots()
        for i, e in enumerate(sw_soa):
            lbl = f"$T_c$ = {e.get('t_c')} °C"
            ax.loglog(e["graph_i_v"][0], e["graph_i_v"][1],
                      color=colors[i % len(colors)], label=lbl)
        ax.set_title(f"{name} – Switch Safe Operating Area")
        ax.set_xlabel("$V_{ds}$ / $V_{ce}$ in V")
        ax.set_ylabel("$I_d$ / $I_c$ in A")
        ax.legend(fontsize=8)
        ax.grid(True, which='both')
        plt.tight_layout()
        plots_shown += 1

    # ------------------------------------------------------------------
    # 8. Diode Channel I-V
    # ------------------------------------------------------------------
    di_ch = [c for c in di.get("channel", [])
             if isinstance(c, dict) and _valid_list(c.get("graph_v_i"))
             and len(c["graph_v_i"]) == 2 and _valid_list(c["graph_v_i"][0])]

    if di_ch:
        by_tj_d = {}
        by_vg_d = {}
        for c in di_ch:
            by_tj_d.setdefault(c.get("t_j"), []).append(c)
            by_vg_d.setdefault(c.get("v_g"), []).append(c)

        multi_per_tj_d = any(len(v) > 1 for v in by_tj_d.values())

        if multi_per_tj_d:
            for tj, curves in sorted(by_tj_d.items()):
                if len(curves) <= 1:
                    continue
                fig, ax = plt.subplots()
                for i, c in enumerate(curves):
                    ax.plot(c["graph_v_i"][0], c["graph_v_i"][1],
                            color=colors[i % len(colors)],
                            label=f"$V_g$ = {c.get('v_g')} V")
                ax.set_title(f"{name} – Diode Channel  ($T_j$ = {tj} °C)")
                ax.set_xlabel("Voltage in V")
                ax.set_ylabel("Current in A")
                ax.legend(fontsize=8)
                ax.grid(True)
                plt.tight_layout()
                plots_shown += 1
        else:
            fig, ax = plt.subplots()
            for i, c in enumerate(di_ch):
                ax.plot(c["graph_v_i"][0], c["graph_v_i"][1],
                        color=colors[i % len(colors)],
                        label=f"$T_j$ = {c.get('t_j')} °C")
            ax.set_title(f"{name} – Diode Channel I-V")
            ax.set_xlabel("Voltage in V")
            ax.set_ylabel("Current in A")
            ax.legend(fontsize=8)
            ax.grid(True)
            plt.tight_layout()
            plots_shown += 1

    # ------------------------------------------------------------------
    # 9. Diode E_rr  vs  Current  (graph_i_e)
    # ------------------------------------------------------------------
    err_ie = _valid_curve(di.get("e_rr", []), "graph_i_e")
    if err_ie:
        fig, ax = plt.subplots()
        for i, e in enumerate(err_ie):
            lbl = (f"$E_{{rr}}$: $V_{{supply}}$={e.get('v_supply')} V, "
                   f"$T_j$={e.get('t_j')} °C, $R_g$={e.get('r_g')} Ω")
            if isinstance(e.get("v_g"), (int, float)):
                lbl += f", $V_g$={e['v_g']} V"
            ax.plot(e["graph_i_e"][0], e["graph_i_e"][1],
                    color=colors[i % len(colors)], label=lbl)
        ax.set_title(f"{name} – Diode Reverse Recovery Energy vs Current")
        ax.set_xlabel("Current in A")
        ax.set_ylabel("Loss energy in J")
        ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.legend(fontsize=6)
        ax.grid(True)
        plt.tight_layout()
        plots_shown += 1

    # ------------------------------------------------------------------
    # 10. Diode E_rr  vs  Gate Resistor  (graph_r_e)
    # ------------------------------------------------------------------
    err_re = _valid_curve(di.get("e_rr", []), "graph_r_e")
    if err_re:
        fig, ax = plt.subplots()
        for i, e in enumerate(err_re):
            lbl = (f"$E_{{rr}}$: $V_{{supply}}$={e.get('v_supply')} V, "
                   f"$T_j$={e.get('t_j')} °C, $I_{{ch}}$={e.get('i_x')} A")
            if isinstance(e.get("v_g"), (int, float)):
                lbl += f", $V_g$={e['v_g']} V"
            ax.plot(e["graph_r_e"][0], e["graph_r_e"][1],
                    color=colors[i % len(colors)], label=lbl)
        ax.set_title(f"{name} – Diode Reverse Recovery Energy vs Gate Resistor")
        ax.set_xlabel("External Gate Resistor in Ω")
        ax.set_ylabel("Loss energy in J")
        ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.legend(fontsize=6)
        ax.grid(True)
        plt.tight_layout()
        plots_shown += 1

    # ------------------------------------------------------------------
    # 11. Diode SOA
    # ------------------------------------------------------------------
    di_soa = [e for e in di.get("soa", [])
              if isinstance(e, dict)
              and _valid_list(e.get("graph_i_v"))
              and len(e["graph_i_v"]) == 2]
    if di_soa:
        fig, ax = plt.subplots()
        for i, e in enumerate(di_soa):
            ax.loglog(e["graph_i_v"][0], e["graph_i_v"][1],
                      color=colors[i % len(colors)],
                      label=f"$T_c$ = {e.get('t_c')} °C")
        ax.set_title(f"{name} – Diode Safe Operating Area")
        ax.set_xlabel("$V_r$ in V")
        ax.set_ylabel("$I_r$ in A")
        ax.legend(fontsize=8)
        ax.grid(True, which='both')
        plt.tight_layout()
        plots_shown += 1

    # ------------------------------------------------------------------
    # 12. C_iss / C_oss / C_rss  vs  Voltage
    # ------------------------------------------------------------------
    cap_curves = {}
    for cap_key, label in [("c_iss", "$C_{iss}$"), ("c_oss", "$C_{oss}$"), ("c_rss", "$C_{rss}$")]:
        entries = d.get(cap_key)
        if not _valid_list(entries):
            continue
        for entry in entries:
            if isinstance(entry, dict) and _valid_list(entry.get("graph_v_c")) and len(entry["graph_v_c"]) == 2:
                cap_curves.setdefault(cap_key, []).append((label, entry["graph_v_c"]))

    if cap_curves:
        fig, ax = plt.subplots()
        ci = 0
        for cap_key, pairs in cap_curves.items():
            for label, gvc in pairs:
                ax.semilogy(gvc[0], gvc[1], color=colors[ci % len(colors)], label=label)
                ci += 1
        ax.set_title(f"{name} – Parasitic Capacitances vs Voltage")
        ax.set_xlabel("Voltage in V")
        ax.set_ylabel("Capacitance in F")
        ax.legend(fontsize=8)
        ax.grid(True, which='both')
        plt.tight_layout()
        plots_shown += 1

    # ------------------------------------------------------------------
    # 13. V_E_oss  (graph_v_ecoss)
    # ------------------------------------------------------------------
    ecoss = d.get("graph_v_ecoss")
    if _valid_list(ecoss) and len(ecoss) == 2 and _valid_list(ecoss[0]):
        fig, ax = plt.subplots()
        ax.plot(ecoss[0], ecoss[1], color=colors[0])
        ax.set_title(f"{name} – Energy stored in $C_{{oss}}$ vs $V_{{DS}}$")
        ax.set_xlabel("Voltage in V")
        ax.set_ylabel("Energy in J")
        ax.grid(True)
        plt.tight_layout()
        plots_shown += 1

    # ------------------------------------------------------------------
    # 14. Thermal Foster transient  Rth(t)  – switch & diode
    # ------------------------------------------------------------------
    for component, tf in [("Switch", sw.get("thermal_foster", {})),
                           ("Diode",  di.get("thermal_foster",  {}))]:
        if not isinstance(tf, dict):
            continue
        gtr = tf.get("graph_t_rthjc")
        if _valid_list(gtr) and len(gtr) == 2 and _valid_list(gtr[0]):
            fig, ax = plt.subplots()
            ax.semilogx(gtr[0], gtr[1],
                        color=colors[0] if component == "Switch" else colors[1])
            ax.set_title(f"{name} – {component} Thermal Impedance $Z_{{th,jc}}(t)$")
            ax.set_xlabel("Time in s")
            ax.set_ylabel("$R_{{th}}$ in K/W")
            ax.grid(True, which='both')
            plt.tight_layout()
            plots_shown += 1

    # ------------------------------------------------------------------
    # Final
    # ------------------------------------------------------------------
    if plots_shown == 0:
        print(f"[INFO] No plottable data found for '{name}'.")
        return

    print(f"[INFO] Opened {plots_shown} plot window(s) for '{name}'.")
    try:
        import matplotlib.pyplot as plt
        plt.show()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# PLECS XML EXPORT
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# PLECS XML EXPORT
# ---------------------------------------------------------------------------

PLECS_NS = "http://www.plexim.com/xml/semiconductors/"
PLECS_VERSION = "1.1"


def _fmt_floats(values: list) -> str:
    """Format a list of floats as space-separated string for PLECS XML."""
    return " ".join(f"{v:.6g}" for v in values)


def _build_plecs_package(root: ET.Element, data: dict) -> None:
    """Populate a <Package> element – section order matches reference:
    TurnOnLoss → TurnOffLoss → ConductionLoss → ThermalModel → Comment."""

    pkg = ET.SubElement(root, "Package",
                        attrib={"class": data["class"],
                                "vendor": data["vendor"],
                                "partnumber": data["partnumber"]})
    ET.SubElement(pkg, "Variables")

    semi = ET.SubElement(pkg, "SemiconductorData", attrib={"type": data["class"]})

    # ---- TurnOnLoss / TurnOffLoss (before ConductionLoss, matching reference) ----
    for loss_key in ("TurnOnLoss", "TurnOffLoss"):
        loss_data = data[loss_key]
        scale = loss_data.get("energy_scale", "0.001")
        loss_el = ET.SubElement(semi, loss_key)
        ET.SubElement(loss_el, "ComputationMethod").text = "Table only"
        ET.SubElement(loss_el, "CurrentAxis").text = _fmt_floats(loss_data["current_axis"])
        ET.SubElement(loss_el, "VoltageAxis").text = _fmt_floats(loss_data["voltage_axis"])
        ET.SubElement(loss_el, "TemperatureAxis").text = _fmt_floats(loss_data["temp_axis"])
        energy_el = ET.SubElement(loss_el, "Energy", attrib={"scale": scale})
        for t_idx in range(len(loss_data["temp_axis"])):
            temp_el = ET.SubElement(energy_el, "Temperature")
            for v_idx in range(len(loss_data["voltage_axis"])):
                row = loss_data["energy_table"][t_idx][v_idx]
                if scale == "0.001":
                    ET.SubElement(temp_el, "Voltage").text = _fmt_floats([x * 1000 for x in row])
                else:
                    ET.SubElement(temp_el, "Voltage").text = _fmt_floats(row)

    # ---- ConductionLoss ----
    cond = ET.SubElement(semi, "ConductionLoss")
    ET.SubElement(cond, "ComputationMethod").text = "Table only"
    ET.SubElement(cond, "CurrentAxis").text = _fmt_floats(data["cond"]["current_axis"])
    ET.SubElement(cond, "TemperatureAxis").text = _fmt_floats(data["cond"]["temp_axis"])
    vdrop = ET.SubElement(cond, "VoltageDrop", attrib={"scale": "1"})
    for curve in data["cond"]["curves"]:
        ET.SubElement(vdrop, "Temperature").text = _fmt_floats(curve)

    # ---- ThermalModel (Foster) ----
    thermal = ET.SubElement(pkg, "ThermalModel")
    branch = ET.SubElement(thermal, "Branch", attrib={"type": "Foster"})
    for r, tau in zip(data["foster"]["r_vec"], data["foster"]["tau_vec"]):
        ET.SubElement(branch, "RTauElement",
                      attrib={"R": f"{r:.6g}", "Tau": f"{tau:.6g}" if tau is not None else "0"})

    # ---- Comment ----
    comment_el = ET.SubElement(pkg, "Comment")
    for line in data.get("comment_lines", []):
        ET.SubElement(comment_el, "Line").text = line


def _prepare_conduction_data(channel_list: list, is_mosfet: bool = False) -> dict | None:
    """
    Direct port of get_channel_data() from transistordatabase/helper_functions.py.

    Interpolates channel I-V to 20 equally-spaced points from 0 to limit_current.
    For MOSFETs applies negate_and_append to generate third-quadrant body-diode curve.

    graph_v_i: row0 = V [V], row1 = I [A]
    """
    import numpy as np

    valid = [ch for ch in channel_list
             if isinstance(ch.get("graph_v_i"), list) and len(ch["graph_v_i"]) == 2
             and len(ch["graph_v_i"][0]) > 0]
    if not valid:
        return None

    # limit_current = min of max(|I|) across all curves (matches reference)
    limit_current = None
    for ch in valid:
        i_max = max(abs(i) for i in ch["graph_v_i"][1])
        if limit_current is None or i_max < limit_current:
            limit_current = i_max
    if not limit_current:
        return None

    interp_current = np.linspace(0, limit_current, 20).tolist()
    temp_axis = []
    curves = []
    seen_tj = set()

    for ch in valid:
        tj = ch["t_j"]
        if tj in seen_tj:
            continue
        seen_tj.add(tj)
        i_pts = [abs(i) for i in ch["graph_v_i"][1]]
        v_pts = [abs(v) for v in ch["graph_v_i"][0]]
        paired = sorted(zip(i_pts, v_pts))
        i_sorted = [p[0] for p in paired]
        v_sorted = [p[1] for p in paired]
        interp_v = np.interp(interp_current, i_sorted, v_sorted).tolist()
        temp_axis.append(tj)
        curves.append(interp_v)

    if not curves:
        return None

    # negate_and_append for MOSFETs – port of helper_functions.negate_and_append
    if is_mosfet:
        cur_arr = np.array(interp_current)
        cur_nonzero = cur_arr[cur_arr != 0]
        cur_neg = (-np.flip(cur_nonzero)).tolist()
        mirrored_current = cur_neg + interp_current

        mirrored_curves = []
        for curve in curves:
            v_arr = np.array(curve)
            v_nonzero = v_arr[v_arr != 0]
            v_neg = (-np.flip(v_nonzero)).tolist()
            mirrored_curves.append(v_neg + curve)

        return {"current_axis": mirrored_current, "temp_axis": temp_axis, "curves": mirrored_curves}

    return {"current_axis": interp_current, "temp_axis": temp_axis, "curves": curves}


def _prepare_loss_data(energy_list: list) -> dict | None:
    """
    Direct port of get_loss_curves() from transistordatabase/helper_functions.py.

    Selects graph_i_e curves, interpolates to 20 equally-spaced current points
    from 0 to limit_current (= min of all curve maxima, matching reference).
    VoltageAxis always starts with -10 and 0 (zero-energy rows), then data voltages.
    Energy values are stored internally in J and exported to PLECS as mJ
    (Energy scale=\"0.001\").
    """
    import numpy as np

    valid = [e for e in energy_list
             if e.get("dataset_type") == "graph_i_e"
             and isinstance(e.get("graph_i_e"), list)
             and len(e["graph_i_e"]) == 2
             and len(e["graph_i_e"][0]) > 0]
    if not valid:
        return None

    # limit_current = min of max(I) across all curves (matches reference)
    limit_current = None
    for e in valid:
        i_max = max(e["graph_i_e"][0])
        if limit_current is None or i_max < limit_current:
            limit_current = i_max
    if not limit_current:
        return None

    interp_current = np.linspace(0, limit_current, 20).tolist()

    # Build energy table grouped by v_supply, then t_j
    # Reference uses dict keyed by v_supply: {v_supply: [[E per current] per t_j]}
    energy_by_vsupply = {}
    temp_axis = []

    for e in valid:
        vs = e.get("v_supply", 0)
        tj = e["t_j"]
        i_pts = e["graph_i_e"][0]
        e_pts = e["graph_i_e"][1]
        loss_energy = np.interp(interp_current, i_pts, e_pts).tolist()

        if vs not in energy_by_vsupply:
            energy_by_vsupply[vs] = []
        energy_by_vsupply[vs].append(loss_energy)
        if tj not in temp_axis:
            temp_axis.append(tj)

    # Sort voltage axis; prepend -10 and 0 with zero rows (matches reference)
    data_voltages = sorted(energy_by_vsupply.keys())
    n_tj = len(temp_axis)
    zero_row = [[0.0] * 20] * n_tj

    voltage_axis = [-10, 0] + data_voltages
    energy_table = []
    # energy_table[t_idx][v_idx] indexed as per _build_plecs_package
    for t_idx in range(n_tj):
        row = []
        row.append([0.0] * 20)          # V = -10
        row.append([0.0] * 20)          # V = 0
        for vs in data_voltages:
            e_rows = energy_by_vsupply[vs]
            row.append(e_rows[t_idx] if t_idx < len(e_rows) else [0.0] * 20)
        energy_table.append(row)

    return {
        "current_axis": interp_current,
        "voltage_axis": voltage_axis,
        "temp_axis": sorted(temp_axis),
        "energy_table": energy_table,
        "energy_scale": "0.001",   # XML values are written in mJ
    }


def _prepare_foster(foster_dict: dict) -> dict | None:
    """Extract Foster RC vectors. Returns None if data is missing."""
    r_vec = foster_dict.get("r_th_vector")
    tau_vec = foster_dict.get("tau_vector")
    if not r_vec or not tau_vec:
        # fall back to scalar total
        r_total = foster_dict.get("r_th_total")
        tau_total = foster_dict.get("tau_total")
        if r_total is not None and tau_total is not None:
            return {"r_vec": [r_total], "tau_vec": [tau_total]}
        return None
    return {"r_vec": list(r_vec), "tau_vec": list(tau_vec)}


def _indent_xml(elem: ET.Element, level: int = 0) -> None:
    """Add pretty-print indentation to an ElementTree in-place."""
    indent = "\n" + "    " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "    "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            _indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent


def export_plecs_xml(json_path: str, output_dir: str = ".") -> bool:
    """
    Export a transistor JSON file as PLECS-compatible XML files.

    Produces two files:
        <name>_switch.xml  –  switch (IGBT/MOSFET/SiC-MOSFET/GaN) characteristics
        <name>_diode.xml   –  body/anti-parallel diode characteristics

    Requires switch.channel and diode.channel to be non-empty.
    switch.e_on / e_off and diode.e_rr are included when available;
    if absent, zero-filled loss tables are generated so PLECS can still load the file.

    :param json_path: Path to the transistor JSON file.
    :param output_dir: Directory where XML files will be saved.
    :return: True on success, False on failure.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception as e:
        print(f"[ERROR] Cannot read JSON file: {e}")
        return False

    name         = d.get("name", "Unknown")
    manufacturer = d.get("manufacturer", "Unknown")
    t_type       = d.get("type", "IGBT")
    v_abs_max    = d.get("v_abs_max", 1200)
    try:
        v_abs_max = float(v_abs_max)
    except (TypeError, ValueError):
        v_abs_max = 1200.0

    plecs_class_map = {
        "IGBT": "IGBT", "SiC-MOSFET": "MOSFET",
        "Si-MOSFET": "MOSFET", "GaN-Transistor": "MOSFET",
        "MOSFET": "MOSFET"
    }
    switch_class = plecs_class_map.get(t_type, "IGBT")
    is_mosfet    = (switch_class == "MOSFET")

    sw = d.get("switch", {})
    di = d.get("diode",  {})

    # ---- Switch: ConductionLoss (pass is_mosfet for negate_and_append) ----
    sw_cond = _prepare_conduction_data(sw.get("channel", []), is_mosfet=is_mosfet)
    if sw_cond is None:
        print(f"[ERROR] '{name}': switch.channel has no usable graph_v_i data. Cannot export.")
        return False

    # ---- Zero-energy fallback matching reference: VoltageAxis = [-10, 0, v_abs_max] ----
    def _zero_loss(cond):
        n = len(cond["current_axis"])
        return {
            "current_axis": cond["current_axis"],
            "voltage_axis": [-10, 0, v_abs_max],
            "temp_axis":    cond["temp_axis"],
            "energy_scale": "0.001",
            "energy_table": [
                [[0.0]*n, [0.0]*n, [0.0]*n]
                for _ in cond["temp_axis"]
            ],
        }

    # ---- Switch: TurnOnLoss / TurnOffLoss ----
    sw_on  = _prepare_loss_data(sw.get("e_on",  []))
    sw_off = _prepare_loss_data(sw.get("e_off", []))
    if sw_on is None:
        print(f"[INFO] '{name}': no switch e_on data – zero table will be used.")
        sw_on = _zero_loss(sw_cond)
    if sw_off is None:
        print(f"[INFO] '{name}': no switch e_off data – zero table will be used.")
        sw_off = _zero_loss(sw_cond)

    # ---- Switch: ThermalModel ----
    sw_foster = _prepare_foster(sw.get("thermal_foster", {}))
    if sw_foster is None:
        print(f"[INFO] '{name}': no switch Foster data – single R=0/Tau=0 element used.")
        sw_foster = {"r_vec": [0.0], "tau_vec": [0.0]}

    # ---- Diode: ConductionLoss (diode is not a MOSFET – no mirroring) ----
    di_cond = _prepare_conduction_data(di.get("channel", []), is_mosfet=False)
    if di_cond is None:
        print(f"[WARNING] '{name}': diode.channel has no usable data. Diode XML will be skipped.")

    # ---- Diode: TurnOffLoss (e_rr) and TurnOnLoss (always zero per reference) ----
    di_off = _prepare_loss_data(di.get("e_rr", []))

    # ---- Comment matching reference style ----
    import datetime as _dt
    comment_lines = [
        f"This datasheet was created by {d.get('author', 'unknown')} on "
        f"{d.get('datasheet_date', '')} and was exported using transistordatabase.",
        f"Datasheet Link : {d.get('datasheet_hyperlink', '')}",
        f"File generated : {_dt.datetime.now()}",
        "File generated by : szukaj.py",
    ]

    os.makedirs(output_dir, exist_ok=True)

    # ---- Write switch XML ----
    switch_data = {
        "class":         switch_class,
        "vendor":        manufacturer,
        "partnumber":    name,
        "cond":          sw_cond,
        "TurnOnLoss":    sw_on,
        "TurnOffLoss":   sw_off,
        "foster":        sw_foster,
        "comment_lines": comment_lines,
    }

    sw_root = ET.Element("SemiconductorLibrary",
                         attrib={"xmlns": PLECS_NS, "version": PLECS_VERSION})
    ET.register_namespace("", PLECS_NS)
    _build_plecs_package(sw_root, switch_data)
    _indent_xml(sw_root)

    sw_path = os.path.join(output_dir, f"{name}_switch.xml")
    with open(sw_path, "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fh.write(ET.tostring(sw_root, encoding="unicode"))
    print(f"  [SUCCESS] Switch XML: {os.path.normpath(sw_path)}")

    # ---- Write diode XML ----
    if di_cond is not None:
        di_foster = _prepare_foster(di.get("thermal_foster", {}))
        if di_foster is None:
            di_foster = {"r_vec": [0.0], "tau_vec": [0.0]}

        di_on_zero = _zero_loss(di_cond)
        if di_off is None:
            di_off = _zero_loss(di_cond)

        diode_data = {
            "class":         "Diode",
            "vendor":        manufacturer,
            "partnumber":    name,
            "cond":          di_cond,
            "TurnOnLoss":    di_on_zero,
            "TurnOffLoss":   di_off,
            "foster":        di_foster,
            "comment_lines": comment_lines,
        }
        di_root = ET.Element("SemiconductorLibrary",
                             attrib={"xmlns": PLECS_NS, "version": PLECS_VERSION})
        ET.register_namespace("", PLECS_NS)
        _build_plecs_package(di_root, diode_data)
        _indent_xml(di_root)

        di_path = os.path.join(output_dir, f"{name}_diode.xml")
        with open(di_path, "w", encoding="utf-8") as fh:
            fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            fh.write(ET.tostring(di_root, encoding="unicode"))
        print(f"  [SUCCESS] Diode XML:  {os.path.normpath(di_path)}")
    else:
        print(f"  [SKIPPED] Diode XML (no diode channel data).")

    return True


# ---------------------------------------------------------------------------
# PLECS XML IMPORT
# ---------------------------------------------------------------------------

def import_plecs_xml() -> bool:
    """
    Import a pair of PLECS-format XML files (switch + diode) and save as a
    transistor JSON file in the appropriate category folder.

    The function reads ConductionLoss, TurnOnLoss, TurnOffLoss and
    ThermalModel (Foster only) sections.  Fields that PLECS XML does not
    carry (v_abs_max, housing_type, etc.) are left blank so the user can
    fill them with the 'edit' command afterwards.

    :return: True if a JSON file was written successfully, False otherwise.
    """
    PLECS_NS_URI = "http://www.plexim.com/xml/semiconductors/"
    ns = {"p": PLECS_NS_URI}

    print("\n--- Import PLECS XML files ---")
    sw_path = input("Path to switch XML file: ").strip().strip("'\"")
    di_path = input("Path to diode XML file (Enter to skip): ").strip().strip("'\"")

    def _parse_xml_file(path: str) -> tuple:
        """Parse one PLECS XML file.  Returns (info_dict, channel_list, e_on_list, e_off_list, foster_dict)."""
        if not os.path.isfile(path):
            raise FileNotFoundError(f"File not found: {path}")

        tree = ET.parse(path)
        root = tree.getroot()
        pkg = root.find("p:Package", ns)
        if pkg is None:
            raise ValueError("No <Package> element found – not a valid PLECS XML file.")

        info = {
            "class":       pkg.attrib.get("class", "IGBT"),
            "vendor":      pkg.attrib.get("vendor", "Unknown"),
            "partnumber":  pkg.attrib.get("partnumber", "Unknown"),
        }

        variables_el = pkg.find("p:Variables", ns)
        if variables_el is not None and variables_el.text and variables_el.text.strip():
            raise ImportError(
                "This file uses PLECS scripted variables – only 'Table only' format is supported.")

        semi = pkg.find("p:SemiconductorData", ns)
        if semi is None:
            raise ValueError("No <SemiconductorData> found.")

        channel_list, e_on_list, e_off_list = [], [], []

        # ---- ConductionLoss ----
        cond_el = semi.find("p:ConductionLoss", ns)
        if cond_el is not None:
            method = cond_el.findtext("p:ComputationMethod", default="", namespaces=ns).lower()
            if "table" not in method:
                raise ImportError("ConductionLoss is not 'Table only' – cannot import.")

            i_text = cond_el.findtext("p:CurrentAxis", default="", namespaces=ns)
            t_text = cond_el.findtext("p:TemperatureAxis", default="", namespaces=ns)
            current_axis = [float(x) for x in i_text.split() if x]
            temp_axis    = [float(x) for x in t_text.split() if x]

            vdrop_el = cond_el.find("p:VoltageDrop", ns)
            scale = float(vdrop_el.attrib.get("scale", "1")) if vdrop_el is not None else 1.0
            v_g = 12.0 if info["class"] != "Diode" else 0.0

            for t_idx, temp_el in enumerate(vdrop_el.findall("p:Temperature", ns)):
                v_vals = [float(x) * scale for x in temp_el.text.split() if x]
                # PLECS ConductionLoss: VoltageDrop(I) -> graph_v_i = [V_axis, I_axis]
                # For MOSFET PLECS mirrors negative currents; strip them (keep non-negative half)
                if info["class"] != "Diode":
                    mid = len(current_axis) // 2
                    if len(current_axis) % 2 == 0 and current_axis[mid] >= 0:
                        i_half = current_axis[mid:]
                        v_half = v_vals[mid:]
                    else:
                        i_half = [i for i in current_axis if i >= 0]
                        v_half = v_vals[len(current_axis) - len(i_half):]
                else:
                    i_half = current_axis
                    v_half = v_vals

                tj = temp_axis[t_idx] if t_idx < len(temp_axis) else 25.0
                channel_list.append({
                    "t_j": tj,
                    "v_g": v_g,
                    "graph_v_i": [v_half, i_half]
                })

        # ---- TurnOnLoss / TurnOffLoss ----
        def _parse_loss(tag: str, default_v_g: float) -> list:
            el = semi.find(f"p:{tag}", ns)
            if el is None:
                return []
            method = el.findtext("p:ComputationMethod", default="", namespaces=ns).lower()
            if "table" not in method:
                return []

            i_text = el.findtext("p:CurrentAxis", default="", namespaces=ns)
            v_text = el.findtext("p:VoltageAxis", default="", namespaces=ns)
            t_text = el.findtext("p:TemperatureAxis", default="", namespaces=ns)
            current_axis = [float(x) for x in i_text.split() if x]
            voltage_axis = [float(x) for x in v_text.split() if x]
            temp_axis    = [float(x) for x in t_text.split() if x]

            energy_el = el.find("p:Energy", ns)
            scale = float(energy_el.attrib.get("scale", "1")) if energy_el is not None else 1.0

            result = []
            for t_idx, temp_el in enumerate(energy_el.findall("p:Temperature", ns)):
                for v_idx, volt_el in enumerate(temp_el.findall("p:Voltage", ns)):
                    v_supply = voltage_axis[v_idx] if v_idx < len(voltage_axis) else 0.0
                    if v_supply == 0.0:
                        continue  # skip zero-voltage placeholder rows
                    e_vals = [float(x) * scale for x in volt_el.text.split() if x]
                    e_joules = [e / 1000.0 for e in e_vals]  # mJ -> J
                    tj = temp_axis[t_idx] if t_idx < len(temp_axis) else 25.0
                    result.append({
                        "dataset_type": "graph_i_e",
                        "t_j": tj,
                        "v_supply": v_supply,
                        "v_g": default_v_g,
                        "r_g": 0,
                        "graph_i_e": [current_axis, e_joules]
                    })
            return result

        v_g_on  = 12.0 if info["class"] != "Diode" else 0.0
        v_g_off = 0.0  if info["class"] != "Diode" else 12.0
        e_on_list  = _parse_loss("TurnOnLoss",  v_g_on)
        e_off_list = _parse_loss("TurnOffLoss", v_g_off)

        # ---- ThermalModel (Foster) ----
        foster_dict = {}
        thermal_el = pkg.find("p:ThermalModel", ns)
        if thermal_el is not None:
            branch = thermal_el.find("p:Branch", ns)
            if branch is not None and branch.attrib.get("type", "").lower() == "foster":
                r_vec, tau_vec = [], []
                for el in branch.findall("p:RTauElement", ns):
                    r_vec.append(float(el.attrib.get("R", 0)))
                    tau_str = el.attrib.get("Tau", "0")
                    tau_vec.append(float(tau_str) if tau_str else 0.0)
                if r_vec:
                    foster_dict = {
                        "r_th_total":  sum(r_vec),
                        "r_th_vector": r_vec,
                        "tau_total":   sum(tau_vec),
                        "tau_vector":  tau_vec,
                        "c_th_total":  None,
                        "c_th_vector": None,
                        "graph_t_rthjc": []
                    }

        return info, channel_list, e_on_list, e_off_list, foster_dict

    # --- Parse switch file ---
    try:
        sw_info, sw_ch, sw_eon, sw_eoff, sw_foster = _parse_xml_file(sw_path)
    except Exception as e:
        print(f"[ERROR] Failed to parse switch XML: {e}")
        return False

    if sw_info["class"] not in ("IGBT", "MOSFET"):
        print(f"[ERROR] Switch file class is '{sw_info['class']}' – expected IGBT or MOSFET.")
        return False

    # --- Parse diode file (optional) ---
    di_ch, di_eoff, di_foster = [], [], {}
    if di_path and os.path.isfile(di_path):
        try:
            di_info, di_ch, _, di_eoff, di_foster = _parse_xml_file(di_path)
            if di_info["partnumber"] != sw_info["partnumber"]:
                print(f"[WARNING] Part numbers differ: switch='{sw_info['partnumber']}' "
                      f"diode='{di_info['partnumber']}'. Continuing anyway.")
        except Exception as e:
            print(f"[WARNING] Diode XML parse failed ({e}). Diode data will be empty.")
    elif di_path:
        print(f"[WARNING] Diode XML file not found: '{di_path}'. Diode data will be empty.")

    # --- Map PLECS class to our type string ---
    type_map = {"IGBT": "IGBT", "MOSFET": "SiC-MOSFET"}
    t_type = type_map.get(sw_info["class"], "IGBT")

    name = sw_info["partnumber"]
    manufacturer = sw_info["vendor"]
    today = datetime.date.today().strftime("%Y-%m-%d")

    transistor_json = {
        "name": name,
        "manufacturer": manufacturer,
        "type": t_type,
        "technology": t_type,
        "housing_type": "PLECS Import",
        "housing_area": "",
        "cooling_area": "",
        "author": "PLECS XML Importer",
        "creation_date": today,
        "last_modified": today,
        "template_version": "0.4.1",
        "template_date": today,
        "datasheet_version": "unknown",
        "datasheet_date": "",
        "datasheet_hyperlink": f"https://www.plexim.com/xml/semiconductors/{name}",
        "comment": "Imported from PLECS XML. v_abs_max, i_abs_max and other absolute ratings "
                   "are not present in PLECS XML – fill them using the 'edit' command.",
        "v_abs_max": "",
        "i_abs_max": max((max(ch["graph_v_i"][1]) for ch in sw_ch if ch.get("graph_v_i")),
                         default=""),
        "i_cont": "",
        "t_c_max": "",
        "r_g_int": 0,
        "r_th_cs": 0,
        "r_th_switch_cs": 0,
        "r_th_diode_cs": 0,
        "c_iss": None, "c_iss_fix": None,
        "c_oss": None, "c_oss_fix": None,
        "c_oss_tr": None, "c_oss_tr_c_o": None,
        "c_oss_tr_v_ds": None, "c_oss_tr_v_gs": None,
        "c_oss_er": None, "c_oss_er_c_o": None,
        "c_oss_er_v_ds": None, "c_oss_er_v_gs": None,
        "c_rss": None, "c_rss_fix": None,
        "switch": {
            "manufacturer": manufacturer,
            "technology": t_type,
            "t_j_max": 175,
            "comment": "Imported from PLECS XML",
            "channel": sw_ch,
            "e_on": sw_eon,
            "e_off": sw_eoff,
            "e_on_meas": [],
            "e_off_meas": [],
            "linearized_switch": [],
            "r_channel_th": [],
            "thermal_foster": sw_foster,
            "soa": [],
            "charge_curve": [],
        },
        "diode": {
            "manufacturer": manufacturer,
            "technology": "body diode",
            "t_j_max": 175,
            "comment": "Imported from PLECS XML",
            "channel": di_ch,
            "e_rr": di_eoff,
            "linearized_diode": [],
            "thermal_foster": di_foster,
            "soa": [],
        },
        "graph_v_ecoss": [],
        "raw_measurement_data": ""
    }

    # --- Determine save location ---
    tech_folders = {'IGBT': 'IGBT', 'SiC-MOSFET': 'SiC-MOSFET',
                    'Si-MOSFET': 'Si-MOSFET', 'GaN-Transistor': 'GaN'}
    category = tech_folders.get(t_type, 'IGBT')
    subfolder = "PLECS_Import"
    dest_dir = os.path.join(category, subfolder)
    os.makedirs(dest_dir, exist_ok=True)

    clean_fn = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in name) + ".json"
    dest_path = os.path.join(dest_dir, clean_fn)

    if os.path.exists(dest_path):
        overwrite = input(f"[WARNING] '{clean_fn}' already exists. Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Import cancelled.")
            return False

    try:
        with open(dest_path, "w", encoding="utf-8") as fh:
            json.dump(transistor_json, fh, indent=4, ensure_ascii=False)
        print(f"\n[SUCCESS] Imported '{name}' as {t_type}.")
        print(f"  Saved to: {os.path.normpath(dest_path)}")
        print(f"  switch.channel entries : {len(sw_ch)}")
        print(f"  switch.e_on entries    : {len(sw_eon)}")
        print(f"  switch.e_off entries   : {len(sw_eoff)}")
        print(f"  diode.channel entries  : {len(di_ch)}")
        print(f"  [NOTE] v_abs_max and other ratings are blank – use 'edit' to fill them.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save JSON: {e}")
        return False


# ---------------------------------------------------------------------------
# CONVERTER CLI
# ---------------------------------------------------------------------------

def _run_converter_cli(df):
    """
    Interactive CLI wizard for converter loss-map analysis.
    Calls converters.analysis.run_loss_map and plots results with matplotlib.
    """
    # lazy import so szukaj.py still works without the converters package
    try:
        import sys, os
        import numpy as np
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from converters.core import ConverterDevice, ConverterError
        from converters.analysis import run_loss_map
    except ImportError as e:
        print(f"[ERROR] converters package not found: {e}")
        print("  Make sure the 'converters/' folder is in the same directory as szukaj.py.")
        return

    print("""
┌──────────────────────────────────────────────────────┐
│          CONVERTER LOSS MAP  –  WIZARD               │
│  Topologies: boost | buck | buck_boost               │
└──────────────────────────────────────────────────────┘
""")

    # ---- topology ----
    topo = input("Topology [boost]: ").strip().lower() or "boost"
    if topo not in ("boost", "buck", "buck_boost"):
        print("[ERROR] Unknown topology. Choose: boost | buck | buck_boost"); return

    # ---- device selection via numbered list ----
    names = sorted(df["name"].dropna().tolist())
    for i, n in enumerate(names, 1):
        print(f"  [{i:>3}] {n}")

    def _pick(label):
        raw = input(f"\nSelect {label} (number): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(names):
            name = names[int(raw) - 1]
            row  = df[df["name"] == name]
            if row.empty:
                print(f"[ERROR] '{name}' not found."); return None
            path = row.iloc[0]["_original_file_path"]
            try:
                dev = ConverterDevice(path)
                print(f"  Loaded: {dev}")
                return dev
            except Exception as e:
                print(f"[ERROR] {e}"); return None
        print("[ERROR] Invalid selection."); return None

    t1 = _pick("T1 – active switch")
    if t1 is None: return
    t2 = _pick("T2 – freewheeling diode / second switch")
    if t2 is None: return

    # ---- parameters ----
    def _f(prompt, default):
        raw = input(f"  {prompt} [{default}]: ").strip()
        try:    return float(raw) if raw else float(default)
        except: return float(default)

    def _i(prompt, default):
        raw = input(f"  {prompt} [{default}]: ").strip()
        try:    return int(raw) if raw else int(default)
        except: return int(default)

    print("\n--- Operating parameters (Enter = use default) ---")
    # NOTE: converters/analysis.py's run_loss_map() expects a "params_legacy"
    # object with these exact attributes (see its docstring) — it is NOT the
    # new ConverterParams dataclass (which uses v_in/v_in_min/v_in_max, no
    # v_in_range tuple, and no 'inductance' field at all, only 'zeta').
    from types import SimpleNamespace
    params = SimpleNamespace(
        v_out         = _f("V_out [V]",           400),
        v_in_range    = (_f("V_in min [V]",        200),
                         _f("V_in max [V]",        800)),
        p_out_range   = (_f("P_out min [W]",       500),
                         _f("P_out max [W]",      10000)),
        frequency     = _f("Frequency [Hz]",     10000),
        zeta          = _f("Zeta = f*L [-]",         5),
        v_g_on        = _f("V_g_on [V]",           15),
        r_g_on        = _f("R_g_on [Ω] (0 = datasheet nominal)",  0),
        r_g_off       = _f("R_g_off [Ω] (0 = datasheet nominal)", 0),
        t_heatsink    = _f("T_heatsink [°C]",       50),
        r_th_heatsink = _f("Rth_heatsink [K/W]",   0.1),
        n_points      = _i("Grid points",           40),
    )

    print("\n⏳ Computing loss map…")
    try:
        result = run_loss_map(topo, t1, t2, params)
    except Exception as e:
        print(f"[ERROR] {e}"); return

    if result.warnings:
        print("\n⚠ Warnings:")
        for w in result.warnings:
            print(f"  {w}")

    # ---- print summary at operating centre ----
    mid_v = len(result.v_in_vec) // 2
    mid_p = len(result.p_out_vec) // 2
    print(f"\n--- Results at V_in={result.v_in_vec[mid_v]:.0f} V, "
          f"P_out={result.p_out_vec[mid_p]:.0f} W ---")
    for attr, label in [
        ("P_cond_T1", "T1 Conduction losses"),
        ("P_cond_T2", "T2 Conduction losses"),
        ("P_sw_T1",   "T1 Switching losses "),
        ("P_rr_T2",   "T2 Rev-recovery     "),
        ("P_total",   "Total losses        "),
        ("T_j_T1",    "T1 Junction temp    "),
        ("T_j_T2",    "T2 Junction temp    "),
        ("duty",      "Duty cycle          "),
        ("i_peak",    "Peak current        "),
    ]:
        arr = getattr(result, attr)
        val = arr[mid_p, mid_v]
        unit = "°C" if "T_j" in attr else ("A" if "peak" in attr else
               ("-" if "duty" in attr else "W"))
        print(f"  {label}: {val:.3f} {unit}" if not np.isnan(val)
              else f"  {label}: N/A")

    # ---- plot ----
    try:
        import matplotlib.pyplot as plt
        import matplotlib

        maps_to_plot = [
            ("P_total",   "Total losses [W]",      "plasma"),
            ("P_sw_T1",   "T1 Switching losses [W]","hot"),
            ("T_j_T1",    "T1 Junction temp [°C]", "RdYlGn_r"),
            ("duty",      "Duty cycle [-]",         "viridis"),
        ]
        valid_maps = [(k, l, c) for k, l, c in maps_to_plot
                      if not np.all(np.isnan(getattr(result, k)))]

        n_plots = len(valid_maps)
        cols = 2
        rows = (n_plots + 1) // 2
        fig, axes = plt.subplots(rows, cols, figsize=(12, 5 * rows))
        axes = np.array(axes).flatten()

        V, P = np.meshgrid(result.v_in_vec, result.p_out_vec)

        for ax, (key, label, cmap) in zip(axes, valid_maps):
            data = np.ma.masked_invalid(getattr(result, key))
            pc = ax.pcolormesh(V, P, data, shading="auto", cmap=cmap)
            fig.colorbar(pc, ax=ax, fraction=0.046, pad=0.04).set_label(label, fontsize=8)
            try:
                levels = np.linspace(np.nanmin(data), np.nanmax(data), 7)
                cs = ax.contour(V, P, data, levels=levels,
                                colors="white", linewidths=0.5, alpha=0.6)
                ax.clabel(cs, fmt="%.1f", fontsize=7, inline=True)
            except Exception:
                pass
            ax.set_xlabel("V_in [V]", fontsize=8)
            ax.set_ylabel("P_out [W]", fontsize=8)
            ax.set_title(label, fontsize=9)

        # hide unused axes
        for ax in axes[n_plots:]:
            ax.set_visible(False)

        topo_label = {"boost": "Boost", "buck": "Buck",
                      "buck_boost": "Buck-Boost"}.get(topo, topo)
        fig.suptitle(f"{topo_label} Converter Loss Map\n"
                     f"T1: {result.t1_name}   |   T2: {result.t2_name}",
                     fontsize=11, fontweight="bold")
        plt.tight_layout()
        plt.show()

    except ImportError:
        print("[INFO] matplotlib not installed – skipping plots.")
        print("       Run: pip install matplotlib")

    print("[DONE] Converter analysis complete.\n")


# ---------------------------------------------------------------------------
# INTERACTIVE SEARCH LOOP
# ---------------------------------------------------------------------------

def interactive_search(df):
    print("\n=== Comprehensive TransistorDataBase System ===")
    print("Type 'help' for full command reference and search examples.\n")

    current_df = df
    last_result = None
    last_single_row = None  # store last single-result row for 'full' command

    while True:
        try:
            query = input("search > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nClosing application.")
            break

        if not query:
            continue

        q_lower = query.lower()

        if q_lower == 'exit':
            print("Closing application.")
            break

        if q_lower == 'help':
            print_help()
            continue

        if q_lower.startswith('info '):
            param_to_check = query[5:].strip().lower()
            if param_to_check in FIELD_META:
                label = FIELD_META[param_to_check]['label']
                desc = FIELD_META[param_to_check]['desc']
                print(f"\nParameter: {param_to_check}")
                print(f"Label:     {label}")
                print(f"Desc:      {desc}\n")
            else:
                print(f"\n[INFO] No detailed description available for '{param_to_check}'.\n")
            continue

        if q_lower == 'list':
            if current_df.empty:
                print("\nDatabase is empty.")
            else:
                print(f"\nFound {len(current_df)} transistors in database:")
                target_columns = ['manufacturer', 'type', 'name', 'v_abs_max', 'i_abs_max']
                existing_columns = [col for col in target_columns if col in current_df.columns]

                if existing_columns:
                    print_df = current_df[existing_columns].fillna('N/A')
                    print(print_df.to_string(index=False))
                else:
                    print("Could not find the requested parameter columns in the database.")
            print()
            continue

        if q_lower == 'list_params':
            if current_df.empty:
                print("\nDatabase is empty.")
            else:
                print("\nActive properties with descriptions:")
                active_cols = sorted([c for c in current_df.columns if c != '_original_file_path'])

                for c in active_cols:
                    if c in FIELD_META:
                        label = FIELD_META[c]['label']
                        desc = FIELD_META[c]['desc']
                        print(f"  • {c.ljust(25)} | {label.ljust(25)} | {desc}")
                    else:
                        print(f"  • {c}")
            print()
            continue

        if q_lower == 'full':
            if last_single_row is not None:
                display_transistor_profile(last_single_row, show_all=True)
            else:
                print("[INFO] No single-result profile loaded. Run a query that returns exactly one device first.\n")
            continue

        if q_lower == 'compare':
            compare_transistor_charts(current_df)
            continue

        if q_lower == 'create':
            if create_new_transistor_template():
                current_df = load_full_database()
            continue

        if q_lower == 'edit':
            if edit_transistor_file(current_df):
                current_df = load_full_database()
            continue

        if q_lower in ['parse_pdf', 'import']:
            print("\nSelect import file type:")
            print("  [1] PDF Datasheet  -> Run data heuristics & manual entry wizard")
            print("  [2] JSON Record    -> Directly import pre-formatted model file")
            print("  [3] PLECS XML      -> Import switch + diode XML files from PLECS")
            choice = input("Choose option [1/2/3]: ").strip()

            success = False
            if choice == '1':
                success = parse_pdf_datasheet_comprehensive()
            elif choice == '2':
                success = import_ready_json_file()
            elif choice == '3':
                success = import_plecs_xml()
            else:
                print("[ERROR] Invalid selection. Aborting import.")

            if success:
                current_df = load_full_database()
            continue

        if q_lower == 'export':
            if last_result is not None:
                print("\nSelect export format:")
                print("  [1] JSON          -> folder structure with JSON data files and chart CSVs")
                print("  [2] CSV           -> folder structure with CSV data files and chart CSVs")
                print("  [3] PLECS XML     -> PLECS-compatible switch + diode XML files")
                fmt_choice = input("Choose option [1/2/3]: ").strip()

                if fmt_choice == '1':
                    export_folder_structure(last_result, data_format='json')
                elif fmt_choice == '2':
                    export_folder_structure(last_result, data_format='csv')
                elif fmt_choice == '3':
                    out_dir = input("Output directory [Exported_PLECS]: ").strip() or "Exported_PLECS"
                    exported = 0
                    for _, row in last_result.iterrows():
                        src = row.get('_original_file_path')
                        if src and os.path.isfile(src):
                            print(f"\nExporting: {row.get('name', '?')}")
                            if export_plecs_xml(src, out_dir):
                                exported += 1
                    print(f"\n[DONE] Exported {exported}/{len(last_result)} transistors to "
                          f"'{os.path.abspath(out_dir)}'")
                else:
                    print("[ERROR] Unknown option.\n")
            else:
                print("Search for something first!\n")
            continue

        if q_lower == 'converter':
            _run_converter_cli(current_df)
            continue

        try:
            processed_query = preprocess_query(query)
            results = current_df.query(processed_query, engine='python')

            if results.empty:
                print("No matching results found.\n")
                last_result = None
                last_single_row = None
            else:
                last_result = results

                if len(results) == 1:
                    last_single_row = results.iloc[0]
                    display_transistor_profile(last_single_row, show_all=False)
                    print("\n  Type 'full' to see all 66 fields.")
                    print("  Type 'export' to generate folders and CSV data for this device.\n")

                else:
                    last_single_row = None
                    cols = ['Category']
                    potential = [c for c in current_df.columns if 'name' in c.lower() or 'id' in c.lower()]
                    if potential:
                        cols.append(potential[0])

                    display_results = results[cols].head(20).copy()
                    display_results.insert(0, '#', range(1, len(display_results) + 1))
                    print(f"\nFound {len(results)} matching devices"
                          f"{' (showing first 20)' if len(results) > 20 else ''}:")
                    print(display_results.to_string(index=False))

                    choice = input("\nEnter row number to view profile (Enter = skip): ").strip()
                    if choice.isdigit():
                        row_idx = int(choice) - 1
                        if 0 <= row_idx < min(len(results), 20):
                            last_single_row = results.iloc[row_idx]
                            last_result = results.iloc[[row_idx]]  # narrow export to this device
                            display_transistor_profile(last_single_row, show_all=False)
                            print("\n  Type 'full' to see all 66 fields.")
                            print("  Type 'export' to generate data for this device.")
                            print("  Run the search again and skip selection to export all results.\n")
                        else:
                            print("[INFO] Row number out of range.\n")
                            print("  Type 'export' to generate data for all results.\n")
                    else:
                        print("  Type 'export' to generate data for all results.\n")

        except Exception as e:
            print(f"[ERROR] Query failed: {e}")
            print("  Tip: type 'help' for syntax examples.\n")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Transistor Database CLI",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--query', type=str, default=None,
        help="Run a single pandas query and exit.\n"
             "Example: --query \"v_abs_max >= 1200\""
    )
    parser.add_argument(
        '--export', action='store_true',
        help="Export the --query results to Exported_Transistors/ (json format)."
    )
    args = parser.parse_args()

    database_df = load_full_database()

    if database_df is None:
        sys.exit(1)

    if args.query:
        # Tryb jednorazowy CLI
        try:
            processed_query = preprocess_query(args.query)
            results = database_df.query(processed_query, engine='python')

            if results.empty:
                print("No matching results found.")
            else:
                display_cols = ['name', 'manufacturer', 'Category', 'v_abs_max', 'i_abs_max']
                available = [c for c in display_cols if c in results.columns]
                print(f"\nFound {len(results)} result(s):\n")
                print(results[available].to_string(index=False))
                if args.export:
                    export_folder_structure(results, data_format='json')
        except Exception as e:
            print(f"[ERROR] Query failed: {e}")
            sys.exit(1)
    else:
        interactive_search(database_df)
