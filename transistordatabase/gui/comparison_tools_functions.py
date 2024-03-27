"""GUI comparison tools."""
import numpy as np
from math import floor
from scipy.interpolate import interpn
from matplotlib.widgets import Cursor
from decimal import Decimal
from transistordatabase.gui.gui import MainWindow


def new_annotation(axis):
    """
    Create an annotation and adds it to a matplotlibwidget axis.

    :param axis: matplotlibwidget axis to put the annotation on
    :return: annotation object
    """
    annotation = axis.annotate("", xy=(0, 0), xytext=(-100, 30), textcoords="offset pixels",
                               bbox=dict(boxstyle="square", fc="linen", ec="k", lw="1"),
                               arrowprops=dict(arrowstyle="-|>"))
    return annotation


def click_event(button, xdata, ydata, matplotlibwidget, annotations_list):
    """
    Create an annotation for an embedded matplotlibwidget graph on left click and removes last created annotation on right click.

    :param button: clicked button
    :param xdata: x-data of matplotlib graph
    :param ydata: y-data of matplotlib graph
    :param matplotlibwidget: matplotlibwidget object
    :param annotations_list: list to store added annotations
    :return: None
    """
    if str(button) == "MouseButton.LEFT":
        click_annotation = new_annotation(matplotlibwidget.axis)
        annotations_list.append(click_annotation)
        y_scientific = '%.2E' % Decimal(str(ydata))
        click_annotation.xy = (xdata, ydata)
        text = f"({round(xdata, 2)}, {y_scientific})"
        click_annotation.set_text(text)
        click_annotation.set_visible(True)
    elif str(button) == "MouseButton.RIGHT":
        annotations_list[-1].remove()
        annotations_list.pop()
    matplotlibwidget.figure.canvas.draw_idle()


def plot_all_energy_data(transistor, matplotlibwidget, switch_diode):
    """
    Plot all switch energy i-e characteristic curves and diode reverse recovery energy i-e characteristic curves.

    Data is extracted from the manufacturer datasheet into a MatplotlibWidget.

    :param transistor: transistor object
    :param matplotlibwidget: MatplotlibWidget object
    :param switch_diode: "switch" or "diode"
    :return: None

    """
    annotations_list = []

    def clicked(event):
        if event.dblclick:
            click_event(event.button, event.xdata, event.ydata, matplotlibwidget, annotations_list)

    if switch_diode == "switch":
        e_on_i_e_curve_count, e_off_i_e_curve_count = [0, 0]
        for i_energy_data in np.array(range(0, len(transistor.switch.e_on))):
            if transistor.switch.e_on[i_energy_data].dataset_type == 'graph_i_e':
                e_on_i_e_curve_count += 1
        for i_energy_data in np.array(range(0, len(transistor.switch.e_off))):
            if transistor.switch.e_off[i_energy_data].dataset_type == 'graph_i_e':
                e_off_i_e_curve_count += 1
        if e_on_i_e_curve_count and e_on_i_e_curve_count == e_off_i_e_curve_count:
            # look for e_on losses
            for i_energy_data in np.array(range(0, len(transistor.switch.e_on))):
                if transistor.switch.e_on[i_energy_data].dataset_type == 'graph_i_e':
                    labelplot = "$e_{{on}}$: $V_{{supply}}$ = {0} V, $V_{{g}}$ = {1} V, $T_{{J}}$ = {2} °C, $R_{{g}}$ = {3} Ohm".format(
                        transistor.switch.e_on[i_energy_data].v_supply,
                        transistor.switch.e_on[i_energy_data].v_g, transistor.switch.e_on[i_energy_data].t_j,
                        transistor.switch.e_on[i_energy_data].r_g)
                    matplotlibwidget.axis.plot(transistor.switch.e_on[i_energy_data].graph_i_e[0],
                                               transistor.switch.e_on[i_energy_data].graph_i_e[1],
                                               label=labelplot)
                    matplotlibwidget.axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            # look for e_off losses
            for i_energy_data in np.array(range(0, len(transistor.switch.e_off))):
                if transistor.switch.e_off[i_energy_data].dataset_type == 'graph_i_e':
                    labelplot = "$e_{{off}}$: $V_{{supply}}$ = {0} V, $V_{{g}}$ = {1} V, $T_{{J}}$ = {2} °C, $R_{{g}}$ = {3} Ohm".format(
                        transistor.switch.e_off[i_energy_data].v_supply,
                        transistor.switch.e_off[i_energy_data].v_g,
                        transistor.switch.e_off[i_energy_data].t_j,
                        transistor.switch.e_off[i_energy_data].r_g)
                    matplotlibwidget.axis.plot(transistor.switch.e_off[i_energy_data].graph_i_e[0],
                                               transistor.switch.e_off[i_energy_data].graph_i_e[1],
                                               label=labelplot)
                    matplotlibwidget.axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            matplotlibwidget.axis.legend(fontsize=5)
            matplotlibwidget.axis.set(xlabel="Current in A",
                                      ylabel="Loss Energy in J")
            matplotlibwidget.axis.grid()
            matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
            matplotlibwidget.figure.canvas.draw_idle()

            matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                             color="Green", linewidth=1)

            matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)

        else:
            matplotlibwidget.axis.clear()
            matplotlibwidget.figure.canvas.draw_idle()
            MainWindow.show_popup_message(MainWindow, f"Switch energy i_e curves are not available for <b>{transistor.name}</b>!")

    if switch_diode == "diode":
        e_rr_i_e_curve_count = 0
        for i_energy_data in np.array(range(0, len(transistor.diode.e_rr))):
            if transistor.diode.e_rr[i_energy_data].dataset_type == 'graph_i_e':
                e_rr_i_e_curve_count += 1
        # look for e_off losses
        if e_rr_i_e_curve_count > 0:
            for i_energy_data in np.array(range(0, len(transistor.diode.e_rr))):
                # check if data is available as 'graph_i_e'
                if transistor.diode.e_rr[i_energy_data].dataset_type == 'graph_i_e':
                    # add label plot
                    labelplot = "$e_{{rr}}$: $v_{{supply}}$ = {0} V, $T_{{J}}$ = {1} °C, $R_{{g}}$ = {2} Ohm".format(
                        transistor.diode.e_rr[i_energy_data].v_supply, transistor.diode.e_rr[i_energy_data].t_j,
                        transistor.diode.e_rr[i_energy_data].r_g)
                    # check if gate voltage is given (GaN Transistor, SiC-MOSFET)
                    # if ture, add gate-voltage to label
                    if isinstance(transistor.diode.e_rr[i_energy_data].v_g, (int, float)):
                        labelplot = labelplot + ", $v_{{g}}$ = {0} V".format(
                            transistor.diode.e_rr[i_energy_data].v_g)
                    # plot
                    matplotlibwidget.axis.plot(transistor.diode.e_rr[i_energy_data].graph_i_e[0],
                                               transistor.diode.e_rr[i_energy_data].graph_i_e[1],
                                               label=labelplot)
                    matplotlibwidget.axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            matplotlibwidget.axis.legend(fontsize=5)
            matplotlibwidget.axis.set(xlabel="Current in A",
                                      ylabel="Loss Energy in J")
            matplotlibwidget.axis.grid()
            matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
            matplotlibwidget.figure.canvas.draw_idle()
            matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                             color="Green", linewidth=1)

            matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)

        else:
            matplotlibwidget.axis.clear()
            matplotlibwidget.figure.canvas.draw_idle()
            MainWindow.show_popup_message(MainWindow, f"Diode reverse recovery energy i_e curves are not available for <b>{transistor.name}</b>!")

