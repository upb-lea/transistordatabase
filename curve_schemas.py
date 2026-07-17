"""
curve_schemas.py
================
Poprawny opis struktury wszystkich pól "krzywych" (curve fields) w bazie
TransistorDataBase, zgodny z rzeczywistymi klasami z biblioteki
transistordatabase (data_classes.py / transistor.py / switch.py / diode.py).

Ten moduł naprawia trzy błędy obecne wcześniej w GUI.py:

  1. Krzywe trafiały do PŁASKIEGO klucza najwyższego poziomu (np. "switch_channel")
     zamiast do właściwego, ZAGNIEŻDŻONEGO miejsca (switch.channel).
  2. Dane z CSV zapisywane były jako lista par punktów [[x1,y1],[x2,y2],...]
     zamiast wymaganej, TRANSPONOWANEJ postaci [[x1,x2,...],[y1,y2,...]].
  3. Pola wielokrzywe (channel, e_on, e_off, soa, charge_curve, ...) w ogóle
     nie pozwalały podać metadanych (t_j, v_g, r_g, i_x, dataset_type...)
     opisujących, do którego zestawu należy dana krzywa.

CURVE_SCHEMAS
-------------
Dla każdego klucza z FIELD_META (pola uznawanego za "krzywą") opisujemy:

  nested_path : tuple
      Ścieżka kluczy w finalnym słowniku JSON, np. ("switch", "channel").
  container : "list" | "dict" | "raw"
      "list" - pole to LISTA obiektów (każdy z własnymi metadanymi + krzywą)
      "dict" - pole to POJEDYNCZY obiekt (np. thermal_foster)
      "raw"  - pole to surowa tablica [[X...],[Y...]] bez żadnych metadanych
  graph_key : str | "dynamic" | None
      Nazwa klucza przechowującego samą tablicę [[X...],[Y...]] wewnątrz
      obiektu. "dynamic" oznacza, że nazwa zależy od wybranego dataset_type
      (patrz DYNAMIC_GRAPH_KEY_FIELD / DYNAMIC_GRAPH_KEY_MAP niżej).
      None oznacza, że to pole nie ma w ogóle krzywej (same skalary, np.
      linearized_switch).
  metadata : list[tuple(name, kind, required)]
      kind: "float" | "str" | "choice:opt1,opt2,..."
"""

import os
import pandas as pd


# ---------------------------------------------------------------------------
# Pola, w których docelowy klucz tablicy zależy od wybranego dataset_type
# (SwitchEnergyData: graph_i_e / graph_r_e / graph_t_e / single)
# ---------------------------------------------------------------------------
DYNAMIC_GRAPH_KEY_FIELD = "dataset_type"
DYNAMIC_GRAPH_KEY_MAP = {
    "graph_i_e": "graph_i_e",
    "graph_r_e": "graph_r_e",
    "graph_t_e": "graph_t_e",
    "single": None,   # 'single' = tylko wartość skalarna e_x, bez żadnej krzywej
}

_SWITCH_ENERGY_METADATA = [
    ("dataset_type", "choice:graph_i_e,graph_r_e,graph_t_e,single", True),
    ("t_j", "float", False),
    ("v_supply", "float", False),
    ("v_g", "float", False),
    ("v_g_off", "float", False),
    ("r_g", "float", False),
    ("i_x", "float", False),
    ("e_x", "float", False),
    ("comment", "str", False),
]

