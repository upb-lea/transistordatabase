"""
gui.py – Graficzna nakładka na szukaj.py
Wszystkie operacje na danych delegowane są do funkcji z szukaj.py.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, json, datetime, sys, csv, subprocess
import xml.etree.ElementTree as ET
import pandas as pd
import importlib.util
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Import szukaj.py z tego samego katalogu (bez względu na cwd)
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

spec = importlib.util.spec_from_file_location("szukaj", os.path.join(_THIS_DIR, "szukaj.py"))
_szukaj = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_szukaj)

# Wszystkie funkcje i stałe ze szukaj
load_full_database          = _szukaj.load_full_database
preprocess_query            = _szukaj.preprocess_query
export_folder_structure     = _szukaj.export_folder_structure
export_plecs_xml            = _szukaj.export_plecs_xml
import_plecs_xml_func       = _szukaj.import_plecs_xml   # importujemy pod inną nazwą by nie kolidować
import_ready_json_file      = _szukaj.import_ready_json_file
deep_search_charts          = _szukaj.deep_search_charts
build_structured_json       = _szukaj.build_structured_json
FIELD_META                  = _szukaj.FIELD_META

# ---------------------------------------------------------------------------
# Converters package (optional – graceful fallback if folder missing)
# ---------------------------------------------------------------------------
try:
    import sys as _sys
    _sys.path.insert(0, _THIS_DIR)
    from converters.gui_tab import ConverterTab
    _CONVERTERS_AVAILABLE = True
except ImportError:
    _CONVERTERS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Kolory i stałe UI
# ---------------------------------------------------------------------------
CLR_HDR   = "#2c3e50"
CLR_BTN   = "#2980b9"
CLR_ODD   = "#f5f7fa"
CLR_EVEN  = "#ffffff"
CLR_DIFF  = "#fff8e1"
CLR_GREEN = "#27ae60"
CLR_RED   = "#c0392b"

TECH_CATEGORIES = ["GaN", "IGBT", "SiC-MOSFET", "Si-MOSFET"]

# ---------------------------------------------------------------------------
# Mapowanie nazw kluczy wykresów na etykiety osi fizycznych
# Klucz to fragment nazwy ścieżki (podciąg), wartość to (xlabel, ylabel)
# ---------------------------------------------------------------------------
_CHART_AXIS_MAP = [
    # napięcie - prąd przewodzenia
    ("graph_v_i",       "V [V]",        "I [A]"),
    ("graph_i_v",       "I [A]",        "V [V]"),
    # energia przełączania vs prąd
    ("graph_i_e",       "I [A]",        "E [J]"),
    ("e_on",            "I [A]",        "E_on [J]"),
    ("e_off",           "I [A]",        "E_off [J]"),
    ("e_rr",            "I [A]",        "E_rr [J]"),
    # pojemności vs napięcie
    ("c_iss",           "V_DS [V]",     "C_iss [F]"),
    ("c_oss",           "V_DS [V]",     "C_oss [F]"),
    ("c_rss",           "V_DS [V]",     "C_rss [F]"),
    # energia w C_oss vs napięcie
    ("v_ecoss",         "V_DS [V]",     "E_oss [J]"),
    # ładunek bramki
    ("charge",          "Q_g [C]",      "V_GS [V]"),
    # SOA
    ("soa",             "V [V]",        "I [A]"),
    # termiczne Foster
    ("thermal",         "t [s]",        "Z_th [K/W]"),
    # linearized
    ("linearized",      "I [A]",        "V [V]"),
]

def _get_axis_labels(chart_key: str):
    """Zwraca (xlabel, ylabel) na podstawie nazwy klucza wykresu."""
    key_lower = chart_key.lower()
    for fragment, xl, yl in _CHART_AXIS_MAP:
        if fragment in key_lower:
            return xl, yl
    return "X", "Y"

# ============================================================================
# HELPER: wykrywanie pól z krzywymi
# ============================================================================
def is_curve_field(fn):
    return (fn.startswith("graph_") or fn.startswith("diode_") or
            fn.startswith("switch_") or fn.startswith("c_")) \
        and not fn.endswith("_fix") \
        and "manufacturer" not in fn and "comment" not in fn \
        and "technology" not in fn and "t_j_max" not in fn

# ============================================================================
# HELPER: wczytaj JSON bezpośrednio
# ============================================================================
def load_json_for_name(name: str, df: pd.DataFrame):
    """Zwraca (dict, path) lub (None, None). Szuka w df, potem przez os.walk."""
    name = name.strip()
    for sub in [df[df["name"] == name],
                df[df["name"].str.lower() == name.lower()]]:
        if not sub.empty:
            p = sub.iloc[0].get("_original_file_path")
            if p and os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f), p
                except Exception:
                    pass
    # Fallback: os.walk
    skip = {"Exported_Comparisons", "Exported_Transistors", "__pycache__", ".git"}
    for root, dirs, files in os.walk(_THIS_DIR):
        dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
        for fn in files:
            if not fn.endswith(".json"):
                continue
            fp = os.path.join(root, fn)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                jname = data.get("name", "")
                stem  = os.path.splitext(fn)[0]
                if jname == name or jname.lower() == name.lower() \
                        or stem == name or stem.lower() == name.lower():
                    return data, fp
            except Exception:
                pass
    return None, None

# ============================================================================
# POPUP: powiększony wykres z tooltipem współrzędnych i fizycznymi etykietami osi
# ============================================================================
def open_chart_popup(parent, title, curves, chart_key=""):
    xl, yl = _get_axis_labels(chart_key or title)
    win = tk.Toplevel(parent)
    win.title(title); win.geometry("860x580"); win.resizable(True, True)
    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=96)
    COLS = ['#2980b9','#e74c3c','#27ae60','#8e44ad','#e67e22']
    LS   = ['-','--',':','-.']
    lines_plotted = []
    for li, (lbl, xd, yd) in enumerate(curves):
        ln, = ax.plot(xd, yd, color=COLS[li%5], linestyle=LS[li%4],
                linewidth=1.8, marker='.', markersize=4, label=lbl, picker=5)
        lines_plotted.append(ln)
    ax.set_title(title, fontsize=11, pad=8)
    ax.set_xlabel(xl, fontsize=10)
    ax.set_ylabel(yl, fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    if len(curves) > 1: ax.legend(fontsize=9)
    fig.tight_layout()
    cv = FigureCanvasTkAgg(fig, master=win); cv.draw()
    cv.get_tk_widget().pack(fill="both", expand=True)
    NavigationToolbar2Tk(cv, win).update()

    # --- tooltip ze współrzędnymi ---
    annot = ax.annotate("", xy=(0,0), xytext=(12,12), textcoords="offset points",
                        bbox=dict(boxstyle="round,pad=0.4", fc="#ffffcc", ec="#888", alpha=0.9),
                        fontsize=8, visible=False)

    def _on_move(event):
        if event.inaxes != ax:
            annot.set_visible(False); cv.draw_idle(); return
        found = False
        for ln, (lbl, xd, yd) in zip(lines_plotted, curves):
            cont, idx = ln.contains(event)
            if cont:
                i = idx["ind"][0]
                x_val, y_val = xd[i], yd[i]
                annot.xy = (x_val, y_val)
                annot.set_text(f"{lbl}\n{xl}: {x_val:.4g}\n{yl}: {y_val:.4g}")
                annot.set_visible(True); found = True; break
        if not found:
            annot.set_visible(False)
        cv.draw_idle()

    cv.mpl_connect("motion_notify_event", _on_move)
    win.protocol("WM_DELETE_WINDOW", lambda: (plt.close(fig), win.destroy()))

# ============================================================================
# GŁÓWNA KLASA GUI
# ============================================================================
class TransistorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Transistor Database – GUI for szukaj.py")
        self.root.geometry("1450x870")

        self.df = load_full_database()      # pd.DataFrame – główna baza danych
        self.last_results: pd.DataFrame = self.df.copy()

        self._build_ui()

    # ------------------------------------------------------------------
    # BUDOWA UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Status bar FIRST – must exist before any _build_* method tries to use it
        self.status = ttk.Label(self.root, text=f"Loaded {len(self.df)} transistors.",
                                relief="sunken", anchor="w")
        self.status.pack(fill="x", side="bottom", ipady=2)

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=5, pady=5)

        tabs = [
            ("tab_browser",  " 🔍 Browser "),
            ("tab_search",   " 🔎 Search "),
            ("tab_profile",  " 📋 Profile "),
            ("tab_compare",  " 📊 Compare "),
            ("tab_create",   " ➕ Create "),
            ("tab_edit",     " ✏️  Edit "),
            ("tab_import",   " 📥 Import "),
            ("tab_export",   " 📤 Export "),
            ("tab_converter"," ⚡ Converters "),
        ]
        for attr, label in tabs:
            f = ttk.Frame(self.nb)
            setattr(self, attr, f)
            self.nb.add(f, text=label)

        self._build_browser()
        self._build_search()
        self._build_profile()
        self._build_compare()
        self._build_create()
        self._build_edit()
        self._build_import()
        self._build_export()
        self._build_converter()

    # ==================================================================
    # BROWSER TAB
    # ==================================================================
    def _build_browser(self):
        p = self.tab_browser
        p.columnconfigure(0, weight=1)
        p.columnconfigure(1, weight=0)
        p.rowconfigure(1, weight=1)

        # --- toolbar ---
        tb = ttk.Frame(p, padding=(8,6,8,2)); tb.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(tb, text="🔍 Browser", font=("Arial",14,"bold")).pack(side="left")
        ttk.Button(tb, text="🔄 Reload DB", command=self._reload_db).pack(side="right", padx=4)
        ttk.Button(tb, text="📤 Export selected", command=self._browser_export).pack(side="right", padx=4)
        ttk.Button(tb, text="📋 Open Profile", command=self._browser_open_profile).pack(side="right", padx=4)
        ttk.Button(tb, text="📊 Add to Compare", command=self._browser_add_compare).pack(side="right", padx=4)

        # --- table (left) ---
        tf = ttk.Frame(p); tf.grid(row=1, column=0, sticky="nsew", padx=(8,4), pady=4)
        tf.columnconfigure(0, weight=1); tf.rowconfigure(0, weight=1)

        # All scalar (non-curve) columns from FIELD_META as browseable columns
        # Always start with 'name', then all scalar FIELD_META keys
        _scalar_fields = [k for k in FIELD_META if not is_curve_field(k)]
        cols = tuple(["name"] + _scalar_fields)

        self.browser_tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="extended")
        # Default widths: name wide, rest moderate
        default_w = {"name": 220, "Category": 90, "manufacturer": 140, "v_abs_max": 90,
                     "i_abs_max": 90, "i_cont": 80, "housing_type": 90, "r_th_cs": 85,
                     "t_c_max": 80, "technology": 100, "author": 130}
        for c in cols:
            lbl = FIELD_META.get(c, {}).get("label", c) if c != "name" else "Device Name"
            self.browser_tree.heading(c, text=lbl,
                command=lambda _c=c: self._sort_browser(_c))
            self.browser_tree.column(c, width=default_w.get(c, 100), minwidth=60, stretch=False)
        self.browser_tree.tag_configure("odd",  background=CLR_ODD)
        self.browser_tree.tag_configure("even", background=CLR_EVEN)
        self.browser_tree.bind("<Double-1>", lambda e: self._browser_open_profile())

        sy = ttk.Scrollbar(tf, orient="vertical",   command=self.browser_tree.yview)
        sx = ttk.Scrollbar(tf, orient="horizontal",  command=self.browser_tree.xview)
        self.browser_tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.browser_tree.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns"); sx.grid(row=1, column=0, sticky="ew")

        # --- filter panel (right) ---
        PANEL_W = 300
        rp = ttk.Frame(p, width=PANEL_W)
        rp.grid(row=1, column=1, sticky="nsew", padx=(0,8), pady=4)
        rp.pack_propagate(False); rp.grid_propagate(False)
        rp.columnconfigure(0, weight=1); rp.rowconfigure(0, weight=1)

        sc = ttk.LabelFrame(rp, text=" Column Filters ", padding=(8,6))
        sc.grid(row=0, column=0, sticky="nsew"); sc.columnconfigure(0, weight=1); sc.rowconfigure(1, weight=1)

        # header labels
        hf = ttk.Frame(sc); hf.grid(row=0, column=0, sticky="ew", pady=(0,4))
        ttk.Label(hf, text="Show?", font=("Arial",9,"bold"), width=5).grid(row=0, column=0, padx=3, sticky="w")
        ttk.Label(hf, text="Parameter", font=("Arial",9,"bold")).grid(row=0, column=1, padx=3, sticky="w")
        ttk.Label(hf, text="Filter", font=("Arial",9,"bold")).grid(row=0, column=2, padx=3, sticky="e")

        # scrollable inner frame
        cf = ttk.Frame(sc); cf.grid(row=1, column=0, sticky="nsew")
        cf.columnconfigure(0, weight=1); cf.rowconfigure(0, weight=1)
        cv = tk.Canvas(cf, borderwidth=0, highlightthickness=0)
        scb = ttk.Scrollbar(cf, orient="vertical", command=cv.yview)
        self._browser_scroll_frame = ttk.Frame(cv)
        self._browser_scroll_frame.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0,0), window=self._browser_scroll_frame, anchor="nw")
        cv.configure(yscrollcommand=scb.set)
        cv.grid(row=0, column=0, sticky="nsew"); scb.grid(row=0, column=1, sticky="ns")
        self._browser_scroll_frame.columnconfigure(0, weight=0, minsize=24)
        self._browser_scroll_frame.columnconfigure(1, weight=1, minsize=130)
        self._browser_scroll_frame.columnconfigure(2, weight=0, minsize=90)

        def _mw(e): cv.yview_scroll(int(-1*(e.delta/120)), "units")
        cv.bind("<Enter>", lambda e: cv.bind_all("<MouseWheel>", _mw))
        cv.bind("<Leave>", lambda e: cv.unbind_all("<MouseWheel>"))

        self._browser_col_vars    = {}
        self._browser_filter_vars = {}

        # Fixed "name" row (always visible, cannot be hidden)
        ttk.Checkbutton(self._browser_scroll_frame, state="disabled").grid(
            row=0, column=0, padx=3, pady=3, sticky="w")
        ttk.Label(self._browser_scroll_frame, text="Device Name",
                  font=("Arial",9,"bold"), foreground="gray").grid(
            row=0, column=1, padx=3, pady=3, sticky="w")
        name_fv = tk.StringVar()
        name_fe = ttk.Entry(self._browser_scroll_frame, textvariable=name_fv,
                            width=11, font=("Consolas",8))
        name_fe.grid(row=0, column=2, padx=3, pady=3, sticky="ew")
        name_fe.bind("<Return>", lambda e: self._browser_apply_filters())
        self._browser_filter_vars["name"] = name_fv

        # Default visible columns (the classic subset shown by default)
        default_visible = {"Category","manufacturer","v_abs_max","i_abs_max","i_cont",
                           "housing_type","r_th_cs","t_c_max","technology","author"}

        # ALL scalar FIELD_META fields shown in filter panel
        for idx, col in enumerate(_scalar_fields, 1):
            var = tk.BooleanVar(value=(col in default_visible))
            self._browser_col_vars[col] = var
            ttk.Checkbutton(self._browser_scroll_frame, variable=var,
                            command=self._browser_rebuild_columns).grid(
                row=idx, column=0, padx=3, pady=2, sticky="w")
            meta = FIELD_META.get(col, {"label": col})
            ttk.Label(self._browser_scroll_frame, text=meta["label"],
                      font=("Arial",9)).grid(row=idx, column=1, padx=3, pady=2, sticky="w")
            fv = tk.StringVar()
            fe = ttk.Entry(self._browser_scroll_frame, textvariable=fv,
                           width=11, font=("Consolas",8))
            fe.grid(row=idx, column=2, padx=3, pady=2, sticky="ew")
            fe.bind("<Return>", lambda e: self._browser_apply_filters())
            self._browser_filter_vars[col] = fv

        af = ttk.Frame(rp, padding=(0,4,0,0)); af.grid(row=1, column=0, sticky="ew")
        ttk.Button(af, text="🔍 Apply Filters", command=self._browser_apply_filters).pack(fill="x", pady=2)
        ttk.Button(af, text="❌ Clear Filters",  command=self._browser_clear_filters).pack(fill="x", pady=2)

        self._browser_sort_col = None
        self._browser_sort_asc = True
        # Apply default visible columns and fill
        self._browser_rebuild_columns()

    def _browser_rebuild_columns(self):
        """Show/hide columns based on checkboxes – rebuild treeview column list."""
        visible = ["name"] + [c for c, v in self._browser_col_vars.items() if v.get()]
        self.browser_tree["displaycolumns"] = visible
        self._browser_apply_filters()

    def _browser_apply_filters(self):
        """Filter browser_tree rows using the filter entry widgets."""
        parts = []
        for col, fv in self._browser_filter_vars.items():
            val = fv.get().strip()
            if not val: continue
            # Only filter on columns that actually exist in the dataframe
            if col not in self.df.columns:
                continue
            # numeric operators
            if any(val.startswith(op) for op in (">=","<=","!=","==",">","<")):
                parts.append(f"{col} {val}")
            else:
                try:
                    float(val)
                    parts.append(f"{col} == {val}")
                except ValueError:
                    parts.append(f"{col}.str.contains({val!r}, case=False, na=False)")

        if not parts:
            filtered = self.df
        else:
            try:
                filtered = self.df.query(" & ".join(parts), engine="python")
            except Exception as e:
                self.status.config(text=f"⚠️ Filter error: {e}")
                return

        self.last_results = filtered
        self._fill_browser(filtered)

    def _browser_clear_filters(self):
        for fv in self._browser_filter_vars.values(): fv.set("")
        self.last_results = self.df.copy()
        self._fill_browser(self.df)

    @staticmethod
    def _cell_str(v) -> str:
        """Safely convert a dataframe cell to display string.
        Handles scalars, lists, dicts and numpy arrays without ambiguous bool errors."""
        if isinstance(v, (list, dict)):
            return "[curve]"
        try:
            if pd.isna(v):
                return "-"
        except (TypeError, ValueError):
            return "[curve]"
        s = str(v).strip()
        return "-" if s in ("", "nan", "None") else s

    def _fill_browser(self, df):
        for r in self.browser_tree.get_children():
            self.browser_tree.delete(r)
        cols = self.browser_tree["columns"]
        for i, (_, row) in enumerate(df.iterrows()):
            vals = [self._cell_str(row.get(c, "")) for c in cols]
            tag = "odd" if i % 2 == 0 else "even"
            self.browser_tree.insert("", "end", values=vals, tags=(tag,))
        self.status.config(text=f"Displaying {len(df)} of {len(self.df)} transistors.")

    def _sort_browser(self, col):
        if self._browser_sort_col == col:
            self._browser_sort_asc = not self._browser_sort_asc
        else:
            self._browser_sort_col = col; self._browser_sort_asc = True
        try:
            df_s = self.last_results.copy()
            df_s["_sort"] = pd.to_numeric(df_s[col], errors="coerce")
            df_s = df_s.sort_values("_sort" if df_s["_sort"].notna().any() else col,
                                    ascending=self._browser_sort_asc)
            self._fill_browser(df_s)
        except Exception:
            pass

    def _get_browser_selected_name(self):
        sel = self.browser_tree.selection()
        if not sel: return None
        return self.browser_tree.item(sel[0], "values")[0]

    def _browser_open_profile(self):
        name = self._get_browser_selected_name()
        if not name: messagebox.showinfo("Info","Select a transistor first."); return
        row = self.df[self.df["name"] == name]
        if row.empty: return
        self._show_profile(row.iloc[0])
        self.nb.select(self.tab_profile)

    def _browser_add_compare(self):
        sel = self.browser_tree.selection()
        if not sel: messagebox.showinfo("Info","Select transistors first."); return
        for s in sel:
            name = self.browser_tree.item(s,"values")[0]
            self._compare_add_name(name)
        self.nb.select(self.tab_compare)

    def _browser_export(self):
        sel = self.browser_tree.selection()
        if not sel: messagebox.showinfo("Info","Select transistors first."); return
        names = [self.browser_tree.item(s,"values")[0] for s in sel]
        sub = self.df[self.df["name"].isin(names)]
        self._do_export_df(sub)

    def _reload_db(self):
        self.df = load_full_database()
        self.last_results = self.df.copy()
        self._fill_browser(self.df)
        self._refresh_dropdowns()
        self.status.config(text=f"Reloaded. {len(self.df)} transistors.")
        # notify converter tab so device dropdowns stay current
        if _CONVERTERS_AVAILABLE and hasattr(self, "_converter_tab"):
            self._converter_tab.update_df(self.df)

    def _build_converter(self):
        """Build the ⚡ Converters tab using ConverterTab from converters/gui_tab.py."""
        p = self.tab_converter
        p.columnconfigure(0, weight=1)
        p.rowconfigure(0, weight=1)

        if not _CONVERTERS_AVAILABLE:
            msg = (
                "The 'converters/' package was not found.\n\n"
                "Make sure the converters/ folder is in the same directory as GUI.py:\n\n"
                "  szukaj/\n"
                "  ├── GUI.py\n"
                "  ├── szukaj.py\n"
                "  └── converters/\n"
                "      ├── __init__.py\n"
                "      ├── core.py\n"
                "      ├── formulas.py\n"
                "      ├── analysis.py\n"
                "      └── gui_tab.py"
            )
            ttk.Label(p, text=msg, font=("Consolas", 10),
                      foreground="#c0392b", justify="left").grid(
                row=0, column=0, padx=40, pady=40, sticky="nw")
            self._converter_tab = None
            return

        self._converter_tab = ConverterTab(p, df=self.df)

    # ==================================================================
    # SEARCH TAB  – używa preprocess_query ze szukaj.py
    # ==================================================================
    def _build_search(self):
        p = self.tab_search
        p.columnconfigure(0, weight=1)

        ttk.Label(p, text="🔎 Pandas Query Search", font=("Arial",14,"bold")
                  ).grid(row=0, column=0, sticky="w", padx=10, pady=(8,2))

        # --- quick filter bar (row 1) ---
        qf = ttk.LabelFrame(p, text=" Quick Filters (auto-AND combined) ", padding=8)
        qf.grid(row=1, column=0, sticky="ew", padx=10, pady=4)
        for ci in range(8): qf.columnconfigure(ci, weight=1 if ci % 2 == 1 else 0)

        self._qf_vars = {}
        quick_fields = [
            ("Name / fragment:", "name"),
            ("Category:",        "Category"),
            ("Manufacturer:",    "manufacturer"),
            ("V_abs_max ≥:",     "v_abs_max_ge"),
            ("I_abs_max ≥:",     "i_abs_max_ge"),
            ("I_cont ≥:",        "i_cont_ge"),
            ("Housing:",         "housing_type"),
            ("Technology:",      "technology"),
        ]
        for i, (lbl, key) in enumerate(quick_fields):
            r, c = divmod(i, 4)
            ttk.Label(qf, text=lbl, font=("Arial",9,"bold")).grid(row=r, column=c*2, padx=4, pady=3, sticky="w")
            var = tk.StringVar()
            e = ttk.Entry(qf, textvariable=var, font=("Consolas",9), width=14)
            e.grid(row=r, column=c*2+1, padx=4, pady=3, sticky="ew")
            e.bind("<Return>", lambda ev: self._run_search())
            self._qf_vars[key] = var

        # --- raw query (row 2) ---
        raw_frame = ttk.LabelFrame(p, text=" Raw Pandas Query (overrides Quick Filters) ", padding=6)
        raw_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=2)
        raw_frame.columnconfigure(0, weight=1)
        self._raw_query_var = tk.StringVar()
        raw_e = ttk.Entry(raw_frame, textvariable=self._raw_query_var, font=("Consolas",9))
        raw_e.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        raw_e.bind("<Return>", lambda e: self._run_search())
        ttk.Label(raw_frame, text='e.g.  v_abs_max >= 900 & manufacturer == "ROHM"  |  name == "C3M"',
                  font=("Arial",8), foreground="gray").grid(row=1, column=0, sticky="w", padx=4)

        # --- buttons (row 3) ---
        btn_row = ttk.Frame(p); btn_row.grid(row=3, column=0, sticky="ew", padx=10, pady=4)
        ttk.Button(btn_row, text="▶ Search",            command=self._run_search).pack(side="left", padx=4, ipady=3)
        ttk.Button(btn_row, text="❌ Clear",             command=self._clear_search).pack(side="left", padx=4, ipady=3)
        ttk.Button(btn_row, text="📋 Open Profile",      command=self._search_open_profile).pack(side="left", padx=8, ipady=3)
        ttk.Button(btn_row, text="📊 Add to Compare",    command=self._search_add_compare).pack(side="left", padx=4, ipady=3)
        ttk.Button(btn_row, text="📤 Export results",    command=self._search_export).pack(side="left", padx=4, ipady=3)
        self._search_count_lbl = ttk.Label(btn_row, text="", font=("Arial",9), foreground="gray")
        self._search_count_lbl.pack(side="left", padx=12)

        # --- results treeview (row 4) ---
        rf = ttk.Frame(p); rf.grid(row=4, column=0, sticky="nsew", padx=10, pady=4)
        p.rowconfigure(4, weight=1)
        rf.columnconfigure(0, weight=1); rf.rowconfigure(0, weight=1)

        res_cols = ("name","Category","manufacturer","v_abs_max","i_abs_max","i_cont",
                    "housing_type","r_th_cs","t_c_max","technology","author")
        self.search_tree = ttk.Treeview(rf, columns=res_cols, show="headings", selectmode="extended")
        res_labels = {"name":"Device Name","Category":"Category","manufacturer":"Manufacturer",
                      "v_abs_max":"V_abs_max [V]","i_abs_max":"I_abs_max [A]","i_cont":"I_cont [A]",
                      "housing_type":"Package","r_th_cs":"R_th_cs [K/W]",
                      "t_c_max":"T_c_max [°C]","technology":"Technology","author":"Author"}
        res_widths = {"name":220,"Category":90,"manufacturer":150,"v_abs_max":90,
                      "i_abs_max":90,"i_cont":80,"housing_type":90,
                      "r_th_cs":85,"t_c_max":75,"technology":100,"author":130}
        for c in res_cols:
            self.search_tree.heading(c, text=res_labels.get(c,c))
            self.search_tree.column(c, width=res_widths.get(c,100), minwidth=60, stretch=False)
        self.search_tree.tag_configure("odd",  background=CLR_ODD)
        self.search_tree.tag_configure("even", background=CLR_EVEN)
        self.search_tree.bind("<Double-1>", lambda e: self._search_open_profile())

        sy = ttk.Scrollbar(rf, orient="vertical",   command=self.search_tree.yview)
        sx = ttk.Scrollbar(rf, orient="horizontal",  command=self.search_tree.xview)
        self.search_tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.search_tree.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns"); sx.grid(row=1, column=0, sticky="ew")

    def _run_search(self):
        raw = self._raw_query_var.get().strip()
        if raw:
            q = preprocess_query(raw, self.df.columns)
        else:
            parts = []
            for key, var in self._qf_vars.items():
                val = var.get().strip()
                if not val: continue
                if key == "v_abs_max_ge":
                    try: parts.append(f"v_abs_max >= {float(val)}")
                    except: pass
                elif key == "i_abs_max_ge":
                    try: parts.append(f"i_abs_max >= {float(val)}")
                    except: pass
                elif key == "i_cont_ge":
                    try: parts.append(f"i_cont >= {float(val)}")
                    except: pass
                else:
                    parts.append(f'{key}.str.contains({val!r}, case=False, na=False)')
            q = " & ".join(parts) if parts else ""

        if not q:
            result = self.df
        else:
            try:
                result = self.df.query(q, engine="python")
            except Exception as e:
                messagebox.showerror("Query Error", str(e)); return

        self.last_results = result
        for r in self.search_tree.get_children(): self.search_tree.delete(r)
        cols = self.search_tree["columns"]
        for i, (_, row) in enumerate(result.iterrows()):
            vals = [self._cell_str(row.get(c, "")) for c in cols]
            tag = "odd" if i%2==0 else "even"
            self.search_tree.insert("","end",values=vals,tags=(tag,))
        self._search_count_lbl.config(text=f"{len(result)} result(s)")
        self.status.config(text=f"Search: {len(result)} of {len(self.df)} transistors.")

    def _clear_search(self):
        for v in self._qf_vars.values(): v.set("")
        self._raw_query_var.set("")
        for r in self.search_tree.get_children(): self.search_tree.delete(r)
        self._search_count_lbl.config(text="")
        self.last_results = self.df.copy()

    def _search_open_profile(self):
        sel = self.search_tree.selection()
        if not sel: messagebox.showinfo("Info","Select a transistor first."); return
        name = self.search_tree.item(sel[0],"values")[0]
        row = self.df[self.df["name"]==name]
        if row.empty: return
        self._show_profile(row.iloc[0])
        self.nb.select(self.tab_profile)

    def _search_add_compare(self):
        sel = self.search_tree.selection()
        if not sel: messagebox.showinfo("Info","Select transistors first."); return
        for s in sel:
            name = self.search_tree.item(s,"values")[0]
            self._compare_add_name(name)
        self.nb.select(self.tab_compare)

    def _search_export(self):
        sel = self.search_tree.selection()
        if sel:
            names = [self.search_tree.item(s,"values")[0] for s in sel]
            sub = self.df[self.df["name"].isin(names)]
        else:
            sub = self.last_results
        if sub.empty: messagebox.showinfo("Info","No results to export."); return
        self._do_export_df(sub)

    # ==================================================================
    # PROFILE TAB  – wyświetla display_transistor_profile jako GUI
    # ==================================================================
    def _build_profile(self):
        p = self.tab_profile
        p.columnconfigure(0, weight=1); p.rowconfigure(1, weight=1)

        tb = ttk.Frame(p, padding=(8,6,8,2)); tb.grid(row=0, column=0, sticky="ew")
        ttk.Label(tb, text="📋 Transistor Profile", font=("Arial",14,"bold")).pack(side="left")
        ttk.Button(tb, text="📋 Copy Selected Value", command=self._profile_copy_value).pack(side="right", padx=4)
        ttk.Button(tb, text="📋 Copy All (TSV)", command=self._profile_copy_all).pack(side="right", padx=4)
        ttk.Button(tb, text="📊 Add to Compare", command=self._profile_add_compare).pack(side="right", padx=4)
        ttk.Button(tb, text="✏️  Open in Editor", command=self._profile_open_editor).pack(side="right", padx=4)
        ttk.Button(tb, text="📤 Export this device", command=self._profile_export).pack(side="right", padx=4)

        pane = ttk.PanedWindow(p, orient="vertical")
        pane.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

        # Parameters table
        pf = ttk.LabelFrame(pane, text=" Parameters ", padding=6)
        pane.add(pf, weight=2)

        tv = ttk.Treeview(pf, columns=("Parameter","Value"), show="headings", height=20)
        tv.heading("Parameter", text="Parameter"); tv.heading("Value", text="Value")
        tv.column("Parameter", width=260, anchor="w"); tv.column("Value", width=600, anchor="w")
        sy = ttk.Scrollbar(pf, orient="vertical",   command=tv.yview)
        sx = ttk.Scrollbar(pf, orient="horizontal",  command=tv.xview)
        tv.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        tv.pack(side="top", fill="both", expand=True)
        sy.pack(side="right", fill="y"); sx.pack(side="bottom", fill="x")
        self._profile_tv  = tv
        self._profile_row = None

        # Charts panel – searchable combobox instead of flat button row
        self._profile_chart_frame = ttk.LabelFrame(pane, text=" 📈 Available Charts ", padding=6)
        pane.add(self._profile_chart_frame, weight=0)

        # Build chart selector widgets once; populate in _show_profile
        chart_sel_row = ttk.Frame(self._profile_chart_frame)
        chart_sel_row.pack(fill="x", pady=(0,4))
        ttk.Label(chart_sel_row, text="Chart:", font=("Arial",9,"bold")).pack(side="left", padx=(0,4))
        self._profile_chart_combo = ttk.Combobox(chart_sel_row, font=("Consolas",9),
                                                  state="readonly", width=55)
        self._profile_chart_combo.pack(side="left", padx=4)
        ttk.Button(chart_sel_row, text="📈 Open Chart",
                   command=self._profile_open_chart).pack(side="left", padx=6, ipady=2)

        self._profile_charts_map: dict = {}   # key -> curves list
        self._profile_chart_search_var = tk.StringVar()

        # Search box that filters combo values
        ttk.Label(chart_sel_row, text="Search:", font=("Arial",9)).pack(side="left", padx=(12,4))
        search_e = ttk.Entry(chart_sel_row, textvariable=self._profile_chart_search_var,
                             width=20, font=("Consolas",9))
        search_e.pack(side="left")

        def _filter_combo(*_):
            f = self._profile_chart_search_var.get().lower()
            filtered = [k for k in sorted(self._profile_charts_map.keys()) if f in k.lower()]
            self._profile_chart_combo["values"] = filtered
            if filtered and self._profile_chart_combo.get() not in filtered:
                self._profile_chart_combo.set(filtered[0])

        self._profile_chart_search_var.trace_add("write", _filter_combo)

    def _profile_open_chart(self):
        key = self._profile_chart_combo.get()
        if not key or key not in self._profile_charts_map:
            messagebox.showinfo("Charts","Select a chart first."); return
        curves = self._profile_charts_map[key]
        name = str(self._profile_row.get("name","")) if self._profile_row is not None else key
        open_chart_popup(self.root, f"{name} – {key}", curves, chart_key=key)

    def _show_profile(self, row):
        self._profile_row = row
        tv = self._profile_tv
        for r in tv.get_children(): tv.delete(r)

        CHART_NOTE = "[Curve data – click chart button below]"
        for key, meta in FIELD_META.items():
            val = row.get(key, None)
            if isinstance(val, (list, dict)):
                val_str = CHART_NOTE if (isinstance(val,list) and len(val)>0) or \
                                        (isinstance(val,dict) and len(val)>0) else "-"
            elif is_curve_field(key):
                val_str = CHART_NOTE
            else:
                try:
                    nan = pd.isna(val)
                except Exception:
                    nan = False
                val_str = "-" if nan or str(val).strip() in ("","nan","None") else str(val)
            tv.insert("","end", values=(meta["label"], val_str))

        # Rebuild charts combobox
        self._profile_charts_map = {}
        self._profile_chart_search_var.set("")

        jd, _ = load_json_for_name(str(row.get("name","")), self.df)
        if jd:
            charts = deep_search_charts(jd, output_folder=None, name_path="", found_charts={})
            if charts:
                for ck, series in charts.items():
                    self._profile_charts_map[ck] = [
                        (s["tj"] or ck, s["data"][0], s["data"][1]) for s in series]

        keys = sorted(self._profile_charts_map.keys())
        self._profile_chart_combo["values"] = keys
        if keys:
            self._profile_chart_combo.set(keys[0])
        else:
            self._profile_chart_combo.set("")

    def _profile_copy_value(self):
        sel = self._profile_tv.selection()
        if not sel: messagebox.showinfo("Copy","Select a row first."); return
        val = self._profile_tv.item(sel[0],"values")
        if len(val) >= 2:
            self.root.clipboard_clear(); self.root.clipboard_append(val[1])
            self.status.config(text=f"Copied: {val[1]}")

    def _profile_copy_all(self):
        rows  = self._profile_tv.get_children()
        lines = ["\t".join(str(v) for v in self._profile_tv.item(r,"values")) for r in rows]
        self.root.clipboard_clear(); self.root.clipboard_append("\n".join(lines))
        self.status.config(text=f"Copied {len(lines)} parameters.")

    def _profile_add_compare(self):
        if self._profile_row is None: return
        self._compare_add_name(str(self._profile_row.get("name","")))
        self.nb.select(self.tab_compare)

    def _profile_open_editor(self):
        """Otwiera plik JSON w edytorze systemowym – jak edit w szukaj.py."""
        if self._profile_row is None: return
        path = self._profile_row.get("_original_file_path")
        if not path or not os.path.exists(path):
            messagebox.showerror("Error","File path not found."); return
        try:
            if sys.platform == "win32":
                subprocess.run(["notepad.exe", path])
            elif sys.platform == "darwin":
                subprocess.run(["open","-w", path])
            else:
                for ed in ["xdg-open","gedit","nano"]:
                    import shutil
                    if shutil.which(ed):
                        subprocess.run([ed, path]); break
            # After editor closes – validate JSON
            with open(path,"r",encoding="utf-8") as f: json.load(f)
            messagebox.showinfo("OK","File saved and validated successfully.")
            self._reload_db()
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Syntax error after editing:\n{e}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _profile_export(self):
        if self._profile_row is None: return
        name = str(self._profile_row.get("name",""))
        sub  = self.df[self.df["name"]==name]
        if not sub.empty: self._do_export_df(sub)

    # ==================================================================
    # COMPARE TAB  – koszyk tranzystorów, wykresy obok siebie
    # ==================================================================
    def _build_compare(self):
        p = self.tab_compare
        p.columnconfigure(0, weight=1); p.rowconfigure(2, weight=1)

        ttk.Label(p, text="📊 Compare Transistors", font=("Arial",14,"bold")
                  ).grid(row=0, column=0, sticky="w", padx=10, pady=(8,2))

        # --- basket ---
        bf = ttk.LabelFrame(p, text=" Comparison Basket ", padding=6)
        bf.grid(row=1, column=0, sticky="ew", padx=10, pady=4)
        bf.columnconfigure(0, weight=1)

        basket_row = ttk.Frame(bf); basket_row.grid(row=0, column=0, sticky="ew")
        basket_row.columnconfigure(0, weight=1)

        self._compare_basket_var = tk.StringVar()
        self._compare_listbox = tk.Listbox(basket_row, listvariable=self._compare_basket_var,
                                           height=4, font=("Consolas",9), selectmode="extended")
        self._compare_listbox.grid(row=0, column=0, sticky="ew")
        sb = ttk.Scrollbar(basket_row, orient="vertical", command=self._compare_listbox.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._compare_listbox.configure(yscrollcommand=sb.set)
        self._compare_names: list[str] = []

        btn_row = ttk.Frame(bf); btn_row.grid(row=1, column=0, sticky="ew", pady=4)
        ttk.Button(btn_row, text="➕ Add by name", command=self._compare_add_dialog).pack(side="left",padx=4)
        ttk.Button(btn_row, text="➖ Remove selected", command=self._compare_remove).pack(side="left",padx=4)
        ttk.Button(btn_row, text="🗑 Clear all", command=self._compare_clear).pack(side="left",padx=4)
        ttk.Button(btn_row, text="📊 Compare (show charts)", command=self._compare_run).pack(side="left",padx=12,ipady=3)
        ttk.Button(btn_row, text="💾 Export comparison CSVs", command=self._compare_export_csv).pack(side="left",padx=4,ipady=3)

        # --- compare canvas (scrollable) ---
        cc = ttk.Frame(p); cc.grid(row=2, column=0, sticky="nsew", padx=10, pady=4)
        cc.columnconfigure(0, weight=1); cc.rowconfigure(0, weight=1)

        self._cmp_canvas = tk.Canvas(cc, background="white", highlightthickness=0)
        csy = ttk.Scrollbar(cc, orient="vertical",   command=self._cmp_canvas.yview)
        self._cmp_canvas.configure(yscrollcommand=csy.set)
        self._cmp_canvas.grid(row=0, column=0, sticky="nsew")
        csy.grid(row=0, column=1, sticky="ns")

        self._cmp_inner = ttk.Frame(self._cmp_canvas)
        self._cmp_win_id = self._cmp_canvas.create_window((0,0), window=self._cmp_inner, anchor="nw")

        def _inner_cfg(e):
            self._cmp_canvas.configure(scrollregion=self._cmp_canvas.bbox("all"))
        def _canvas_cfg(e):
            self._cmp_canvas.itemconfigure(self._cmp_win_id, width=e.width)
        self._cmp_inner.bind("<Configure>", _inner_cfg)
        self._cmp_canvas.bind("<Configure>", _canvas_cfg)

        def _mw(e): self._cmp_canvas.yview_scroll(int(-1*(e.delta/120)),"units")
        self._cmp_canvas.bind("<Enter>", lambda e: self._cmp_canvas.bind_all("<MouseWheel>",_mw))
        self._cmp_canvas.bind("<Leave>", lambda e: self._cmp_canvas.unbind_all("<MouseWheel>"))

        self._compare_chart_figs: list = []

    def _compare_add_name(self, name: str):
        name = name.strip()
        if name and name not in self._compare_names:
            self._compare_names.append(name)
            self._compare_listbox.insert("end", name)

    def _compare_add_dialog(self):
        names = sorted(self.df["name"].dropna().unique().tolist())
        win = tk.Toplevel(self.root); win.title("Add to Compare"); win.geometry("400x460")
        ttk.Label(win, text="Filter:", font=("Arial",9,"bold")).pack(anchor="w", padx=8, pady=(8,0))
        fv = tk.StringVar()
        fe = ttk.Entry(win, textvariable=fv, font=("Consolas",9)); fe.pack(fill="x", padx=8)
        lb = tk.Listbox(win, font=("Consolas",9), selectmode="extended"); lb.pack(fill="both",expand=True,padx=8,pady=4)
        def _filt(*_):
            lb.delete(0,"end")
            f = fv.get().lower()
            for n in names:
                if f in n.lower(): lb.insert("end",n)
        fv.trace_add("write", _filt); _filt()
        def _add():
            for i in lb.curselection():
                self._compare_add_name(lb.get(i))
            win.destroy()
        ttk.Button(win, text="➕ Add selected", command=_add).pack(pady=4, ipady=3)

    def _compare_remove(self):
        sel = list(self._compare_listbox.curselection())
        for i in reversed(sel):
            self._compare_names.pop(i)
            self._compare_listbox.delete(i)

    def _compare_clear(self):
        self._compare_names.clear()
        self._compare_listbox.delete(0,"end")
        for w in self._cmp_inner.winfo_children(): w.destroy()
        for fig in self._compare_chart_figs:
            try: plt.close(fig)
            except: pass
        self._compare_chart_figs.clear()

    def _compare_run(self):
        """Buduje tabelę parametrów i mini-wykresy obok siebie – jak compare w szukaj.py."""
        names = self._compare_names
        if len(names) < 2:
            messagebox.showwarning("Compare","Add at least 2 transistors to compare."); return

        for w in self._cmp_inner.winfo_children(): w.destroy()
        for fig in self._compare_chart_figs:
            try: plt.close(fig)
            except: pass
        self._compare_chart_figs.clear()

        inner = self._cmp_inner
        N = len(names)
        inner.columnconfigure(0, weight=1, minsize=160)
        for ci in range(1, N+1):
            inner.columnconfigure(ci, weight=3, minsize=160)

        CHART_H = 160

        # Header
        tk.Label(inner, text="Parameter", bg=CLR_HDR, fg="white",
                 font=("Arial",9,"bold"), anchor="w", padx=6
                 ).grid(row=0, column=0, sticky="nsew", padx=(0,1), pady=(0,1), ipady=4)
        for ci, n in enumerate(names):
            tk.Label(inner, text=n, bg=CLR_HDR, fg="white",
                     font=("Consolas",8), anchor="center", wraplength=200
                     ).grid(row=0, column=ci+1, sticky="nsew", padx=(0,1), pady=(0,1), ipady=4)

        # Load data
        rows_data  = {}
        charts_data = {}
        for n in names:
            r = self.df[self.df["name"]==n]
            rows_data[n]   = r.iloc[0] if not r.empty else {}
            jd, _          = load_json_for_name(n, self.df)
            charts_data[n] = deep_search_charts(jd, None,"",{}) if jd else {}

        # Find common chart keys
        all_chart_keys = set()
        for cd in charts_data.values():
            all_chart_keys.update(cd.keys())

        ri = 1
        for fi, (field, meta) in enumerate(FIELD_META.items()):
            is_curve = is_curve_field(field)
            bg = CLR_ODD if fi%2==0 else CLR_EVEN

            vals = []
            for n in names:
                row = rows_data[n]
                v = row.get(field, "") if hasattr(row,"get") else ""
                if isinstance(v,(list,dict)) or is_curve:
                    vals.append("[curve]")
                else:
                    vals.append(self._cell_str(v))

            unique_vals = set(v for v in vals if v not in ("-","[curve]"))
            rbg = CLR_DIFF if len(unique_vals) > 1 else bg

            tk.Label(inner, text=meta["label"], bg=rbg, fg="#2c3e50",
                     font=("Arial",8), anchor="w", padx=6
                     ).grid(row=ri, column=0, sticky="nsew", padx=(0,1), pady=(0,1), ipady=3)

            for ci, (n, vs) in enumerate(zip(names, vals)):
                cell_bg = rbg
                if is_curve:
                    # Szukaj odpowiednich serii
                    series = []
                    for ck, sl in charts_data[n].items():
                        if ck.startswith(field) or field.startswith(ck):
                            series = sl; break
                    if not series and field in charts_data[n]:
                        series = charts_data[n][field]

                    if series:
                        curves = [(s["tj"] or ck, s["data"][0], s["data"][1]) for s in series]
                        # Determine axis labels from chart key
                        xl, yl = _get_axis_labels(ck if series else field)
                        cell = tk.Frame(inner, bg=cell_bg, highlightbackground="#3498db",
                                        highlightthickness=1, cursor="hand2")
                        cell.grid(row=ri, column=ci+1, sticky="nsew", padx=(0,1), pady=(0,1))
                        fig = Figure(figsize=(2.0, CHART_H/96), dpi=96)
                        ax  = fig.add_subplot(111)
                        COLS = ['#2980b9','#e74c3c','#27ae60','#8e44ad','#e67e22']
                        for li, (lbl,xd,yd) in enumerate(curves):
                            ax.plot(xd,yd, color=COLS[li%5], linewidth=1.2, label=lbl)
                        ax.set_xlabel(xl, fontsize=5)
                        ax.set_ylabel(yl, fontsize=5)
                        ax.tick_params(labelsize=5); ax.grid(True,linestyle=':',alpha=0.4)
                        fig.tight_layout(pad=0.3)
                        fc = FigureCanvasTkAgg(fig, master=cell); fc.draw()
                        fc.get_tk_widget().pack(fill="both", expand=True, padx=2, pady=2)
                        self._compare_chart_figs.append(fig)
                        _ck = ck if series else field
                        def _click(ev, c=curves, t=f"{n} – {meta['label']}", k=_ck):
                            open_chart_popup(self.root, t, c, chart_key=k)
                        fc.mpl_connect("button_press_event", _click)
                        tk.Label(cell, text="🔍 click", font=("Arial",5,"italic"),
                                 bg=cell_bg, fg="#888").pack(side="bottom")
                        continue

                cell = tk.Frame(inner, bg=cell_bg, highlightbackground="#d0d7de",
                                highlightthickness=1)
                cell.grid(row=ri, column=ci+1, sticky="nsew", padx=(0,1), pady=(0,1))
                disp = vs if vs != "[curve]" else "—"
                tk.Label(cell, text=disp, font=("Consolas",8), bg=cell_bg,
                         fg="#2c3e50", anchor="center").pack(fill="both", expand=True, padx=3, pady=3)
            ri += 1

        self._cmp_canvas.update_idletasks()
        self._cmp_canvas.configure(scrollregion=self._cmp_canvas.bbox("all"))

    def _compare_export_csv(self):
        """Eksportuje CSV z porównania – tak jak compare_transistor_charts w szukaj.py."""
        names = self._compare_names
        if len(names) < 2:
            messagebox.showwarning("Compare","Add at least 2 transistors."); return

        out_dir = filedialog.askdirectory(title="Select output folder for comparison CSVs")
        if not out_dir: return

        all_charts = {}
        valid_names = []
        for n in names:
            jd, _ = load_json_for_name(n, self.df)
            if jd:
                all_charts[n] = deep_search_charts(jd, None, "", {})
                valid_names.append(n)

        if len(valid_names) < 2:
            messagebox.showerror("Error","Not enough valid transistors found."); return

        # Intersection of chart keys
        common = None
        for n in valid_names:
            ks = set(all_charts[n].keys())
            common = ks if common is None else common & ks
        common = sorted(list(common)) if common else []

        if not common:
            messagebox.showinfo("Info","No common chart keys found across selected transistors.")
            return

        exported = 0
        for ck in common:
            xl, yl = _get_axis_labels(ck)
            combined = {}
            for n in valid_names:
                for s in all_charts[n].get(ck,[]):
                    suf = s["tj"] or "_s"
                    combined[f"{n}{suf}_{xl.split('[')[0].strip()}"] = s["data"][0]
                    combined[f"{n}{suf}_{yl.split('[')[0].strip()}"] = s["data"][1]
            df_cmp = pd.DataFrame({k: pd.Series(v) for k,v in combined.items()})
            clean  = ck.replace(" ","_").replace("/","_")
            path   = os.path.join(out_dir, f"Comparison_{len(valid_names)}dev_{clean}.csv")
            try:
                df_cmp.to_csv(path, index=False, sep=";", encoding="utf-8-sig")
                exported += 1
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

        messagebox.showinfo("Done", f"Exported {exported} CSV file(s) to:\n{out_dir}")

    # ==================================================================
    # CREATE TAB  – formularz + build_structured_json z szukaj.py
    # ==================================================================
    def _build_create(self):
        p = self.tab_create
        p.columnconfigure(0, weight=1); p.rowconfigure(1, weight=1)

        ttk.Label(p, text="➕ Create New Transistor", font=("Arial",14,"bold")
                  ).grid(row=0, column=0, sticky="w", padx=10, pady=(8,2))

        outer = ttk.LabelFrame(p, text=" Specification Form ", padding=10)
        outer.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)
        outer.columnconfigure(0, weight=1); outer.rowconfigure(0, weight=1)

        cc = tk.Canvas(outer, borderwidth=0, highlightthickness=0)
        cs = ttk.Scrollbar(outer, orient="vertical", command=cc.yview)
        sf = ttk.Frame(cc)
        sf.bind("<Configure>", lambda e: cc.configure(scrollregion=cc.bbox("all")))
        cc.create_window((0,0), window=sf, anchor="nw")
        cc.configure(yscrollcommand=cs.set)
        cc.pack(side="left", fill="both", expand=True); cs.pack(side="right", fill="y")

        sf.columnconfigure(0, weight=0, minsize=200)
        sf.columnconfigure(1, weight=1, minsize=280)
        sf.columnconfigure(2, weight=0, minsize=200)
        sf.columnconfigure(3, weight=1, minsize=280)

        def _mw(e): cc.yview_scroll(int(-1*(e.delta/120)),"units")
        cc.bind("<Enter>", lambda e: cc.bind_all("<MouseWheel>",_mw))
        cc.bind("<Leave>", lambda e: cc.unbind_all("<MouseWheel>"))

        self._create_entries       = {}
        self._create_graph_data    = {}    # col -> list of rows or None
        self._create_graph_labels  = {}    # col -> ttk.Label for status

        # Helper: add greyed placeholder behaviour
        def _add_placeholder(entry, text):
            entry.insert(0, text); entry.config(foreground="gray")
            entry.placeholder = text
            def _fi(e):
                if entry.get() == text:
                    entry.delete(0, "end"); entry.config(foreground="black")
            def _fo(e):
                if not entry.get():
                    entry.insert(0, text); entry.config(foreground="gray")
            entry.bind("<FocusIn>", _fi); entry.bind("<FocusOut>", _fo)

        # Name field spanning full width
        ttk.Label(sf, text="Part Number (name):", font=("Arial",9,"bold")).grid(
            row=0, column=0, padx=5, pady=6, sticky="w")
        name_e = ttk.Entry(sf, font=("Consolas",10))
        name_e.grid(row=0, column=1, columnspan=3, padx=5, pady=6, sticky="ew")
        _add_placeholder(name_e, "Commercial part number of the transistor")
        self._create_entries["name"] = name_e

        # Category and v_abs_max first (needed for folder path)
        special = ["Category", "v_abs_max"]
        ri, ci = 1, 0
        for key in special:
            meta = FIELD_META.get(key, {"label": key, "desc": ""})
            ttk.Label(sf, text=f"{meta['label']}:", font=("Arial",9,"bold")).grid(
                row=ri, column=ci, padx=5, pady=5, sticky="w")
            ent = ttk.Entry(sf, font=("Consolas",10), width=14)
            ent.grid(row=ri, column=ci+1, padx=5, pady=5, sticky="ew")
            _add_placeholder(ent, meta.get("desc",""))
            self._create_entries[key] = ent
            ci += 2
        ri += 1; ci = 0

        simple_fields = [k for k in FIELD_META if not is_curve_field(k)]
        curve_fields  = [k for k in FIELD_META if is_curve_field(k)]

        # Simple scalar fields with greyed placeholders
        for key in simple_fields:
            if key in special: continue
            meta = FIELD_META.get(key, {"label": key, "desc": ""})
            col = ci % 4
            ttk.Label(sf, text=f"{meta['label']}:", font=("Arial",9)).grid(
                row=ri, column=col, padx=5, pady=3, sticky="w")
            ent = ttk.Entry(sf, font=("Consolas",10), width=14)
            ent.grid(row=ri, column=col+1, padx=5, pady=3, sticky="ew")
            _add_placeholder(ent, meta.get("desc",""))
            self._create_entries[key] = ent
            ci += 2
            if ci >= 4: ci = 0; ri += 1

        # Curve / graph fields with Add CSV button + status label
        if ri > 0 and ci > 0: ri += 1; ci = 0   # flush to new row
        ttk.Separator(sf, orient="horizontal").grid(
            row=ri, column=0, columnspan=4, sticky="ew", pady=(6,2))
        ri += 1
        ttk.Label(sf, text="Curve Data", font=("Arial",9,"bold"),
                  foreground="#2c3e50").grid(row=ri, column=0, columnspan=4,
                  sticky="w", padx=5, pady=(0,4))
        ri += 1; ci = 0

        for key in curve_fields:
            meta = FIELD_META.get(key, {"label": key, "desc": ""})
            col = ci % 4
            ttk.Label(sf, text=f"{meta['label']}:", font=("Arial",9)).grid(
                row=ri, column=col, padx=5, pady=3, sticky="w")
            frm = ttk.Frame(sf)
            frm.grid(row=ri, column=col+1, padx=5, pady=3, sticky="ew")
            self._create_graph_data[key]  = None
            btn = ttk.Button(frm, text="📁 Add curves…",
                             command=lambda k=key: self._create_import_csv(k))
            btn.pack(side="left")
            lbl = ttk.Label(frm, text=f"No dataset  ({meta.get('desc','')})",
                            font=("Arial",8,"italic"), foreground="gray")
            lbl.pack(side="left", padx=6, fill="x", expand=True)
            self._create_graph_labels[key] = lbl
            ci += 2
            if ci >= 4: ci = 0; ri += 1

        bf = ttk.Frame(p, padding=(0,6,0,0)); bf.grid(row=2, column=0, sticky="ew", padx=10)
        ttk.Button(bf, text="💾 Save New Transistor",
                   command=self._create_save).pack(side="left", padx=4, ipady=4)
        ttk.Button(bf, text="🧹 Clear Form",
                   command=self._create_clear).pack(side="left", padx=4, ipady=4)

    def _create_import_csv(self, col: str):
        fp = filedialog.askopenfilename(
            title=f"Select CSV for {col}",
            filetypes=[("CSV","*.csv"),("Text","*.txt"),("All","*.*")])
        if not fp: return
        try:
            try:   df_c = pd.read_csv(fp, sep=None, engine="python")
            except: df_c = pd.read_csv(fp, sep=";")
            rows = df_c.dropna().values.tolist()
            self._create_graph_data[col] = rows
            self._create_graph_labels[col].config(
                text=f"✅ {os.path.basename(fp)}  ({len(rows)} pts)",
                foreground=CLR_GREEN, font=("Arial",8,"bold"))
        except Exception as e:
            messagebox.showerror("CSV Error", str(e))

    def _create_save(self):
        def _get(e):
            v = e.get().strip()
            return "" if hasattr(e, "placeholder") and v == e.placeholder else v

        flat = {k: _get(e) for k, e in self._create_entries.items()}

        name = flat.get("name", "")
        cat  = flat.get("Category", "")
        vabs = flat.get("v_abs_max", "")
        if not name or not cat:
            messagebox.showerror("Error","'name' and 'Category' are required."); return
        if cat not in TECH_CATEGORIES:
            messagebox.showerror("Error",f"Category must be one of: {TECH_CATEGORIES}"); return

        flat["creation_date"] = datetime.date.today().strftime("%Y-%m-%d")
        flat["last_modified"] = flat["creation_date"]

        structured = build_structured_json(flat)

        # Inject curve data collected via CSV imports
        for k, rows in self._create_graph_data.items():
            if rows is not None:
                structured[k] = rows

        vnum = "".join(c for c in vabs if c.isdigit()) or "Unsorted"
        dest_dir = os.path.join(_THIS_DIR, cat, f"{vnum}V")
        os.makedirs(dest_dir, exist_ok=True)
        clean_fn = "".join(c if c.isalnum() or c in('_','-') else '_' for c in name) + ".json"
        fp = os.path.join(dest_dir, clean_fn)

        if os.path.exists(fp):
            if not messagebox.askyesno("Overwrite?",f"'{clean_fn}' already exists. Overwrite?"): return

        try:
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(structured, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Success", f"Saved to:\n{fp}")
            self._reload_db()
            self._create_clear()
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _create_clear(self):
        for e in self._create_entries.values():
            e.delete(0, "end")
            if hasattr(e, "placeholder"):
                e.insert(0, e.placeholder); e.config(foreground="gray")
        for k in list(self._create_graph_data.keys()):
            self._create_graph_data[k] = None
            meta = FIELD_META.get(k, {"desc": "data"})
            if k in self._create_graph_labels:
                self._create_graph_labels[k].config(
                    text=f"No dataset  ({meta.get('desc','')})",
                    foreground="gray", font=("Arial",8,"italic"))

    # ==================================================================
    # EDIT TAB  – identyczny formularz co CREATE, wstępnie wypełniony danymi
    # ==================================================================
    def _build_edit(self):
        p = self.tab_edit
        p.columnconfigure(0, weight=1); p.rowconfigure(2, weight=1)

        ttk.Label(p, text="✏️  Edit Transistor", font=("Arial",14,"bold")
                  ).grid(row=0, column=0, sticky="w", padx=10, pady=(8,2))

        # Selector row
        sel_f = ttk.LabelFrame(p, text=" Select transistor ", padding=10)
        sel_f.grid(row=1, column=0, sticky="ew", padx=10, pady=4)
        sel_f.columnconfigure(1, weight=1)

        ttk.Label(sel_f, text="Name:", font=("Arial",9,"bold")).grid(
            row=0, column=0, padx=5, sticky="w")
        self._edit_combo = ttk.Combobox(sel_f, font=("Consolas",9), state="readonly", width=50)
        self._edit_combo.grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(sel_f, text="📂 Load into form",
                   command=self._edit_load).grid(row=0, column=2, padx=6, ipady=3)

        # Form (same layout as Create)
        outer = ttk.LabelFrame(p, text=" Specification Form ", padding=10)
        outer.grid(row=2, column=0, sticky="nsew", padx=10, pady=4)
        outer.columnconfigure(0, weight=1); outer.rowconfigure(0, weight=1)

        cc = tk.Canvas(outer, borderwidth=0, highlightthickness=0)
        cs = ttk.Scrollbar(outer, orient="vertical", command=cc.yview)
        sf = ttk.Frame(cc)
        sf.bind("<Configure>", lambda e: cc.configure(scrollregion=cc.bbox("all")))
        cc.create_window((0,0), window=sf, anchor="nw")
        cc.configure(yscrollcommand=cs.set)
        cc.pack(side="left", fill="both", expand=True); cs.pack(side="right", fill="y")

        sf.columnconfigure(0, weight=0, minsize=200)
        sf.columnconfigure(1, weight=1, minsize=280)
        sf.columnconfigure(2, weight=0, minsize=200)
        sf.columnconfigure(3, weight=1, minsize=280)

        def _mw(e): cc.yview_scroll(int(-1*(e.delta/120)),"units")
        cc.bind("<Enter>", lambda e: cc.bind_all("<MouseWheel>",_mw))
        cc.bind("<Leave>", lambda e: cc.unbind_all("<MouseWheel>"))

        self._edit_entries      = {}
        self._edit_graph_data   = {}
        self._edit_graph_labels = {}

        # Name field
        ttk.Label(sf, text="Part Number (name):", font=("Arial",9,"bold")).grid(
            row=0, column=0, padx=5, pady=6, sticky="w")
        name_e = ttk.Entry(sf, font=("Consolas",10))
        name_e.grid(row=0, column=1, columnspan=3, padx=5, pady=6, sticky="ew")
        self._edit_entries["name"] = name_e

        special = ["Category", "v_abs_max"]
        ri, ci = 1, 0
        for key in special:
            meta = FIELD_META.get(key, {"label": key, "desc": ""})
            ttk.Label(sf, text=f"{meta['label']}:", font=("Arial",9,"bold")).grid(
                row=ri, column=ci, padx=5, pady=5, sticky="w")
            ent = ttk.Entry(sf, font=("Consolas",10), width=14)
            ent.grid(row=ri, column=ci+1, padx=5, pady=5, sticky="ew")
            self._edit_entries[key] = ent
            ci += 2
        ri += 1; ci = 0

        simple_fields = [k for k in FIELD_META if not is_curve_field(k)]
        curve_fields  = [k for k in FIELD_META if is_curve_field(k)]

        for key in simple_fields:
            if key in special: continue
            meta = FIELD_META.get(key, {"label": key, "desc": ""})
            col = ci % 4
            ttk.Label(sf, text=f"{meta['label']}:", font=("Arial",9)).grid(
                row=ri, column=col, padx=5, pady=3, sticky="w")
            ent = ttk.Entry(sf, font=("Consolas",10), width=14)
            ent.grid(row=ri, column=col+1, padx=5, pady=3, sticky="ew")
            self._edit_entries[key] = ent
            ci += 2
            if ci >= 4: ci = 0; ri += 1

        if ri > 0 and ci > 0: ri += 1; ci = 0
        ttk.Separator(sf, orient="horizontal").grid(
            row=ri, column=0, columnspan=4, sticky="ew", pady=(6,2))
        ri += 1
        ttk.Label(sf, text="Curve Data", font=("Arial",9,"bold"),
                  foreground="#2c3e50").grid(row=ri, column=0, columnspan=4,
                  sticky="w", padx=5, pady=(0,4))
        ri += 1; ci = 0

        for key in curve_fields:
            meta = FIELD_META.get(key, {"label": key, "desc": ""})
            col = ci % 4
            ttk.Label(sf, text=f"{meta['label']}:", font=("Arial",9)).grid(
                row=ri, column=col, padx=5, pady=3, sticky="w")
            frm = ttk.Frame(sf)
            frm.grid(row=ri, column=col+1, padx=5, pady=3, sticky="ew")
            self._edit_graph_data[key] = None
            btn = ttk.Button(frm, text="📁 Replace curves…",
                             command=lambda k=key: self._edit_import_csv(k))
            btn.pack(side="left")
            lbl = ttk.Label(frm, text=f"(unchanged)  {meta.get('desc','')}",
                            font=("Arial",8,"italic"), foreground="gray")
            lbl.pack(side="left", padx=6, fill="x", expand=True)
            self._edit_graph_labels[key] = lbl
            ci += 2
            if ci >= 4: ci = 0; ri += 1

        # Buttons bar
        bf = ttk.Frame(p, padding=(0,6,0,0)); bf.grid(row=3, column=0, sticky="ew", padx=10)
        ttk.Button(bf, text="💾 Save Changes",
                   command=self._edit_save).pack(side="left", padx=4, ipady=4)
        ttk.Button(bf, text="🧹 Clear Form",
                   command=self._edit_clear).pack(side="left", padx=4, ipady=4)
        ttk.Button(bf, text="🔄 Reload from disk",
                   command=self._edit_load).pack(side="left", padx=12, ipady=4)
        self._edit_status = ttk.Label(bf, text="", foreground="gray", font=("Arial",9))
        self._edit_status.pack(side="left", padx=12)

        self._edit_current_path: str | None = None
        self._edit_current_json: dict | None = None
        self._refresh_dropdowns()

    def _edit_load(self):
        name = self._edit_combo.get()
        if not name: messagebox.showinfo("Info","Select a transistor."); return
        jd, path = load_json_for_name(name, self.df)
        if not path:
            messagebox.showerror("Error",f"JSON file not found for '{name}'."); return

        self._edit_current_path = path
        self._edit_current_json = jd

        # Flatten JSON for scalar fields (same logic as load_full_database)
        flat = {}
        for key, value in jd.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    if isinstance(v, dict) and 'value' in v:
                        flat[f"{key}_{k}"] = str(v['value'])
                    elif not isinstance(v, (dict, list)):
                        flat[f"{key}_{k}"] = str(v)
            elif not isinstance(value, list):
                flat[key] = str(value) if value is not None else ""

        # Populate scalar entries
        for key, ent in self._edit_entries.items():
            ent.delete(0, "end")
            val = flat.get(key, "")
            if val and val not in ("None","nan"):
                ent.insert(0, val)

        # Reset curve labels to show current state from JSON
        for key in self._edit_graph_data:
            self._edit_graph_data[key] = None   # None = keep existing in JSON
            existing = jd.get(key)
            if existing and isinstance(existing, list) and len(existing) > 0:
                n_pts = len(existing[0]) if isinstance(existing[0], list) else len(existing)
                self._edit_graph_labels[key].config(
                    text=f"✅ existing data ({n_pts} pts) – click to replace",
                    foreground=CLR_GREEN, font=("Arial",8,"bold"))
            else:
                self._edit_graph_labels[key].config(
                    text="(no data) – click to add curves",
                    foreground="gray", font=("Arial",8,"italic"))

        self._edit_status.config(text=f"Loaded: {os.path.basename(path)}", foreground="gray")

    def _edit_import_csv(self, col: str):
        fp = filedialog.askopenfilename(
            title=f"Select CSV for {col}",
            filetypes=[("CSV","*.csv"),("Text","*.txt"),("All","*.*")])
        if not fp: return
        try:
            try:   df_c = pd.read_csv(fp, sep=None, engine="python")
            except: df_c = pd.read_csv(fp, sep=";")
            rows = df_c.dropna().values.tolist()
            self._edit_graph_data[col] = rows
            self._edit_graph_labels[col].config(
                text=f"✅ NEW: {os.path.basename(fp)}  ({len(rows)} pts)",
                foreground="#e67e22", font=("Arial",8,"bold"))
        except Exception as e:
            messagebox.showerror("CSV Error", str(e))

    def _edit_save(self):
        if not self._edit_current_path or not self._edit_current_json:
            messagebox.showinfo("Info","Load a transistor first."); return

        # Read scalar values from form entries
        flat = {k: e.get().strip() for k, e in self._edit_entries.items()}
        name = flat.get("name","")
        cat  = flat.get("Category","")
        if not name or not cat:
            messagebox.showerror("Error","'name' and 'Category' are required."); return
        if cat not in TECH_CATEGORIES:
            messagebox.showerror("Error",f"Category must be one of: {TECH_CATEGORIES}"); return

        flat["last_modified"] = datetime.date.today().strftime("%Y-%m-%d")

        # Start from existing JSON, update scalar fields
        updated = dict(self._edit_current_json)
        # Apply flat scalar values back – prefer root keys, also handle nested
        for key, val in flat.items():
            if not val: continue
            if key in updated:
                updated[key] = val
            else:
                # Try to set in nested structure
                parts = key.split("_", 1)
                if len(parts) == 2 and parts[0] in updated and isinstance(updated[parts[0]], dict):
                    if parts[1] in updated[parts[0]]:
                        v_node = updated[parts[0]][parts[1]]
                        if isinstance(v_node, dict) and 'value' in v_node:
                            updated[parts[0]][parts[1]]['value'] = val
                        else:
                            updated[parts[0]][parts[1]] = val
                    else:
                        updated[key] = val
                else:
                    updated[key] = val

        # Apply new curve data where provided
        for k, rows in self._edit_graph_data.items():
            if rows is not None:
                updated[k] = rows

        pretty = json.dumps(updated, indent=4, ensure_ascii=False)
        try:
            with open(self._edit_current_path, "w", encoding="utf-8") as f:
                f.write(pretty)
        except Exception as e:
            messagebox.showerror("Save Error", str(e)); return

        self._edit_current_json = updated
        self._edit_status.config(
            text=f"✅ Saved  {datetime.datetime.now().strftime('%H:%M:%S')}",
            foreground=CLR_GREEN)
        self._reload_db()
        messagebox.showinfo("Saved", f"Saved to:\n{self._edit_current_path}")

    def _edit_clear(self):
        for ent in self._edit_entries.values(): ent.delete(0, "end")
        for k in list(self._edit_graph_data.keys()):
            self._edit_graph_data[k] = None
            self._edit_graph_labels[k].config(
                text="(unchanged)", foreground="gray", font=("Arial",8,"italic"))
        self._edit_current_path = None
        self._edit_current_json = None
        self._edit_status.config(text="", foreground="gray")

    # ==================================================================
    # IMPORT TAB  – JSON, PLECS XML (jak szukaj.py)
    # ==================================================================
    def _build_import(self):
        p = self.tab_import
        p.columnconfigure(0, weight=1); p.rowconfigure(2, weight=1)

        ttk.Label(p, text="📥 Import", font=("Arial",14,"bold")
                  ).grid(row=0, column=0, sticky="w", padx=10, pady=(8,2))

        # JSON import
        jf = ttk.LabelFrame(p, text=" Import JSON file (import_ready_json_file) ", padding=10)
        jf.grid(row=1, column=0, sticky="ew", padx=10, pady=4)
        jf.columnconfigure(1, weight=1)

        self._import_json_path = tk.StringVar()
        ttk.Label(jf, text="JSON file:", font=("Arial",9,"bold")).grid(row=0,column=0,padx=5,sticky="w")
        ttk.Entry(jf, textvariable=self._import_json_path, font=("Consolas",9), width=60
                  ).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(jf, text="📂 Browse", command=lambda: self._import_json_path.set(
            filedialog.askopenfilename(filetypes=[("JSON","*.json")]))).grid(row=0,column=2,padx=4)
        ttk.Button(jf, text="✅ Import JSON", command=self._import_json).grid(row=1,column=0,columnspan=3,pady=6,ipady=3)

        # PLECS XML import
        xf = ttk.LabelFrame(p, text=" Import PLECS XML (import_plecs_xml) ", padding=10)
        xf.grid(row=2, column=0, sticky="ew", padx=10, pady=4)
        xf.columnconfigure(1, weight=1)

        self._import_sw_path  = tk.StringVar()
        self._import_di_path  = tk.StringVar()
        ttk.Label(xf, text="Switch XML:", font=("Arial",9,"bold")).grid(row=0,column=0,padx=5,sticky="w")
        ttk.Entry(xf, textvariable=self._import_sw_path, font=("Consolas",9), width=60
                  ).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(xf, text="📂", command=lambda: self._import_sw_path.set(
            filedialog.askopenfilename(filetypes=[("XML","*.xml")]))).grid(row=0,column=2,padx=4)

        ttk.Label(xf, text="Diode XML (opt):", font=("Arial",9,"bold")).grid(row=1,column=0,padx=5,sticky="w")
        ttk.Entry(xf, textvariable=self._import_di_path, font=("Consolas",9), width=60
                  ).grid(row=1, column=1, padx=5, sticky="ew")
        ttk.Button(xf, text="📂", command=lambda: self._import_di_path.set(
            filedialog.askopenfilename(filetypes=[("XML","*.xml")]))).grid(row=1,column=2,padx=4)

        # Category / voltage for PLECS import
        cf2 = ttk.Frame(xf); cf2.grid(row=2, column=0, columnspan=3, sticky="ew", pady=4)
        ttk.Label(cf2, text="Category:", font=("Arial",9,"bold")).pack(side="left", padx=5)
        self._import_plecs_cat = ttk.Combobox(cf2, values=TECH_CATEGORIES, width=14, state="readonly")
        self._import_plecs_cat.set("SiC-MOSFET"); self._import_plecs_cat.pack(side="left")
        ttk.Label(cf2, text="V_abs_max:", font=("Arial",9,"bold")).pack(side="left", padx=(12,2))
        self._import_plecs_v   = ttk.Entry(cf2, width=8, font=("Consolas",9))
        self._import_plecs_v.pack(side="left")
        ttk.Button(xf, text="✅ Import PLECS XML", command=self._import_plecs
                   ).grid(row=3, column=0, columnspan=3, pady=6, ipady=3)

        # Log
        lf = ttk.LabelFrame(p, text=" Log ", padding=6)
        lf.grid(row=3, column=0, sticky="nsew", padx=10, pady=4)
        p.rowconfigure(3, weight=1)
        self._import_log = tk.Text(lf, font=("Consolas",9), state="disabled", height=8, wrap="word")
        self._import_log.pack(fill="both", expand=True)

    def _import_log_write(self, msg):
        self._import_log.config(state="normal")
        self._import_log.insert("end", msg+"\n")
        self._import_log.see("end")
        self._import_log.config(state="disabled")

    def _import_json(self):
        path = self._import_json_path.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showerror("Error","Select a valid JSON file."); return
        try:
            with open(path,"r",encoding="utf-8") as f: data = json.load(f)
            name = data.get("name","").strip()
            if not name: raise ValueError("JSON missing 'name' field.")
            dtype = str(data.get("type", data.get("technology","SiC-MOSFET")))
            cat = "SiC-MOSFET"
            for tc in TECH_CATEGORIES:
                if tc.upper() in dtype.upper(): cat = tc; break
            vabs = str(data.get("v_abs_max","")).strip()
            vnum = str(int(float(vabs))) if vabs.replace('.','',1).isdigit() else "Unsorted"
            dest = os.path.join(_THIS_DIR, cat, f"{vnum}V")
            os.makedirs(dest, exist_ok=True)
            fn = "".join(c if c.isalnum() or c in('_','-') else '_' for c in name)+".json"
            fp = os.path.join(dest, fn)
            with open(fp,"w",encoding="utf-8") as f: json.dump(data,f,indent=4,ensure_ascii=False)
            self._import_log_write(f"[OK] Imported '{name}' → {fp}")
            self._reload_db()
        except Exception as e:
            self._import_log_write(f"[ERROR] {e}")
            messagebox.showerror("Import Error", str(e))

    def _import_plecs(self):
        sw  = self._import_sw_path.get().strip()
        di  = self._import_di_path.get().strip()
        cat = self._import_plecs_cat.get()
        v   = self._import_plecs_v.get().strip()

        if not sw or not os.path.exists(sw):
            messagebox.showerror("Error","Select a valid switch XML file."); return

        PLECS_NS_URI = "http://www.plexim.com/xml/semiconductors/"
        ns = {"p": PLECS_NS_URI}

        def _get_partnumber(path):
            try:
                tree = ET.parse(path)
                pkg  = tree.getroot().find("p:Package", ns)
                return pkg.attrib.get("partnumber","Unknown") if pkg is not None else "Unknown"
            except Exception:
                return "Unknown"

        name = _get_partnumber(sw)
        vnum = "".join(c for c in v if c.isdigit()) or "Unsorted"
        out  = os.path.join(_THIS_DIR, cat, f"{vnum}V")
        os.makedirs(out, exist_ok=True)

        try:
            jdata = {"name": name, "type": cat, "technology": cat,
                     "v_abs_max": v, "manufacturer": "", "author": "PLECS import"}
            if di and os.path.exists(di):
                di_name = _get_partnumber(di)
                jdata["diode_source_file"] = di_name

            fn = "".join(c if c.isalnum() or c in('_','-') else '_' for c in name)+".json"
            fp = os.path.join(out, fn)
            with open(fp,"w",encoding="utf-8") as f: json.dump(jdata,f,indent=4,ensure_ascii=False)
            self._import_log_write(f"[OK] Created skeleton JSON for '{name}' → {fp}")
            self._import_log_write("     Use ✏️ Edit to fill in the remaining fields.")
            self._reload_db()
        except Exception as e:
            self._import_log_write(f"[ERROR] {e}")
            messagebox.showerror("Import Error",str(e))

    # ==================================================================
    # EXPORT TAB  – export_folder_structure + export_plecs_xml z szukaj.py
    # ==================================================================
    def _build_export(self):
        p = self.tab_export
        p.columnconfigure(0, weight=1); p.rowconfigure(3, weight=1)

        ttk.Label(p, text="📤 Export", font=("Arial",14,"bold")
                  ).grid(row=0, column=0, sticky="w", padx=10, pady=(8,2))

        # Device selector
        sf = ttk.LabelFrame(p, text=" Select transistor(s) ", padding=10)
        sf.grid(row=1, column=0, sticky="ew", padx=10, pady=4)
        sf.columnconfigure(1, weight=1)

        ttk.Label(sf, text="Transistor:", font=("Arial",9,"bold")).grid(row=0,column=0,padx=5,sticky="w")
        self._export_combo = ttk.Combobox(sf, font=("Consolas",9), state="readonly", width=50)
        self._export_combo.grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Label(sf, text="(or use Browser/Search to select multiple)",
                  font=("Arial",8), foreground="gray").grid(row=1,column=0,columnspan=2,sticky="w",padx=5)

        # Format
        ff = ttk.LabelFrame(p, text=" Export Format ", padding=10)
        ff.grid(row=2, column=0, sticky="ew", padx=10, pady=4)
        self._export_fmt = tk.StringVar(value="json")
        for fmt, lbl in [("json","📄 JSON + chart CSVs"),
                         ("csv","📊 CSV + chart CSVs"),
                         ("plecs","🔧 PLECS XML (switch + diode)")]:
            ttk.Radiobutton(ff, text=lbl, variable=self._export_fmt, value=fmt).pack(anchor="w", pady=2)

        ttk.Button(p, text="📤 Export", command=self._export_run,
                   padding=(20,6)).grid(row=2, column=0, sticky="e", padx=14, pady=4)

        # Log
        lf = ttk.LabelFrame(p, text=" Export Log ", padding=6)
        lf.grid(row=3, column=0, sticky="nsew", padx=10, pady=4)
        self._export_log = tk.Text(lf, font=("Consolas",9), state="disabled", height=14, wrap="word")
        self._export_log.pack(fill="both", expand=True)

        self._refresh_dropdowns()

    def _export_log_write(self, msg):
        self._export_log.config(state="normal")
        self._export_log.insert("end", msg+"\n")
        self._export_log.see("end")
        self._export_log.config(state="disabled")

    def _export_run(self):
        name = self._export_combo.get()
        if not name: messagebox.showinfo("Info","Select a transistor."); return
        sub  = self.df[self.df["name"]==name]
        if sub.empty: messagebox.showerror("Error",f"'{name}' not found."); return
        self._do_export_df(sub, fmt_override=self._export_fmt.get())

    def _do_export_df(self, sub: pd.DataFrame, fmt_override=None):
        fmt = fmt_override or self._export_fmt.get() if hasattr(self,"_export_fmt") else "json"

        if fmt == "plecs":
            out = filedialog.askdirectory(title="Select output folder for PLECS XML")
            if not out: return
            ok = 0
            for _, row in sub.iterrows():
                src = row.get("_original_file_path")
                if src and os.path.isfile(src):
                    if export_plecs_xml(src, out):
                        ok += 1
                        msg = f"[OK] {row.get('name','?')}"
                    else:
                        msg = f"[SKIP] {row.get('name','?')} – no channel data"
                    try: self._export_log_write(msg)
                    except: pass
            try: self._export_log_write(f"\nExported {ok}/{len(sub)} PLECS XML files to {out}")
            except: pass
            messagebox.showinfo("Done",f"Exported {ok}/{len(sub)} PLECS XML files.")
        else:
            fmt_choice = fmt if fmt in ("json","csv") else "json"
            try:
                export_folder_structure(sub, data_format=fmt_choice)
                try:
                    self._export_log_write(f"[OK] export_folder_structure({fmt_choice}) done for {len(sub)} transistors.")
                except: pass
                messagebox.showinfo("Done",f"Exported {len(sub)} transistors to Exported_Transistors/")
            except Exception as e:
                messagebox.showerror("Export Error",str(e))

    # ==================================================================
    # SHARED HELPERS
    # ==================================================================
    def _refresh_dropdowns(self):
        names = sorted(self.df["name"].dropna().unique().tolist())
        if hasattr(self, "_edit_combo"):
            self._edit_combo["values"] = names
        if hasattr(self, "_export_combo"):
            self._export_combo["values"] = names


# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app  = TransistorGUI(root)
    root.mainloop()