def plot_all_energy_data_r_g(transistor, matplotlibwidget, switch_diode):
    """
    Plot all switch energy r-e characteristic curves and diode reverse recovery energy r-e characteristic curves.

    The plotted data is extracted from the manufacturer datasheet into a MatplotlibWidget.

    :param transistor: transistor object
    :param matplotlibwidget: MatplotlibWidget object
    :param switch_diode: "switch" or "diode"
    :return: None
    """
    annotations_list = []

    def clicked(event):
        if event.dblclick:
            click_event(event.button, event.xdata, event.ydata, matplotlibwidget, annotations_list)

    if switch_diode == "switch":
        e_on_r_e_curve_count, e_off_r_e_curve_count = [0, 0]
        for i_energy_data in np.array(range(0, len(transistor.switch.e_on))):
            if transistor.switch.e_on[i_energy_data].dataset_type == 'graph_r_e':
                e_on_r_e_curve_count += 1
        for i_energy_data in np.array(range(0, len(transistor.switch.e_off))):
            if transistor.switch.e_off[i_energy_data].dataset_type == 'graph_r_e':
                e_off_r_e_curve_count += 1
        if e_on_r_e_curve_count and e_on_r_e_curve_count == e_off_r_e_curve_count:
            # look for e_on losses
            for i_energy_data in np.array(range(0, len(transistor.switch.e_on))):
                if transistor.switch.e_on[i_energy_data].dataset_type == 'graph_r_e':
                    labelplot = "$e_{{on}}$: $V_{{supply}}$ = {0} V, $V_{{g}}$ = {1} V, $T_{{J}}$ = {2} °C, $i_{{ch}}$ = {3} A".format(
                        transistor.switch.e_on[i_energy_data].v_supply,
                        transistor.switch.e_on[i_energy_data].v_g, transistor.switch.e_on[i_energy_data].t_j,
                        transistor.switch.e_on[i_energy_data].i_x)
                    matplotlibwidget.axis.plot(transistor.switch.e_on[i_energy_data].graph_r_e[0],
                                               transistor.switch.e_on[i_energy_data].graph_r_e[1],
                                               label=labelplot)
                    matplotlibwidget.axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            # look for e_off losses
            for i_energy_data in np.array(range(0, len(transistor.switch.e_off))):
                if transistor.switch.e_off[i_energy_data].dataset_type == 'graph_r_e':
                    labelplot = "$e_{{off}}$: $V_{{supply}}$ = {0} V, $V_{{g}}$ = {1} V, $T_{{J}}$ = {2} °C, $i_{{ch}}$ = {3} A".format(
                        transistor.switch.e_off[i_energy_data].v_supply,
                        transistor.switch.e_off[i_energy_data].v_g,
                        transistor.switch.e_off[i_energy_data].t_j,
                        transistor.switch.e_off[i_energy_data].i_x)
                    matplotlibwidget.axis.plot(transistor.switch.e_off[i_energy_data].graph_r_e[0],
                                               transistor.switch.e_off[i_energy_data].graph_r_e[1],
                                               label=labelplot)
                    matplotlibwidget.axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            matplotlibwidget.axis.legend(fontsize=5)
            matplotlibwidget.axis.set(xlabel="Gate Resistor in Ω",
                                      ylabel="Loss Energy in J")
            matplotlibwidget.axis.grid()
            matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
            matplotlibwidget.figure.canvas.draw_idle()
            matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                             color="Green", linewidth=1)

            matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)

        else:
            matplotlibwidget.axis.clear()
            matplotlibwidget.figure.canvas.draw_idle()
            MainWindow.show_popup_message(MainWindow, f"Switch energy r_e curves are not available for <b>{transistor.name}</b>!")

    if switch_diode == "diode":
        e_rr_r_e_curve_count = 0
        for i_energy_data in np.array(range(0, len(transistor.diode.e_rr))):
            if transistor.diode.e_rr[i_energy_data].dataset_type == 'graph_r_e':
                e_rr_r_e_curve_count += 1
        # look for e_off losses
        if e_rr_r_e_curve_count > 0:
            for i_energy_data in np.array(range(0, len(transistor.diode.e_rr))):
                # check if data is available as 'graph_i_e'
                if transistor.diode.e_rr[i_energy_data].dataset_type == 'graph_r_e':
                    # add label plot
                    labelplot = "$e_{{rr}}$: $v_{{supply}}$ = {0} V, $T_{{J}}$ = {1} °C, $I_{{ch}}$ = {2} A".format(
                        transistor.diode.e_rr[i_energy_data].v_supply, transistor.diode.e_rr[i_energy_data].t_j,
                        transistor.diode.e_rr[i_energy_data].i_x)
                    # check if gate voltage is given (GaN Transistor, SiC-MOSFET)
                    # if ture, add gate-voltage to label
                    if isinstance(transistor.diode.e_rr[i_energy_data].v_g, (int, float)):
                        labelplot = labelplot + ", $v_{{g}}$ = {0} V".format(
                            transistor.diode.e_rr[i_energy_data].v_g)

                    # plot
                    matplotlibwidget.axis.plot(transistor.diode.e_rr[i_energy_data].graph_r_e[0],
                                               transistor.diode.e_rr[i_energy_data].graph_r_e[1],
                                               label=labelplot)
                    matplotlibwidget.axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            matplotlibwidget.axis.legend(fontsize=5)
            matplotlibwidget.axis.set(xlabel="Gate Resistor in Ω",
                                      ylabel="Loss Energy in J")
            matplotlibwidget.axis.grid()
            matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
            matplotlibwidget.figure.canvas.draw_idle()
            matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                             color="Green", linewidth=1)

            matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)

        else:
            matplotlibwidget.axis.clear()
            matplotlibwidget.figure.canvas.draw_idle()
            MainWindow.show_popup_message(MainWindow, f"Diode reverse recovery energy r_e curves are not available for <b>{transistor.name}</b>!")