CURVE_SCHEMAS = {
    # ---- pojemności (top-level, lista {t_j, graph_v_c}) --------------------
    "c_iss": {"nested_path": ("c_iss",), "container": "list",
              "graph_key": "graph_v_c", "metadata": [("t_j", "float", True)]},
    "c_oss": {"nested_path": ("c_oss",), "container": "list",
              "graph_key": "graph_v_c", "metadata": [("t_j", "float", True)]},
    "c_rss": {"nested_path": ("c_rss",), "container": "list",
              "graph_key": "graph_v_c", "metadata": [("t_j", "float", True)]},

    # ---- energia w C_oss (top-level, surowa tablica, bez metadanych) ------
    "graph_v_ecoss": {"nested_path": ("graph_v_ecoss",), "container": "raw",
                       "graph_key": None, "metadata": []},

    # ---- switch.channel / diode.channel  (lista {t_j, v_g, graph_v_i}) ----
    "switch_channel": {"nested_path": ("switch", "channel"), "container": "list",
                        "graph_key": "graph_v_i",
                        "metadata": [("t_j", "float", True), ("v_g", "float", True)]},
    "diode_channel": {"nested_path": ("diode", "channel"), "container": "list",
                       "graph_key": "graph_v_i",
                       "metadata": [("t_j", "float", True), ("v_g", "float", False)]},

    # ---- switch.soa / diode.soa  (lista {t_c, time_pulse, graph_i_v}) -----
    "switch_soa": {"nested_path": ("switch", "soa"), "container": "list",
                   "graph_key": "graph_i_v",
                   "metadata": [("t_c", "float", False), ("time_pulse", "float", False)]},
    "diode_soa": {"nested_path": ("diode", "soa"), "container": "list",
                  "graph_key": "graph_i_v",
                  "metadata": [("t_c", "float", False), ("time_pulse", "float", False)]},

    # ---- switch.charge_curve  (lista {t_j, v_supply, i_channel, i_g, graph_q_v}) ---
    "switch_charge_curve": {"nested_path": ("switch", "charge_curve"), "container": "list",
                             "graph_key": "graph_q_v",
                             "metadata": [("t_j", "float", False), ("v_supply", "float", False),
                                          ("i_channel", "float", False), ("i_g", "float", False)]},

    # ---- switch.r_channel_th  (lista {i_channel, v_g, dataset_type, r_channel_nominal, graph_t_r}) ---
    "switch_r_channel_th": {"nested_path": ("switch", "r_channel_th"), "container": "list",
                             "graph_key": "graph_t_r",
                             "metadata": [("i_channel", "float", False), ("v_g", "float", False),
                                          ("dataset_type", "choice:t_r,t_factor", True),
                                          ("r_channel_nominal", "float", False)]},

    # ---- switch.e_on / e_off / e_on_meas / e_off_meas, diode.e_rr ---------
    "switch_e_on": {"nested_path": ("switch", "e_on"), "container": "list",
                     "graph_key": "dynamic", "metadata": _SWITCH_ENERGY_METADATA},
    "switch_e_off": {"nested_path": ("switch", "e_off"), "container": "list",
                      "graph_key": "dynamic", "metadata": _SWITCH_ENERGY_METADATA},
    "switch_e_on_meas": {"nested_path": ("switch", "e_on_meas"), "container": "list",
                          "graph_key": "dynamic", "metadata": _SWITCH_ENERGY_METADATA},
    "switch_e_off_meas": {"nested_path": ("switch", "e_off_meas"), "container": "list",
                           "graph_key": "dynamic", "metadata": _SWITCH_ENERGY_METADATA},
    "diode_e_rr": {"nested_path": ("diode", "e_rr"), "container": "list",
                   "graph_key": "dynamic", "metadata": _SWITCH_ENERGY_METADATA},

    # ---- modele liniowe (same skalary, bez krzywej) -----------------------
    "switch_linearized_switch": {"nested_path": ("switch", "linearized_switch"), "container": "list",
                                  "graph_key": None,
                                  "metadata": [("t_j", "float", True), ("v_g", "float", False),
                                               ("i_channel", "float", True), ("r_channel", "float", True),
                                               ("v0_channel", "float", True)]},
    "diode_linearized_diode": {"nested_path": ("diode", "linearized_diode"), "container": "list",
                                "graph_key": None,
                                "metadata": [("t_j", "float", True), ("v_g", "float", False),
                                             ("i_channel", "float", True), ("r_channel", "float", True),
                                             ("v0_channel", "float", True)]},

    # ---- Foster (pojedynczy obiekt, nie lista) -----------------------------
    "switch_thermal_foster": {"nested_path": ("switch", "thermal_foster"), "container": "dict",
                               "graph_key": "graph_t_rthjc",
                               "metadata": [("r_th_total", "float", False), ("c_th_total", "float", False),
                                            ("tau_total", "float", False)]},
    "diode_thermal_foster": {"nested_path": ("diode", "thermal_foster"), "container": "dict",
                              "graph_key": "graph_t_rthjc",
                              "metadata": [("r_th_total", "float", False), ("c_th_total", "float", False),
                                           ("tau_total", "float", False)]},
}

# Pola, które FIELD_META/is_curve_field błędnie klasyfikował jako "krzywe",
# a w rzeczywistości (klasa EffectiveOutputCapacitance) to same skalary
# (c_o, v_ds, v_gs) pogrupowane w jeden pod-obiekt. Traktujemy je jako zwykłe
# pola liczbowe, zapisywane na końcu do structured["c_oss_er"]/["c_oss_tr"].
SCALAR_GROUP_FIELDS = {
    "c_oss_er": {"nested_path": ("c_oss_er",),
                 "members": {"c_oss_er_c_o": "c_o", "c_oss_er_v_ds": "v_ds", "c_oss_er_v_gs": "v_gs"}},
    "c_oss_tr": {"nested_path": ("c_oss_tr",),
                 "members": {"c_oss_tr_c_o": "c_o", "c_oss_tr_v_ds": "v_ds", "c_oss_tr_v_gs": "v_gs"}},
}
# Klucze pól, które NIE powinny być traktowane jako pola do CSV (są skalarami
# wchodzącymi w skład SCALAR_GROUP_FIELDS powyżej, plus same nagłówki grup).
NON_CURVE_SCALAR_KEYS = {
    "c_oss_er", "c_oss_er_c_o", "c_oss_er_v_ds", "c_oss_er_v_gs",
    "c_oss_tr", "c_oss_tr_c_o", "c_oss_tr_v_ds", "c_oss_tr_v_gs",
}


