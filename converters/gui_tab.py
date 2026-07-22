"""
converters/gui_tab.py
---------------------
Topology Calculator tab matching the reference transistordatabase GUI
(transistordatabase/gui/gui.py) as closely as possible within Tkinter.

Structure:
  Left panel  – scalars (P_out, Vin, Vout, Freq, Zeta, T_heatsink,
                          Rth_heatsink) + gate drive (Vg_on, Rg_on, Rg_off)
                         + topology selector + device selectors
  Right panel – 3 independent plot columns, each with:
                  • Line/Contour selector
                  • x-Axis combobox
                  • y-Axis combobox  (= metric in Line; sweep axis in Contour)
                  • z-Axis combobox  (= metric in Contour; hidden in Line)
                  • embedded matplotlib figure + NavigationToolbar

Range fields (min/max) for each variable are placed below the scalars,
matching the reference "Output Power min/max", "Vin min/max" etc.

Usage in GUI.py:
    from converters.gui_tab import ConverterTab
    tab = ttk.Frame(self.nb)
    self.nb.add(tab, text="⚡ Converters")
    ConverterTab(tab, df=self.df)
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np

from .core import ConverterDevice
from .analysis import (
    ConverterParams, compute, AXIS_VARS, METRICS, TOPOLOGIES
)

# ── Topology display labels (match reference exactly) ──────────────────────
TOPO_LABELS = {
    "boost":      "Boost-Converter",
    "buck":       "Buck-Converter",
    "buck_boost": "Buck-Boost-Converter",
}
TOPO_FROM_LABEL = {v: k for k, v in TOPO_LABELS.items()}

CLR_GREEN = "#27ae60"
CLR_RED   = "#e74c3c"
CLR_WARN  = "#e67e22"


class ConverterTab:
    """Builds the full Topology Calculator UI inside parent_frame."""

    def __init__(self, parent: tk.Widget, df=None):
        self.parent = parent
        self.df = df
        self._devices: dict[str, ConverterDevice] = {}
        self._plot_threads: list = []
        self._scroll_canvas: tk.Canvas | None = None

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        # ── Full-window scrollable canvas (controls + plots scroll together) ──
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical",
                                  command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._scroll_canvas = canvas

        content = ttk.Frame(canvas)
        content.columnconfigure(0, weight=1)
        content_id = canvas.create_window((0, 0), window=content, anchor="nw")

        def _update_scroll_region(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _sync_width(event):
            canvas.itemconfigure(content_id, width=event.width)

        content.bind("<Configure>", _update_scroll_region)
        canvas.bind("<Configure>", _sync_width)

        # Bind mousewheel only while cursor is over this canvas
        canvas.bind("<Enter>", lambda _: canvas.bind_all(
            "<MouseWheel>", self._on_mousewheel))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))

        top = ttk.Frame(content)
        bottom = ttk.Frame(content)
        top.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 3))
        bottom.grid(row=1, column=0, sticky="ew", padx=6, pady=(3, 6))
        top.columnconfigure(0, weight=1)
        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)

        self._build_left(top)
        self._build_right(bottom)

    def _on_mousewheel(self, event):
        if self._scroll_canvas is not None:
            self._scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ──────────────────────────────────────────────────────────────────────
    # LEFT PANEL
    # ──────────────────────────────────────────────────────────────────────

    def _build_left(self, p: tk.Widget):
        p.columnconfigure(0, weight=1)

        # ── Topology ──
        tf = ttk.LabelFrame(p, text=" Topology ", padding=6)
        tf.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
        tf.columnconfigure(1, weight=1)
        self._topo_var = tk.StringVar(value="Buck-Boost-Converter")
        ttk.Label(tf, text="Topology:").grid(row=0, column=0, sticky="w", padx=4)
        ttk.Combobox(tf, textvariable=self._topo_var,
                     values=list(TOPO_LABELS.values()),
                     state="readonly", font=("Arial", 9)).grid(
            row=0, column=1, sticky="ew", padx=4, pady=3)

        # ── Devices ──
        df_frame = ttk.LabelFrame(p, text=" Devices ", padding=6)
        df_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=2)
        df_frame.columnconfigure(1, weight=1)
        ttk.Label(df_frame, text="Transistor 1:", font=("Arial", 9, "bold")).grid(
            row=0, column=0, sticky="w", padx=4, pady=3)
        self._t1_var = tk.StringVar()
        self._t1_cb  = ttk.Combobox(df_frame, textvariable=self._t1_var,
                                     state="readonly", font=("Consolas", 8), width=28)
        self._t1_cb.grid(row=0, column=1, sticky="ew", padx=4, pady=3)

        ttk.Label(df_frame, text="Diode Transistor 2:", font=("Arial", 9, "bold")).grid(
            row=1, column=0, sticky="w", padx=4, pady=3)
        self._t2_var = tk.StringVar()
        self._t2_cb  = ttk.Combobox(df_frame, textvariable=self._t2_var,
                                     state="readonly", font=("Consolas", 8), width=28)
        self._t2_cb.grid(row=1, column=1, sticky="ew", padx=4, pady=3)
        self._refresh_device_lists()

        # ── Gate drive ──
        gf = ttk.LabelFrame(p, text=" Gate Drive ", padding=6)
        gf.grid(row=2, column=0, sticky="ew", padx=4, pady=2)
        gf.columnconfigure(1, weight=1)

        gate_fields = [
            ("Turn-on Gate Resistor [Ω]:",  "r_g_on",   56.0),
            ("Turn-off Gate Resistor [Ω]:", "r_g_off",  52.4),
            ("Turn-on Gate Voltage [V]:",   "v_g_on",   15.0),
        ]
        self._gate_vars = {}
        for r, (lbl, key, default) in enumerate(gate_fields):
            ttk.Label(gf, text=lbl, font=("Arial", 9)).grid(
                row=r, column=0, sticky="w", padx=4, pady=2)
            var = tk.StringVar(value=str(default))
            ttk.Entry(gf, textvariable=var, width=10,
                      font=("Consolas", 9)).grid(
                row=r, column=1, sticky="ew", padx=4, pady=2)
            self._gate_vars[key] = var

        # ── Scalar operating point ──
        sf = ttk.LabelFrame(p, text=" Operating Point (scalars) ", padding=6)
        sf.grid(row=3, column=0, sticky="ew", padx=4, pady=2)
        sf.columnconfigure(1, weight=1)

        scalar_fields = [
            ("Output Power [W]:",              "p_out",         10000.0),
            ("Vin [V]:",                        "v_in",           700.0),
            ("Vout [V]:",                       "v_out",          300.0),
            ("Frequency [kHz]:",               "frequency",       10.0),
            ("Zeta = f * L:",                  "zeta",             5.0),
            ("Temperature Heatsink [°C]:",     "t_heatsink",      25.0),
            ("Thermal Resistance [K/W]:",      "r_th_heatsink",    1.0),
        ]
        self._scalar_vars = {}
        for r, (lbl, key, default) in enumerate(scalar_fields):
            ttk.Label(sf, text=lbl, font=("Arial", 9)).grid(
                row=r, column=0, sticky="w", padx=4, pady=2)
            var = tk.StringVar(value=str(default))
            ttk.Entry(sf, textvariable=var, width=10,
                      font=("Consolas", 9)).grid(
                row=r, column=1, sticky="ew", padx=4, pady=2)
            self._scalar_vars[key] = var

        # ── Axis ranges ──
        rf = ttk.LabelFrame(p, text=" Axis Ranges (min / max) ", padding=6)
        rf.grid(row=4, column=0, sticky="ew", padx=4, pady=2)
        rf.columnconfigure(1, weight=1); rf.columnconfigure(3, weight=1)

        range_fields = [
            ("Output Power [W]", "p_out",     1000.0,  10000.0),
            ("Vin [V]",          "v_in",       300.0,    700.0),
            ("Vout [V]",         "v_out",      100.0,    300.0),
            ("Frequency [kHz]",  "frequency",    1.0,     10.0),
            ("Zeta = f*L",       "zeta",         1.0,      5.0),
        ]
        self._range_vars = {}   # key+"_min" / key+"_max"
        for r, (lbl, key, dmin, dmax) in enumerate(range_fields):
            ttk.Label(rf, text=f"{lbl} min:", font=("Arial", 8)).grid(
                row=r, column=0, sticky="w", padx=3, pady=1)
            vmin = tk.StringVar(value=str(dmin))
            ttk.Entry(rf, textvariable=vmin, width=8,
                      font=("Consolas", 8)).grid(row=r, column=1, sticky="ew", padx=3)
            ttk.Label(rf, text="max:", font=("Arial", 8)).grid(
                row=r, column=2, sticky="w", padx=3)
            vmax = tk.StringVar(value=str(dmax))
            ttk.Entry(rf, textvariable=vmax, width=8,
                      font=("Consolas", 8)).grid(row=r, column=3, sticky="ew", padx=3)
            self._range_vars[key+"_min"] = vmin
            self._range_vars[key+"_max"] = vmax

        # ── Update Plots button + status ──
        bf = ttk.Frame(p, padding=(0, 4))
        bf.grid(row=5, column=0, sticky="ew", padx=4, pady=4)
        self._run_btn = ttk.Button(bf, text="▶  Update Plots",
                                   command=self._run_all)
        self._run_btn.pack(side="left", ipady=4, ipadx=8)
        self._status_lbl = ttk.Label(bf, text="", foreground="gray",
                                     font=("Arial", 8))
        self._status_lbl.pack(side="left", padx=8)

        # ── Warnings ──
        wf = ttk.LabelFrame(p, text=" Warnings ", padding=4)
        wf.grid(row=6, column=0, sticky="ew", padx=4, pady=(2, 4))
        wf.columnconfigure(0, weight=1)
        self._warn_text = tk.Text(wf, height=4, font=("Arial", 8),
                                  wrap="word", state="disabled",
                                  background="#fff8e1")
        self._warn_text.grid(row=0, column=0, sticky="ew")

    # ──────────────────────────────────────────────────────────────────────
    # RIGHT PANEL  – 3 plot columns
    # ──────────────────────────────────────────────────────────────────────

    def _build_right(self, p: tk.Widget):
        p.columnconfigure(0, weight=1)
        p.columnconfigure(1, weight=1)
        p.rowconfigure(0, weight=1)
        p.rowconfigure(1, weight=1)

        self._panels: list[dict] = []

        # Default configurations matching the reference screenshots
        defaults = [
            {"mode": "Contour", "x": "Zeta = f*L",      "y": "Vin [V]",
             "z": "Conduction Losses Transistor1 [W]"},
            {"mode": "Contour", "x": "Zeta = f*L",      "y": "Vin [V]",
             "z": "Total Switching Losses Transistor1 [W]"},
            {"mode": "Contour", "x": "Frequency [kHz]", "y": "Vin [V]",
             "z": "Total Switching Losses Transistor1 [W]"},
            {"mode": "Contour", "x": "Output Power [W]", "y": "Vin [V]",
             "z": "Total Power Losses Transistor1 [W]"},
        ]

        for idx, cfg in enumerate(defaults):
            pnl = self._build_plot_panel(p, idx // 2, idx % 2, cfg)
            self._panels.append(pnl)

    def _build_plot_panel(self, parent: tk.Widget, row: int, col: int, cfg: dict) -> dict:
        """Build one plot cell. Returns a dict of its widgets/variables."""
        frame = ttk.Frame(parent, height=420)
        frame.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        frame.grid_propagate(False)

        # ── Selectors ──
        sel = ttk.LabelFrame(frame, text=" Plot Settings ", padding=4)
        sel.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        sel.columnconfigure(1, weight=1)

        # Line / Contour
        mode_var = tk.StringVar(value=cfg["mode"])
        ttk.Label(sel, text="Line/Contour:", font=("Arial", 8)).grid(
            row=0, column=0, sticky="w", padx=3, pady=2)
        mode_cb = ttk.Combobox(sel, textvariable=mode_var,
                               values=["Contour", "Line"],
                               state="readonly", font=("Arial", 8), width=10)
        mode_cb.grid(row=0, column=1, sticky="ew", padx=3, pady=2)

        # x-Axis
        x_var = tk.StringVar(value=cfg["x"])
        ttk.Label(sel, text="x-Axis:", font=("Arial", 8)).grid(
            row=1, column=0, sticky="w", padx=3, pady=2)
        x_cb = ttk.Combobox(sel, textvariable=x_var,
                             values=AXIS_VARS, state="readonly",
                             font=("Arial", 8), width=20)
        x_cb.grid(row=1, column=1, sticky="ew", padx=3, pady=2)

        # y-Axis  (axis var in Contour; metric in Line)
        y_var = tk.StringVar(value=cfg["y"])
        y_lbl = ttk.Label(sel, text="y-Axis:", font=("Arial", 8))
        y_lbl.grid(row=2, column=0, sticky="w", padx=3, pady=2)
        y_cb = ttk.Combobox(sel, textvariable=y_var,
                             values=AXIS_VARS, state="readonly",
                             font=("Arial", 8), width=20)
        y_cb.grid(row=2, column=1, sticky="ew", padx=3, pady=2)

        # z-Axis  (metric in Contour; hidden in Line)
        z_var = tk.StringVar(value=cfg["z"])
        z_lbl = ttk.Label(sel, text="z-Axis:", font=("Arial", 8))
        z_lbl.grid(row=3, column=0, sticky="w", padx=3, pady=2)
        z_cb = ttk.Combobox(sel, textvariable=z_var,
                             values=METRICS, state="readonly",
                             font=("Arial", 8), width=20)
        z_cb.grid(row=3, column=1, sticky="ew", padx=3, pady=2)

        # Pop-Out button
        pnl_ref = {}  # will be filled below
        ttk.Button(sel, text="Pop-Out",
                   command=lambda pr=pnl_ref: self._popout(pr)).grid(
            row=0, column=2, padx=4)

        # ── Matplotlib figure ──
        fig_frame = ttk.Frame(frame)
        fig_frame.grid(row=1, column=0, sticky="nsew")
        fig_frame.columnconfigure(0, weight=1)
        fig_frame.rowconfigure(0, weight=1)

        try:
            import matplotlib
            matplotlib.use("TkAgg")
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import (
                FigureCanvasTkAgg, NavigationToolbar2Tk)

            class FixedToolbar(NavigationToolbar2Tk):
                def set_message(self, _message):
                    pass

            fig  = Figure(figsize=(5.5, 4.2), dpi=90,
                          facecolor="#f5f5f5", layout="none")
            if hasattr(fig, "set_layout_engine"):
                fig.set_layout_engine(None)
            ax   = fig.add_axes([0.12, 0.16, 0.70, 0.70])
            cax  = fig.add_axes([0.86, 0.16, 0.035, 0.70])
            cax.set_visible(False)
            ax.set_facecolor("#eef2f7")
            ax.text(0.5, 0.5, "Press ▶ Update Plots",
                    ha="center", va="center", fontsize=9,
                    color="gray", transform=ax.transAxes)

            canvas = FigureCanvasTkAgg(fig, master=fig_frame)
            canvas.draw()
            canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

            tb_frame = ttk.Frame(fig_frame)
            tb_frame.grid(row=1, column=0, sticky="ew")
            FixedToolbar(canvas, tb_frame)

            has_mpl = True
        except ImportError:
            ttk.Label(fig_frame, text="matplotlib not installed",
                      foreground=CLR_RED).grid(row=0, column=0)
            fig = ax = cax = canvas = None
            has_mpl = False

        pnl_ref.update(dict(
            mode_var=mode_var, x_var=x_var, y_var=y_var, z_var=z_var,
            fig=fig, ax=ax, cax=cax, canvas=canvas, has_mpl=has_mpl,
            y_lbl=y_lbl, y_cb=y_cb, z_lbl=z_lbl, z_cb=z_cb,
        ))

        # Wire mode change → update y/z combobox values
        def _on_mode_change(*_, pnl=pnl_ref):
            self._sync_axis_options(pnl)
        mode_var.trace_add("write", _on_mode_change)
        _on_mode_change()  # set initial state

        return pnl_ref

    def _sync_axis_options(self, pnl: dict):
        """Switch y-axis and z-axis combos between axis vars and metrics."""
        if pnl["mode_var"].get() == "Contour":
            pnl["y_cb"]["values"] = AXIS_VARS
            pnl["y_lbl"].config(text="y-Axis:")
            pnl["z_lbl"].grid()
            pnl["z_cb"].grid()
            # ensure y_var is an axis var
            if pnl["y_var"].get() not in AXIS_VARS:
                pnl["y_var"].set(AXIS_VARS[0])
        else:  # Line
            pnl["y_cb"]["values"] = METRICS
            pnl["y_lbl"].config(text="y-Axis (metric):")
            pnl["z_lbl"].grid_remove()
            pnl["z_cb"].grid_remove()
            # ensure y_var is a metric
            if pnl["y_var"].get() not in METRICS:
                pnl["y_var"].set(METRICS[0])

    # ──────────────────────────────────────────────────────────────────────
    # Device list management
    # ──────────────────────────────────────────────────────────────────────

    def _refresh_device_lists(self):
        if self.df is None or self.df.empty:
            return
        names = sorted(self.df["name"].dropna().tolist())
        for cb in (self._t1_cb, self._t2_cb):
            current = cb.get()
            cb["values"] = names
            if current in names:
                cb.set(current)
            elif names:
                cb.set(names[0])

    def update_df(self, df):
        self.df = df
        self._refresh_device_lists()

    def _load_device(self, name: str) -> ConverterDevice | None:
        if name in self._devices:
            return self._devices[name]
        if self.df is None:
            return None
        row = self.df[self.df["name"] == name]
        if row.empty:
            return None
        try:
            dev = ConverterDevice(row.iloc[0]["_original_file_path"])
            self._devices[name] = dev
            return dev
        except Exception as e:
            messagebox.showerror("Device Error", str(e))
            return None

    # ──────────────────────────────────────────────────────────────────────
    # Parameter parsing
    # ──────────────────────────────────────────────────────────────────────

    def _parse_params(self, pnl: dict) -> ConverterParams | None:
        def _f(d, k, default=0.0):
            try: return float(d[k].get())
            except Exception: return default
        def _i(d, k, default=40):
            try: return int(d[k].get())
            except Exception: return default

        try:
            return ConverterParams(
                topology      = TOPO_FROM_LABEL.get(self._topo_var.get(), "buck_boost"),
                p_out         = _f(self._scalar_vars, "p_out",        10000.0),
                v_in          = _f(self._scalar_vars, "v_in",           700.0),
                v_out         = _f(self._scalar_vars, "v_out",          300.0),
                frequency     = _f(self._scalar_vars, "frequency",       10.0),
                zeta          = _f(self._scalar_vars, "zeta",             5.0),
                t_heatsink    = _f(self._scalar_vars, "t_heatsink",      25.0),
                r_th_heatsink = _f(self._scalar_vars, "r_th_heatsink",    1.0),
                v_g_on        = _f(self._gate_vars,   "v_g_on",          15.0),
                r_g_on        = _f(self._gate_vars,   "r_g_on",           0.0),
                r_g_off       = _f(self._gate_vars,   "r_g_off",          0.0),
                p_out_min     = _f(self._range_vars,  "p_out_min",     1000.0),
                p_out_max     = _f(self._range_vars,  "p_out_max",    10000.0),
                v_in_min      = _f(self._range_vars,  "v_in_min",      300.0),
                v_in_max      = _f(self._range_vars,  "v_in_max",      700.0),
                v_out_min     = _f(self._range_vars,  "v_out_min",     100.0),
                v_out_max     = _f(self._range_vars,  "v_out_max",     300.0),
                frequency_min = _f(self._range_vars,  "frequency_min",   1.0),
                frequency_max = _f(self._range_vars,  "frequency_max",  10.0),
                zeta_min      = _f(self._range_vars,  "zeta_min",        1.0),
                zeta_max      = _f(self._range_vars,  "zeta_max",        5.0),
                mode   = pnl["mode_var"].get(),
                x_axis = pnl["x_var"].get(),
                y_axis = pnl["y_var"].get(),
                z_axis = pnl["z_var"].get(),
                n_points = 100,
            )
        except Exception as e:
            messagebox.showerror("Parameter Error", str(e))
            return None

    # ──────────────────────────────────────────────────────────────────────
    # Run
    # ──────────────────────────────────────────────────────────────────────

    def _run_all(self):
        t1_name = self._t1_var.get()
        t2_name = self._t2_var.get()
        if not t1_name or not t2_name:
            messagebox.showwarning("Selection", "Select T1 and T2 first.")
            return

        t1 = self._load_device(t1_name)
        t2 = self._load_device(t2_name)
        if t1 is None or t2 is None:
            return

        self._run_btn.config(state="disabled")
        self._status_lbl.config(text="⏳ Computing…", foreground=CLR_WARN)
        self.parent.update_idletasks()

        all_warnings = []

        def _worker():
            for pnl in self._panels:
                params = self._parse_params(pnl)
                if params is None:
                    continue
                try:
                    result = compute(params, t1, t2)
                    all_warnings.extend(result.warnings)
                    self.parent.after(0, lambda r=result, p=pnl: self._draw(r, p))
                except Exception as e:
                    self.parent.after(0, lambda err=str(e): messagebox.showerror(
                        "Computation Error", err))

            self.parent.after(0, lambda: self._finish(all_warnings))

        threading.Thread(target=_worker, daemon=True).start()

    def _finish(self, warnings):
        self._run_btn.config(state="normal")
        self._status_lbl.config(text="✅ Done", foreground=CLR_GREEN)
        self._warn_text.config(state="normal")
        self._warn_text.delete("1.0", "end")
        if warnings:
            seen = []
            for w in warnings:
                if w not in seen:
                    self._warn_text.insert("end", f"⚠ {w}\n")
                    seen.append(w)
        else:
            self._warn_text.insert("end", "No warnings.")
        self._warn_text.config(state="disabled")

    # ──────────────────────────────────────────────────────────────────────
    # Drawing
    # ──────────────────────────────────────────────────────────────────────

    def _draw(self, result, pnl: dict):
        if not pnl["has_mpl"]:
            return
        from matplotlib import cm as mpl_cm
        from matplotlib.ticker import FormatStrFormatter

        ax  = pnl["ax"]
        fig = pnl["fig"]
        cax = pnl["cax"]
        for extra_ax in list(fig.axes):
            if extra_ax not in (ax, cax):
                extra_ax.remove()
        ax.cla()
        cax.cla()
        cax.set_visible(False)
        pnl["_cbar"] = None

        if result.mode == "Contour":
            X, Y = np.meshgrid(result.x_data, result.y_data)
            Z = np.ma.masked_invalid(result.z_data)
            try:
                mappable = ax.contourf(X, Y, Z, 100, cmap=mpl_cm.inferno)
                cax.set_visible(True)
                cbar = fig.colorbar(mappable, cax=cax, format="%.2f")
                cbar.set_label(pnl["z_var"].get(), fontsize=7)
                pnl["_cbar"] = cbar
            except Exception:
                mappable = ax.pcolormesh(X, Y, Z, shading="auto", cmap=mpl_cm.inferno)
                cax.set_visible(True)
                cbar = fig.colorbar(mappable, cax=cax, format="%.2f")
                cbar.set_label(pnl["z_var"].get(), fontsize=7)
                pnl["_cbar"] = cbar

            ax.set_xlabel(result.x_label, fontsize=8)
            ax.set_ylabel(result.y_label, fontsize=8)
            ax.set_title(result.z_data is not None and result.y_label or "", fontsize=8)
            # use z_axis label as title
            ax.set_title(pnl["z_var"].get(), fontsize=8)
            ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
            ax.yaxis.set_major_formatter(FormatStrFormatter("%.2f"))

        else:  # Line
            ax.plot(result.x_data, result.z_data, color="#2980b9", linewidth=1.8)
            ax.set_xlabel(result.x_label, fontsize=8)
            ax.set_ylabel(result.y_label, fontsize=8)
            ax.set_title(result.y_label, fontsize=8)
            ax.grid(True)
            ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
            ax.yaxis.set_major_formatter(FormatStrFormatter("%.2f"))

        pnl["canvas"].draw()

    # ──────────────────────────────────────────────────────────────────────
    # Pop-Out
    # ──────────────────────────────────────────────────────────────────────

    def _popout(self, pnl: dict):
        """Open the current panel's figure in a detached matplotlib window."""
        if not pnl["has_mpl"] or pnl["fig"] is None:
            return
        import matplotlib.pyplot as plt
        fig2, ax2 = plt.subplots(figsize=(7, 5))
        # copy the lines/collections from the embedded axes
        for coll in pnl["ax"].collections:
            try:
                import copy
                ax2.add_collection(copy.copy(coll))
            except Exception:
                pass
        for line in pnl["ax"].lines:
            ax2.plot(line.get_xdata(), line.get_ydata(),
                     color=line.get_color(), linewidth=line.get_linewidth())
        ax2.set_xlim(pnl["ax"].get_xlim())
        ax2.set_ylim(pnl["ax"].get_ylim())
        ax2.set_xlabel(pnl["ax"].get_xlabel(), fontsize=10)
        ax2.set_ylabel(pnl["ax"].get_ylabel(), fontsize=10)
        ax2.set_title(pnl["ax"].get_title(), fontsize=10)
        ax2.grid(True)
        fig2.tight_layout()
        plt.show()