def plot_all_channel_data(transistor, matplotlibwidget, switch_diode):
    """
    Plot all channel characteristic curves which are extracted from the manufacturer datasheet into a MatplotlibWidget.

    :param transistor: transistor object
    :param matplotlibwidget: MatplotlibWidget object
    :param switch_diode: "switch" or "diode"
    :return: None
    """
    annotations_list = []

    def clicked(event):
        if event.dblclick:
            click_event(event.button, event.xdata, event.ydata, matplotlibwidget, annotations_list)

    if switch_diode == "switch":
        categorize_with_temp_plots = {}
        categorize_with_vgs_plots = {}
        if len(transistor.switch.channel) > 5:
            count = 0
            for channel in transistor.switch.channel:
                try:
                    categorize_with_temp_plots[channel.t_j].append(channel)
                except KeyError:
                    categorize_with_temp_plots[channel.t_j] = [channel]
                try:
                    categorize_with_vgs_plots[channel.v_g].append(channel)
                except KeyError:
                    categorize_with_vgs_plots[channel.v_g] = [channel]
            for _, curve_list in categorize_with_temp_plots.items():
                if len(curve_list) > 1:
                    count += 1
                    for curve in curve_list:
                        plot_label = "$V_{{g}}$ = {0} V ".format(curve.v_g)
                        matplotlibwidget.axis.plot(curve.graph_v_i[0], curve.graph_v_i[1], label=plot_label)
                    matplotlibwidget.axis.legend(fontsize=5)
                    matplotlibwidget.axis.set(xlabel="Voltage in V", ylabel="Current in A")
                    matplotlibwidget.axis.grid()
                    matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
                    matplotlibwidget.figure.canvas.draw_idle()
                    matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                                     color="Green", linewidth=1)

                    matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)

            for _, curve_list in categorize_with_vgs_plots.items():
                if len(curve_list) > count:
                    for curve in curve_list:
                        plot_label = "$T_{{j}}$ = {0} °C".format(curve.t_j)
                        matplotlibwidget.axis.plot(curve.graph_v_i[0], curve.graph_v_i[1], label=plot_label)
                    matplotlibwidget.axis.legend(fontsize=5)
                    matplotlibwidget.axis.set(xlabel="Voltage in V", ylabel="Current in A")
                    matplotlibwidget.axis.grid()
                    matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
                    matplotlibwidget.figure.canvas.draw_idle()
                    matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                                     color="Green", linewidth=1)

                    matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)
        else:
            for i_channel in np.array(range(0, len(transistor.switch.channel))):
                plot_label = "$V_{{g}}$ = {0} V, $T_{{J}}$ = {1} °C".format(transistor.switch.channel[i_channel].v_g, transistor.switch.channel[i_channel].t_j)
                matplotlibwidget.axis.plot(transistor.switch.channel[i_channel].graph_v_i[0], transistor.switch.channel[i_channel].graph_v_i[1],
                                           label=plot_label)
            matplotlibwidget.axis.legend(fontsize=5)
            matplotlibwidget.axis.set(xlabel="Voltage in V", ylabel="Current in A")
            matplotlibwidget.axis.grid()
            matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
            matplotlibwidget.figure.canvas.draw_idle()
            matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                             color="Green", linewidth=1)

            matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)

    elif switch_diode == "diode":
        categorize_with_temp_plots = {}
        categorize_with_vgs_plots = {}
        if len(transistor.diode.channel) > 5:
            count = 0
            for channel in transistor.diode.channel:
                try:
                    categorize_with_temp_plots[channel.t_j].append(channel)
                except KeyError:
                    categorize_with_temp_plots[channel.t_j] = [channel]
                try:
                    categorize_with_vgs_plots[channel.v_g].append(channel)
                except KeyError:
                    categorize_with_vgs_plots[channel.v_g] = [channel]
            for _, curve_list in categorize_with_temp_plots.items():
                if len(curve_list) > 1:
                    count += 1
                    for curve in curve_list:
                        plot_label = "$V_{{g}}$ = {0} V ".format(curve.v_g)
                        matplotlibwidget.axis.plot(curve.graph_v_i[0], curve.graph_v_i[1], label=plot_label)
                    matplotlibwidget.axis.legend(fontsize=5)
                    matplotlibwidget.axis.set(xlabel="Voltage in V", ylabel="Current in A")
                    matplotlibwidget.axis.grid()
                    matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
                    matplotlibwidget.figure.canvas.draw_idle()
                    matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                                     color="Green", linewidth=1)

                    matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)

            for _, curve_list in categorize_with_vgs_plots.items():
                if len(curve_list) > count:
                    for curve in curve_list:
                        plot_label = "$T_{{j}}$ = {0} °C".format(curve.t_j)
                        matplotlibwidget.axis.plot(curve.graph_v_i[0], curve.graph_v_i[1], label=plot_label)
                    matplotlibwidget.axis.legend(fontsize=5)
                    matplotlibwidget.axis.set(xlabel="Voltage in V", ylabel="Current in A")
                    matplotlibwidget.axis.grid()
                    matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
                    matplotlibwidget.figure.canvas.draw_idle()
                    matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                                     color="Green", linewidth=1)

                    matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)
        else:
            for i_channel in np.array(range(0, len(transistor.diode.channel))):
                plot_label = "$V_{{g}}$ = {0} V, $T_{{J}}$ = {1} °C".format(transistor.diode.channel[i_channel].v_g,
                                                                            transistor.diode.channel[i_channel].t_j)
                matplotlibwidget.axis.plot(transistor.diode.channel[i_channel].graph_v_i[0],
                                           transistor.diode.channel[i_channel].graph_v_i[1], label=plot_label)
            matplotlibwidget.axis.legend(fontsize=5)
            matplotlibwidget.axis.set(xlabel="Voltage in V", ylabel="Current in A")
            matplotlibwidget.axis.grid()
            matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
            matplotlibwidget.figure.canvas.draw_idle()
            matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                             color="Green", linewidth=1)

            matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)