def empty_container(field_key: str):
    """Zwraca prawidłowy 'pusty' kontener dla danego pola (wg jego schematu)."""
    schema = CURVE_SCHEMAS.get(field_key)
    if schema is None:
        return None
    if schema["container"] == "list":
        return []
    return None  # dict / raw -> brak danych = None


def csv_to_graph_array(filepath: str):
    """
    Wczytuje plik CSV (dowolny separator, w tym ';') z dokładnie dwiema
    kolumnami X;Y i zwraca dane w POPRAWNEJ, transponowanej postaci
    wymaganej przez bibliotekę transistordatabase:

        [[x1, x2, x3, ...], [y1, y2, y3, ...]]

    zamiast błędnej listy par punktów [[x1,y1],[x2,y2],...].

    Punkty są dodatkowo sortowane rosnąco po X (wymagane np. przy interpolacji
    w bibliotece).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(filepath)

    with open(filepath, "r", encoding="utf-8-sig") as f:
        raw_lines = [ln.strip() for ln in f if ln.strip()]

    if not raw_lines:
        raise ValueError("Plik CSV jest pusty.")

    # Wykrycie separatora kolumn na podstawie pierwszej niepustej linii.
    # WebPlotDigitizer w ustawieniach US eksportuje "x,y" (kropka dziesiętna),
    # a w ustawieniach regionalnych EU "x;y" (przecinek jako separator dziesiętny).
    sample = raw_lines[0]
    sep = ";" if sample.count(";") >= 1 else ","

    def parse_num(token: str) -> float:
        token = token.strip()
        if sep == ";" and "," in token:
            # Format EU: kropka (jeśli występuje) to separator tysięcy, przecinek to separator dziesiętny.
            token = token.replace(".", "").replace(",", ".")
        return float(token)

    x_vals, y_vals = [], []
    for i, line in enumerate(raw_lines):
        parts = line.split(sep)
        if len(parts) < 2:
            continue
        try:
            x = parse_num(parts[0])
            y = parse_num(parts[1])
        except ValueError:
            if i == 0:
                # Pierwsza linia nie jest liczbą -> to nagłówek (np. "X,Y"), pomiń ją.
                continue
            raise ValueError(f"Nie można sparsować linii {i + 1} pliku CSV: '{line}'")
        x_vals.append(x)
        y_vals.append(y)

    if len(x_vals) < 2:
        raise ValueError("Plik CSV musi zawierać co najmniej dwa punkty danych (X;Y lub X,Y).")

    pairs = sorted(zip(x_vals, y_vals), key=lambda p: p[0])
    x_sorted = [p[0] for p in pairs]
    y_sorted = [p[1] for p in pairs]
    return [x_sorted, y_sorted]


def get_nested(d: dict, path: tuple, default=None):
    """Bezpiecznie pobiera wartość zagnieżdżoną w słowniku wg ścieżki kluczy."""
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def set_nested(d: dict, path: tuple, value):
    """Ustawia wartość w słowniku pod zagnieżdżoną ścieżką, tworząc po drodze
    brakujące pod-słowniki (nie nadpisując reszty istniejącego pod-słownika)."""
    cur = d
    for key in path[:-1]:
        if key not in cur or not isinstance(cur[key], dict):
            cur[key] = {}
        cur = cur[key]
    cur[path[-1]] = value


def describe_dataset(field_key: str, obj: dict) -> str:
    """Buduje krótki, czytelny opis pojedynczego zestawu danych (do listy w GUI)."""
    schema = CURVE_SCHEMAS.get(field_key, {})
    parts = []
    for name, _kind, _req in schema.get("metadata", []):
        val = obj.get(name)
        if val not in (None, ""):
            parts.append(f"{name}={val}")
    graph_key = schema.get("graph_key")
    if graph_key == "dynamic":
        graph_key = DYNAMIC_GRAPH_KEY_MAP.get(obj.get("dataset_type"))
    n_pts = ""
    if graph_key and isinstance(obj.get(graph_key), list) and len(obj[graph_key]) == 2:
        n_pts = f", {len(obj[graph_key][0])} pkt"
    return (", ".join(parts) if parts else "(brak metadanych)") + n_pts