def plot_e_on(transistor1, transistor2, transistor3, matplotlibwidget, t_j1, t_j2, t_j3, r_g_on1, r_g_on2, r_g_on3, v_supply1, v_supply2, v_supply3):
    """
    Calculate and plot switch turn-on energy i-e characteristic curves for all three transistors.

    Valid for a chosen junction temperature, gate resistor and supply voltage into a MatplotlibWidget

    :param transistor1: transistor object for transistor1
    :param transistor2: transistor object for transistor2
    :param transistor3: transistor object for transistor3
    :param matplotlibwidget: MatplotlibWidget object
    :param t_j1: junction temperature for transistor1
    :param t_j2: junction temperature for transistor2
    :param t_j3: junction temperature for transistor3
    :param r_g_on1: gate resistor for transistor1
    :param r_g_on2: gate resistor for transistor2
    :param r_g_on3: gate resistor for transistor3
    :param v_supply1: supply voltage for transistor1
    :param v_supply2: supply voltage for transistor2
    :param v_supply3: supply voltage for transistor3

    :return: None
    """
    annotations_list = []

    def clicked(event):
        if event.dblclick:
            click_event(event.button, event.xdata, event.ydata, matplotlibwidget, annotations_list)

    transistor_list = [transistor1, transistor2, transistor3]
    t_j_list = [t_j1, t_j2, t_j3]
    r_g_on_list = [r_g_on1, r_g_on2, r_g_on3]
    v_supply_list = [v_supply1, v_supply2, v_supply3]

    color_list = ["blue", "green", "red"]

    for m in range(len(transistor_list)):
        try:
            t_j_available_unfiltered = [i for i in [e_on.t_j for e_on in transistor_list[m].switch.e_on]]
            t_j_available = []
            for i in t_j_available_unfiltered:
                if i not in t_j_available:
                    t_j_available.append(i)
            t_j_available.sort()

            v_supply_chosen = max([i for i in [e_on.v_supply for e_on in transistor_list[m].switch.e_on]])

            if len(t_j_available) == 1:
                try:
                    transistor_list[m].wp.e_on = transistor_list[m].calc_object_i_e(e_on_off_rr="e_on",
                                                                                    t_j=t_j_available[0],
                                                                                    v_supply=v_supply_chosen,
                                                                                    r_g=r_g_on_list[m],
                                                                                    normalize_t_to_v=10)
                    vec_e_on = transistor_list[m].wp.e_on.graph_i_e[1] * v_supply_list[m] / v_supply_chosen
                    vec_i = transistor_list[m].wp.e_on.graph_i_e[0]
                except:
                    transistor_list[m].wp.e_on = transistor_list[m].get_object_i_e(
                        e_on_off_rr="e_on",
                        t_j=t_j_available[0], v_supply=v_supply_chosen, r_g=r_g_on_list[m],
                        v_g=max([i for i in [e_on.v_g for e_on in transistor_list[m].switch.e_on] if i is not None]))
                    vec_e_on = transistor_list[m].wp.e_on.graph_i_e[1] * v_supply_list[m] / v_supply_chosen
                    vec_i = transistor_list[m].wp.e_on.graph_i_e[0]

                label = f"{transistor_list[m].name}, T_j = {t_j_available[0]}°C"

                MainWindow.show_popup_message(MainWindow,
                                              f"Switch energy i_e curve for <b>{transistor_list[m].name}</b> only available for T_j = "
                                              f"{t_j_available[0]}°C due to missing data!")

            else:
                r_g_on_max_list = np.zeros_like(t_j_available)

                for i in range(len(t_j_available)):
                    r_e_object_on = transistor_list[m].get_object_r_e_simplified(
                        e_on_off_rr="e_on",
                        t_j=t_j_available[i], v_g=max([i for i in [e_on.v_g for e_on in transistor_list[m].switch.e_on] if i is not None]),
                        v_supply=max([i for i in [e_on.v_supply for e_on in transistor_list[m].switch.e_on] if i is not None]),
                        normalize_t_to_v=10)
                    r_g_on_max_list[i] = np.amax(r_e_object_on.graph_r_e[0]) * 10000

                r_g_on_max = floor(10 * min(r_g_on_max_list) / 10000) / 10

                r_g_on_available = np.linspace(0, r_g_on_max, 10)

                vec_i = np.linspace(0, transistor_list[m].i_abs_max, 10)

                m_t_j_available, m_r_g_on_available, m_i = np.meshgrid(t_j_available, r_g_on_available, vec_i,
                                                                       indexing='ij')

                m_e_on = np.zeros_like(m_t_j_available)

                for i in range(len(t_j_available)):
                    for j in range(len(r_g_on_available)):
                        for k in range(len(vec_i)):
                            transistor_list[m].wp.e_on = transistor_list[m].calc_object_i_e(e_on_off_rr="e_on",
                                                                                            t_j=m_t_j_available[
                                                                                                i, j, k],
                                                                                            v_supply=v_supply_chosen,
                                                                                            r_g=m_r_g_on_available[
                                                                                                i, j, k],
                                                                                            normalize_t_to_v=10)

                            m_e_on[i, j, k] = np.interp(m_i[i, j, k], transistor_list[m].wp.e_on.graph_i_e[0],
                                                        transistor_list[m].wp.e_on.graph_i_e[1]) * v_supply_list[m] / v_supply_chosen * 1000000000

                points = (t_j_available, r_g_on_available, vec_i)
                values = m_e_on

                vec_e_on = np.zeros_like(vec_i)

                for n in range(len(vec_i)):
                    point = ([t_j_list[m], r_g_on_list[m], vec_i[n]])
                    vec_e_on[n] = interpn(points, values, point, bounds_error=False, fill_value=None) / 1000000000

                if t_j_list[m] < min(t_j_available) or t_j_list[m] > max(t_j_available):
                    label = f"{transistor_list[m].name} (data extrapolated)"
                else:
                    label = f"{transistor_list[m].name} (data interpolated)"

            matplotlibwidget.axis.plot(vec_i, vec_e_on, label=label, color=color_list[m])

        except:
            MainWindow.show_popup_message(MainWindow, f"Switch energy i_e curve is not available for <b>{transistor_list[m].name}</b>!")

        try:
            matplotlibwidget.axis.legend(fontsize=5)
            matplotlibwidget.axis.set(xlabel="Current in A",
                                      ylabel="Loss energy in J")
            matplotlibwidget.axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
            matplotlibwidget.axis.grid()
            matplotlibwidget.figure.canvas.draw_idle()

            matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                             color="Green", linewidth=1)
            matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)
        except:
            matplotlibwidget.axis.clear()
            matplotlibwidget.figure.canvas.draw_idle()

def plot_e_off(transistor1, transistor2, transistor3, matplotlibwidget, t_j1, t_j2, t_j3, r_g_off1, r_g_off2, r_g_off3, v_supply1, v_supply2, v_supply3):
    """
    Calculate and plot switch turn-off energy i-e characteristic curves for all three transistors.

    Valid for a chosen junction temperature, gate resistor and supply voltage into a MatplotlibWidget

    :param transistor1: transistor object for transistor1
    :param transistor2: transistor object for transistor2
    :param transistor3: transistor object for transistor3
    :param matplotlibwidget: MatplotlibWidget object
    :param t_j1: junction temperature for transistor1
    :param t_j2: junction temperature for transistor2
    :param t_j3: junction temperature for transistor3
    :param r_g_off1: gate resistor for transistor1
    :param r_g_off2: gate resistor for transistor2
    :param r_g_off3: gate resistor for transistor3
    :param v_supply1: supply voltage for transistor1
    :param v_supply2: supply voltage for transistor2
    :param v_supply3: supply voltage for transistor3

    :return: None
    """
    annotations_list = []

    def clicked(event):
        if event.dblclick:
            click_event(event.button, event.xdata, event.ydata, matplotlibwidget, annotations_list)

    transistor_list = [transistor1, transistor2, transistor3]
    t_j_list = [t_j1, t_j2, t_j3]
    r_g_off_list = [r_g_off1, r_g_off2, r_g_off3]
    v_supply_list = [v_supply1, v_supply2, v_supply3]

    color_list = ["blue", "green", "red"]

    for m in range(len(transistor_list)):
        try:
            t_j_available_unfiltered = [i for i in [e_off.t_j for e_off in transistor_list[m].switch.e_off]]
            t_j_available = []
            for i in t_j_available_unfiltered:
                if i not in t_j_available:
                    t_j_available.append(i)
            t_j_available.sort()

            v_supply_chosen = max([i for i in [e_off.v_supply for e_off in transistor_list[m].switch.e_off]])

            if len(t_j_available) == 1:
                try:
                    transistor_list[m].wp.e_off = transistor_list[m].calc_object_i_e(e_on_off_rr="e_off",
                                                                                     t_j=t_j_available[0],
                                                                                     v_supply=v_supply_chosen,
                                                                                     r_g=r_g_off_list[m],
                                                                                     normalize_t_to_v=10)
                    vec_e_off = transistor_list[m].wp.e_off.graph_i_e[1] * v_supply_list[m] / v_supply_chosen
                    vec_i = transistor_list[m].wp.e_off.graph_i_e[0]
                except:
                    transistor_list[m].wp.e_off = transistor_list[m].get_object_i_e(
                        e_on_off_rr="e_off",
                        t_j=t_j_available[0], v_supply=v_supply_chosen, r_g=r_g_off_list[m],
                        v_g=min([i for i in [e_off.v_g for e_off in transistor_list[m].switch.e_off] if i is not None]))
                    vec_e_off = transistor_list[m].wp.e_off.graph_i_e[1] * v_supply_list[m] / v_supply_chosen
                    vec_i = transistor_list[m].wp.e_off.graph_i_e[0]

                label = f"{transistor_list[m].name}, T_j = {t_j_available[0]}°C"

                MainWindow.show_popup_message(MainWindow, f"Switch energy i_e curve for <b>{transistor_list[m].name}</b> "
                                                          f"only available for T_j = {t_j_available[0]}°C due to missing data!")

            else:
                r_g_off_max_list = np.zeros_like(t_j_available)

                for i in range(len(t_j_available)):
                    r_e_object_off = transistor_list[m].get_object_r_e_simplified(e_on_off_rr="e_off",
                                                                                  t_j=t_j_available[i],
                                                                                  v_g=max([i for i in
                                                                                           [e_off.v_g for e_off in
                                                                                            transistor_list[
                                                                                                m].switch.e_off]
                                                                                           if
                                                                                           i is not None]),
                                                                                  v_supply=max(
                                                                                      [i for i in
                                                                                       [e_off.v_supply for e_off in
                                                                                        transistor_list[
                                                                                            m].switch.e_off] if
                                                                                       i is not None]),
                                                                                  normalize_t_to_v=10)
                    r_g_off_max_list[i] = np.amax(r_e_object_off.graph_r_e[0]) * 10000

                r_g_off_max = floor(10 * min(r_g_off_max_list) / 10000) / 10

                r_g_off_available = np.linspace(0, r_g_off_max, 10)

                vec_i = np.linspace(0, transistor_list[m].i_abs_max, 10)

                m_t_j_available, m_r_g_off_available, m_i = np.meshgrid(t_j_available, r_g_off_available, vec_i, indexing='ij')

                m_e_off = np.zeros_like(m_t_j_available)

                for i in range(len(t_j_available)):
                    for j in range(len(r_g_off_available)):
                        for k in range(len(vec_i)):
                            transistor_list[m].wp.e_off = transistor_list[m].calc_object_i_e(
                                e_on_off_rr="e_off", t_j=m_t_j_available[i, j, k], v_supply=v_supply_chosen,
                                r_g=m_r_g_off_available[i, j, k], normalize_t_to_v=10)
                            m_e_off[i, j, k] = np.interp(m_i[i, j, k], transistor_list[m].wp.e_off.graph_i_e[0],
                                                         transistor_list[m].wp.e_off.graph_i_e[1]) * v_supply_list[m] / v_supply_chosen * 1000000000

                points = (t_j_available, r_g_off_available, vec_i)
                values = m_e_off

                vec_e_off = np.zeros_like(vec_i)

                for n in range(len(vec_i)):
                    point = ([t_j_list[m], r_g_off_list[m], vec_i[n]])
                    vec_e_off[n] = interpn(points, values, point, bounds_error=False, fill_value=None) / 1000000000

                if t_j_list[m] < min(t_j_available) or t_j_list[m] > max(t_j_available):
                    label = f"{transistor_list[m].name} (data extrapolated)"
                else:
                    label = f"{transistor_list[m].name} (data interpolated)"

            matplotlibwidget.axis.plot(vec_i, vec_e_off, label=label, color=color_list[m])

        except:
            MainWindow.show_popup_message(MainWindow, f"Switch energy i_e curve is not available for <b>{transistor_list[m].name}</b>!")

        try:
            matplotlibwidget.axis.legend(fontsize=5)
            matplotlibwidget.axis.set(xlabel="Current in A",
                                      ylabel="Loss energy in J")
            matplotlibwidget.axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
            matplotlibwidget.axis.grid()
            matplotlibwidget.figure.canvas.draw_idle()

            matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                             color="Green", linewidth=1)
            matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)
        except:
            matplotlibwidget.axis.clear()
            matplotlibwidget.figure.canvas.draw_idle()

def plot_e_rr(transistor1, transistor2, transistor3, matplotlibwidget, t_j1, t_j2, t_j3, r_g_off1, r_g_off2, r_g_off3, v_supply1, v_supply2, v_supply3):
    """
    Calculate and plot diode reverse recovery energy i-e characteristic curves for all three transistors.

    Valid for a chosen junction temperature, gate resistor and supply voltage into a MatplotlibWidget

    :param transistor1: transistor object for transistor1
    :param transistor2: transistor object for transistor2
    :param transistor3: transistor object for transistor3
    :param matplotlibwidget: MatplotlibWidget object
    :param t_j1: junction temperature for transistor1
    :param t_j2: junction temperature for transistor2
    :param t_j3: junction temperature for transistor3
    :param r_g_off1: gate resistor for transistor1
    :param r_g_off2: gate resistor for transistor2
    :param r_g_off3: gate resistor for transistor3
    :param v_supply1: supply voltage for transistor1
    :param v_supply2: supply voltage for transistor2
    :param v_supply3: supply voltage for transistor3

    :return: None
    """
    annotations_list = []

    def clicked(event):
        if event.dblclick:
            click_event(event.button, event.xdata, event.ydata, matplotlibwidget, annotations_list)

    transistor_list = [transistor1, transistor2, transistor3]
    t_j_list = [t_j1, t_j2, t_j3]
    r_g_off_list = [r_g_off1, r_g_off2, r_g_off3]
    v_supply_list = [v_supply1, v_supply2, v_supply3]

    color_list = ["blue", "green", "red"]

    for m in range(len(transistor_list)):
        try:
            t_j_available_unfiltered = [i for i in [e_rr.t_j for e_rr in transistor_list[m].diode.e_rr]]
            t_j_available = []
            for i in t_j_available_unfiltered:
                if i not in t_j_available:
                    t_j_available.append(i)
            t_j_available.sort()

            v_supply_chosen = max([i for i in [e_rr.v_supply for e_rr in transistor_list[m].diode.e_rr]])

            if len(t_j_available) == 1:
                try:
                    transistor_list[m].wp.e_rr = transistor_list[m].calc_object_i_e(e_on_off_rr="e_rr",
                                                                                    t_j=t_j_available[0],
                                                                                    v_supply=v_supply_chosen,
                                                                                    r_g=r_g_off_list[m],
                                                                                    normalize_t_to_v=10)
                    vec_e_rr = transistor_list[m].wp.e_rr.graph_i_e[1] * v_supply_list[m] / v_supply_chosen
                    vec_i = transistor_list[m].wp.e_rr.graph_i_e[0]
                except:
                    transistor_list[m].wp.e_rr = transistor_list[m].get_object_i_e(
                        e_on_off_rr="e_rr", t_j=t_j_available[0], v_supply=v_supply_chosen, r_g=r_g_off_list[m],
                        v_g=min([i for i in [e_rr.v_g for e_rr in transistor_list[m].diode.e_rr] if i is not None]))

                    vec_e_rr = transistor_list[m].wp.e_rr.graph_i_e[1] * v_supply_list[m] / v_supply_chosen
                    vec_i = transistor_list[m].wp.e_rr.graph_i_e[0]

                label = f"{transistor_list[m].name}, T_j = {t_j_available[0]}°C"
                MainWindow.show_popup_message(MainWindow, f"Diode energy i_e curve for <b>{transistor_list[m].name}</b> only available for "
                                                          f"T_j = {t_j_available[0]}°C due to missing data!")

            else:
                r_g_rr_max_list = np.zeros_like(t_j_available)

                for i in range(len(t_j_available)):
                    r_e_object_rr = transistor_list[m].get_object_r_e_simplified(
                        e_on_off_rr="e_rr", t_j=t_j_available[i], v_g=max([i for i in [e_rr.v_g for e_rr in transistor_list[m].diode.e_rr] if i is not None]),
                        v_supply=max([i for i in [e_rr.v_supply for e_rr in transistor_list[m].diode.e_rr] if i is not None]),
                        normalize_t_to_v=10)
                    r_g_rr_max_list[i] = np.amax(r_e_object_rr.graph_r_e[0]) * 10000

                r_g_rr_max = floor(10 * min(r_g_rr_max_list) / 10000) / 10

                r_g_rr_available = np.linspace(0, r_g_rr_max, 10)

                vec_i = np.linspace(0, transistor_list[m].i_abs_max, 10)

                m_t_j_available, m_r_g_rr_available, m_i = np.meshgrid(t_j_available, r_g_rr_available, vec_i,
                                                                       indexing='ij')

                m_e_rr = np.zeros_like(m_t_j_available)

                for i in range(len(t_j_available)):
                    for j in range(len(r_g_rr_available)):
                        for k in range(len(vec_i)):
                            transistor_list[m].wp.e_rr = transistor_list[m].calc_object_i_e(
                                e_on_off_rr="e_rr", t_j=m_t_j_available[i, j, k], v_supply=v_supply_chosen,
                                r_g=m_r_g_rr_available[i, j, k], normalize_t_to_v=10)
                            m_e_rr[i, j, k] = np.interp(m_i[i, j, k], transistor_list[m].wp.e_rr.graph_i_e[0],
                                                        transistor_list[m].wp.e_rr.graph_i_e[1]) * v_supply_list[m] / v_supply_chosen * 1000000000

                points = (t_j_available, r_g_rr_available, vec_i)
                values = m_e_rr

                vec_e_rr = np.zeros_like(vec_i)

                for n in range(len(vec_i)):
                    point = ([t_j_list[m], r_g_off_list[m], vec_i[n]])
                    vec_e_rr[n] = interpn(points, values, point, bounds_error=False, fill_value=None) / 1000000000

                if t_j_list[m] < min(t_j_available) or t_j_list[m] > max(t_j_available):
                    label = f"{transistor_list[m].name} (data extrapolated)"
                else:
                    label = f"{transistor_list[m].name} (data interpolated)"

            matplotlibwidget.axis.plot(vec_i, vec_e_rr, label=label, color=color_list[m])

        except:
            MainWindow.show_popup_message(MainWindow, f"Diode energy i_e curve is not available for <b>{transistor_list[m].name}</b>!")

        try:
            matplotlibwidget.axis.legend(fontsize=5)
            matplotlibwidget.axis.set(xlabel="Current in A",
                                      ylabel="Loss energy in J")
            matplotlibwidget.axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
            matplotlibwidget.axis.grid()
            matplotlibwidget.figure.canvas.draw_idle()

            matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                             color="Green", linewidth=1)
            matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)
        except:
            matplotlibwidget.axis.clear()
            matplotlibwidget.figure.canvas.draw_idle()


def plot_channel(transistor1, transistor2, transistor3, matplotlibwidget, t_j1, t_j2, t_j3, v_g_on1, v_g_on2, v_g_on3,
                 v_g_off1, v_g_off2, v_g_off3, switch_diode):
    """
    Calculate and plot switch or diode channel v_i characteristic curves for all three transistors.

    Valid for a chosen junction temperature and gate voltage into a MatplotlibWidget.

    :param transistor1: transistor object for transistor1
    :param transistor2: transistor object for transistor2
    :param transistor3: transistor object for transistor3
    :param matplotlibwidget: MatplotlibWidget object
    :param t_j1: junction temperature for transistor1
    :param t_j2: junction temperature for transistor2
    :param t_j3: junction temperature for transistor3
    :param v_g_on1: gate turn-on voltage for transistor1
    :param v_g_on2: gate turn-on voltage for transistor2
    :param v_g_on3: gate turn-on voltage for transistor3
    :param v_g_off1: gate turn-off voltage for transistor1
    :param v_g_off2: gate turn-off voltage for transistor2
    :param v_g_off3: gate turn-off voltage for transistor3

    :return: None
    """
    annotations_list = []

    def clicked(event):
        if event.dblclick:
            click_event(event.button, event.xdata, event.ydata, matplotlibwidget, annotations_list)

    transistor_list = [transistor1, transistor2, transistor3]
    t_j_list = [t_j1, t_j2, t_j3]
    v_g_on_list = [v_g_on1, v_g_on2, v_g_on3]
    v_g_off_list = [v_g_off1, v_g_off2, v_g_off3]
    color_list = ["blue", "green", "red"]

    if switch_diode == "switch":
        for m in range(len(transistor_list)):
            try:
                dict = transistor_list[m].switch.convert_to_dict()

                channel = []
                for curve in dict["channel"]:
                    if curve["v_g"] == v_g_on_list[m]:
                        channel.append(curve)

                t_j_available = []
                for curve in channel:
                    if curve["t_j"] not in t_j_available:
                        t_j_available.append(curve["t_j"])
                t_j_available.sort()

                if len(t_j_available) == 1:
                    transistor_list[m].wp.switch_channel = transistor_list[m].get_object_v_i(
                        switch_or_diode="switch",
                        t_j=t_j_available[0],
                        v_g=v_g_on_list[m])

                    vec_v = transistor_list[m].wp.switch_channel.graph_v_i[0]
                    vec_i = transistor_list[m].wp.switch_channel.graph_v_i[1]
                    label = f"{transistor_list[m]}, T_j = {t_j_available[0]}"
                    MainWindow.show_popup_message(MainWindow, f"Switch channel v_i curve for <b>{transistor_list[m].name}</b> only available for T_j = "
                                                              f"{t_j_available[0]}°C due to missing data!")

                else:
                    vec_i = np.linspace(0, transistor_list[m].i_abs_max, 50)

                    m_t_j_available, m_i = np.meshgrid(t_j_available, vec_i, indexing='ij')

                    m_v = np.zeros_like(m_t_j_available)

                    for i in range(len(t_j_available)):
                        for j in range(len(vec_i)):
                            transistor_list[m].wp.switch_channel = transistor_list[m].get_object_v_i(
                                switch_or_diode="switch",
                                t_j=m_t_j_available[i, j],
                                v_g=v_g_on_list[m])

                            m_v[i, j] = np.interp(m_i[i, j], transistor_list[m].wp.switch_channel.graph_v_i[1],
                                                  transistor_list[m].wp.switch_channel.graph_v_i[0] * 1000000)

                    points = (t_j_available, vec_i)
                    values = m_v

                    vec_v = np.zeros_like(vec_i)

                    for n in range(len(vec_i)):
                        point = ([t_j_list[m], vec_i[n]])
                        vec_v[n] = interpn(points, values, point, bounds_error=False, fill_value=None) / 1000000

                    if t_j_list[m] < min(t_j_available) or t_j_list[m] > max(t_j_available):
                        label = f"{transistor_list[m].name} (data extrapolated)"
                    else:
                        label = f"{transistor_list[m].name} (data interpolated)"

                matplotlibwidget.axis.plot(vec_v, vec_i, label=label, color=color_list[m])

            except:
                MainWindow.show_popup_message(MainWindow, f"Switch channel v_i curve is not available for <b>{transistor_list[m].name}</b>!")

    elif switch_diode == "diode":
        for m in range(len(transistor_list)):
            try:
                dict = transistor_list[m].diode.convert_to_dict()

                channel = []
                for curve in dict["channel"]:
                    if curve["v_g"] == v_g_off_list[m]:
                        channel.append(curve)

                t_j_available = []
                for curve in channel:
                    if curve["t_j"] not in t_j_available:
                        t_j_available.append(curve["t_j"])
                t_j_available.sort()

                if len(t_j_available) == 1:
                    transistor_list[m].wp.switch_channel = transistor_list[m].get_object_v_i(
                        switch_or_diode="diode",
                        t_j=t_j_available[0],
                        v_g=v_g_off_list[m])

                    vec_v = transistor_list[m].wp.switch_channel.graph_v_i[0]
                    vec_i = transistor_list[m].wp.switch_channel.graph_v_i[1]
                    label = f"{transistor_list[m]}, T_j = {t_j_available[0]}"
                    MainWindow.show_popup_message(MainWindow,
                                                  f"Diode channel v_i curve for <b>{transistor_list[m].name}</b> only available for T_j = "
                                                  f"{t_j_available[0]}°C due to missing data!")

                else:
                    vec_i = np.linspace(0, transistor_list[m].i_abs_max, 50)

                    m_t_j_available, m_i = np.meshgrid(t_j_available, vec_i, indexing='ij')

                    m_v = np.zeros_like(m_t_j_available)

                    for i in range(len(t_j_available)):
                        for j in range(len(vec_i)):
                            transistor_list[m].wp.switch_channel = transistor_list[m].get_object_v_i(
                                switch_or_diode="diode",
                                t_j=m_t_j_available[i, j],
                                v_g=v_g_off_list[m])

                            m_v[i, j] = np.interp(m_i[i, j], transistor_list[m].wp.switch_channel.graph_v_i[1],
                                                  transistor_list[m].wp.switch_channel.graph_v_i[0] * 1000000)

                    points = (t_j_available, vec_i)
                    values = m_v

                    vec_v = np.zeros_like(vec_i)

                    for n in range(len(vec_v)):
                        point = ([t_j_list[m], vec_i[n]])
                        vec_v[n] = interpn(points, values, point, bounds_error=False, fill_value=None) / 1000000

                    if t_j_list[m] < min(t_j_available) or t_j_list[m] > max(t_j_available):
                        label = f"{transistor_list[m].name} (data extrapolated)"
                    else:
                        label = f"{transistor_list[m].name} (data interpolated)"

                matplotlibwidget.axis.plot(vec_v, vec_i, label=label, color=color_list[m])

            except:
                MainWindow.show_popup_message(MainWindow, f"Diode channel v_i curve is not available for <b>{transistor_list[m].name}</b>!")

    try:
        matplotlibwidget.axis.legend(fontsize=5)
        matplotlibwidget.axis.set(xlabel="Voltage in V",
                                  ylabel="Current in A")
        matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
        matplotlibwidget.axis.grid()
        matplotlibwidget.figure.canvas.draw_idle()

        matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                         color="Green", linewidth=1)
        matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)
    except:
        matplotlibwidget.axis.clear()
        matplotlibwidget.figure.canvas.draw_idle()

def plot_v_eoss(transistor1, transistor2, transistor3, matplotlibwidget):
    """
    Plot e_oss vs channel voltage for all three selected transistors in the comparison tools tab.

    :param transistor1:
    :param transistor2:
    :param transistor3:
    :param matplotlibwidget: matplotlibwidget object
    :return:
    """
    annotations_list = []

    def clicked(event):
        if event.dblclick:
            click_event(event.button, event.xdata, event.ydata, matplotlibwidget, annotations_list)

    transistor_list = [transistor1, transistor2, transistor3]
    color_list = ["blue", "green", "red"]

    for m in range(len(transistor_list)):
        try:
            v_eoss = transistor_list[m].calc_v_eoss()
            matplotlibwidget.axis.plot(v_eoss[0], v_eoss[1], label=transistor_list[m].name, color=color_list[m])
        except:
            pass
            MainWindow.show_popup_message(MainWindow, f"Output capacitance energy curves are not available for <b>{transistor_list[m].name}</b>!")

    try:
        matplotlibwidget.axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        matplotlibwidget.axis.legend(fontsize=5)
        matplotlibwidget.axis.set(xlabel="Voltage in V",
                                  ylabel="Energy in J")
        matplotlibwidget.axis.grid()
        matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
        matplotlibwidget.figure.canvas.draw_idle()

        matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                         color="Green", linewidth=1)

        matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)
    except:
        matplotlibwidget.axis.clear()
        matplotlibwidget.figure.canvas.draw_idle()

def plot_v_qoss(transistor1, transistor2, transistor3, matplotlibwidget):
    """
    Plot q_oss vs channel voltage for all three selected transistors in the comparison tools tab.

    :param transistor1:
    :param transistor2:
    :param transistor3:
    :param matplotlibwidget: matplotlibwidget object

    :return:
    """
    annotations_list = []

    def clicked(event):
        if event.dblclick:
            click_event(event.button, event.xdata, event.ydata, matplotlibwidget, annotations_list)

    transistor_list = [transistor1, transistor2, transistor3]
    color_list = ["blue", "green", "red"]

    for m in range(len(transistor_list)):
        try:
            v_qoss = transistor_list[m].calc_v_qoss()
            matplotlibwidget.axis.plot(v_qoss[0], v_qoss[1], label=transistor_list[m].name, color=color_list[m])

        except:
            MainWindow.show_popup_message(MainWindow, f"Output capacitance charge curves are not available for <b>{transistor_list[m].name}</b>!")

    try:
        matplotlibwidget.axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        matplotlibwidget.axis.legend(fontsize=5)
        matplotlibwidget.axis.set(xlabel="Voltage in V",
                                  ylabel="Charge in C")
        matplotlibwidget.axis.grid()
        matplotlibwidget.axis.set_position([0.12, 0.2, 0.9, 0.7])
        matplotlibwidget.figure.canvas.draw_idle()
        matplotlibwidget.cursor = Cursor(matplotlibwidget.axis, horizOn=True, vertOn=True, useblit=True,
                                         color="Green", linewidth=1)

        matplotlibwidget.figure.canvas.mpl_connect("button_press_event", clicked)

    except:
        matplotlibwidget.axis.clear()
        matplotlibwidget.figure.canvas.draw_idle()
