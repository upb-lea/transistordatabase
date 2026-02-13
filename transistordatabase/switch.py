"""Switch class."""
# Python standard libraries
from __future__ import annotations
from matplotlib import pyplot as plt
from typing import List, Dict, Tuple
from scipy.spatial import distance
import numpy as np

# Local libraries
from transistordatabase.helper_functions import get_img_raw_data, isvalid_dict
from transistordatabase.checker_functions import check_keys
from transistordatabase.data_classes import FosterThermalModel, ChannelData, SwitchEnergyData, LinearizedModel, TemperatureDependResistance, \
    GateChargeCurve, SOA
from transistordatabase.exceptions import MissingDataError
from transistordatabase.plot_functions import plot_soa_lib

def append_valid_datasets(target_list, datasets, validation_type, data_class):
    """
    Append valid datasets to the target list.

    :param target_list: The list to append valid datasets to
    :param datasets: The datasets to validate and append
    :param validation_type: The type of validation to perform
    :param data_class: The class to instantiate for valid datasets
    """
    if isinstance(datasets, list):
        for dataset in datasets:
            try:
                if isvalid_dict(dataset, validation_type):
                    target_list.append(data_class(dataset))
            except KeyError as error:
                handle_key_error(error, datasets, dataset, validation_type)
            except ValueError as error:
                handle_value_error(error, datasets, dataset, validation_type)
    elif isvalid_dict(datasets, validation_type):
        target_list.append(data_class(datasets))

def handle_key_error(error, dict_list, dataset, validation_type):
    """
    Handle KeyError by raising an error with additional context.

    :param error: The KeyError to handle
    :param dict_list: The list of dictionaries being processed
    :param dataset: The current dataset being processed
    :param validation_type: The type of validation being performed
    """
    if not error.args:
        error.args = ('',)  # This syntax is necessary because error.args is a tuple
    error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                  f"{validation_type} dictionaries: ",) + error.args
    raise

def handle_value_error(error, dict_list, dataset, validation_type):
    """
    Handle ValueError by raising an error with additional context.

    :param error: The ValueError to handle
    :param dict_list: The list of dictionaries being processed
    :param dataset: The current dataset being processed
    :param validation_type: The type of validation being performed
    """
    raise Exception(f"for index [{str(dict_list.index(dataset))}] in list of {validation_type} dictionaries:" + str(error))

class Switch:
    """
    Data associated with the switching-characteristics of a MOSFET/SiC-MOSFET or IGBT.

    Can contain multiple channel-, e_on- and e_off-datasets.
    """

    # Metadata
    comment: str | None  #: Comment if any to be specified (Optional key)
    manufacturer: str | None  #: Name of the manufacturer (Optional key)
    technology: str | None  #: Semiconductor technology. e.g. IGBT3/IGBT4/IGBT7  (Optional key)
    # These are documented in their respective class definitions.
    thermal_foster: FosterThermalModel  #: Transient thermal_foster model. (Optional key)
    channel: List[ChannelData] | None  #: Switch channel voltage and current data.
    e_on: List[SwitchEnergyData] | None  #: Switch on energy data.
    e_off: List[SwitchEnergyData] | None  #: Switch of energy data.
    e_on_meas: List[SwitchEnergyData] | None  #: Switch on energy data.
    e_off_meas: List[SwitchEnergyData] | None  #: Switch on energy data.
    linearized_switch: List[LinearizedModel] | None  #: Static data valid for a specific operating point.
    r_channel_th: List[TemperatureDependResistance] | None  #: Temperature dependant on resistance.
    charge_curve: List[GateChargeCurve] | None  #: Gate voltage dependant charge characteristics
    t_j_max: float   #: Maximum junction temperature. Units in °C (Mandatory key)
    soa: List[SOA] | None  #: Safe operating area of switch

    def __init__(self, switch_args):
        """
        Initialize the Switch object.

        :param switch_args: argument to be passed for initialization

        :raises KeyError: Expected during the channel/e_on/e_off instance initialization
        :raises ValueError: Expected during the channel/e_on/e_off instance initialization

        .. todo:: Is this the right behavior or should the 'thermal_foster' attribute be left empty instead?
        """
        # Current behavior on empty 'foster' dictionary: thermal_foster object is still created but with empty attributes.
        # ToDo: Is this the right behavior or should the 'thermal_foster' attribute be left empty instead?
        self.thermal_foster = FosterThermalModel(switch_args.get('thermal_foster'))
        if isvalid_dict(switch_args, 'Switch'):
            self.t_j_max = switch_args.get('t_j_max')
            self.comment = switch_args.get('comment')
            self.manufacturer = switch_args.get('manufacturer')
            self.technology = switch_args.get('technology')
            # This currently accepts dictionaries and lists of dictionaries. Validity is only checked by keys and
            # not their values.

            self.channel = []
            append_valid_datasets(self.channel, switch_args.get('channel'), 'Switch_ChannelData', ChannelData)

            self.e_on = []
            append_valid_datasets(self.e_on, switch_args.get('e_on'), 'SwitchEnergyData', SwitchEnergyData)

            self.e_off = []
            append_valid_datasets(self.e_off, switch_args.get('e_off'), 'SwitchEnergyData', SwitchEnergyData)

            self.e_on_meas = []
            append_valid_datasets(self.e_on_meas, switch_args.get('e_on_meas'), 'SwitchEnergyData', SwitchEnergyData)

            self.e_off_meas = []
            append_valid_datasets(self.e_off_meas, switch_args.get('e_off_meas'), 'SwitchEnergyData', SwitchEnergyData)

            self.linearized_switch = []
            append_valid_datasets(self.linearized_switch, switch_args.get('linearized_switch'), 'Switch_LinearizedModel', LinearizedModel)

            self.r_channel_th = []
            append_valid_datasets(self.r_channel_th, switch_args.get('r_channel_th'), 'TemperatureDependResistance', TemperatureDependResistance)

            self.charge_curve = []
            append_valid_datasets(self.charge_curve, switch_args.get('charge_curve'), 'GateChargeCurve', GateChargeCurve)

            self.soa = []
            append_valid_datasets(self.soa, switch_args.get('soa'), 'SOA', SOA)

        else:  # Can be constructed from empty or 'None' argument dictionary since no attributes are mandatory.
            self.comment = None
            self.manufacturer = None
            self.technology = None
            self.channel = []
            self.e_on = []
            self.e_off = []
            self.e_on_meas = []
            self.e_off_meas = []
            self.linearized_switch = []
            self.r_channel_th = []
            self.charge_curve = []

    def convert_to_dict(self) -> Dict:
        """
        Convert Switch object into dict datatype.

        :return: Switch object of dict type
        :rtype: dict
        """
        d = dict(vars(self))
        d['thermal_foster'] = self.thermal_foster.convert_to_dict()
        d['channel'] = [c.convert_to_dict() for c in self.channel]
        d['e_on'] = [e.convert_to_dict() for e in self.e_on]
        d['e_off'] = [e.convert_to_dict() for e in self.e_off]
        d['e_on_meas'] = [e.convert_to_dict() for e in self.e_on_meas]
        d['e_off_meas'] = [e.convert_to_dict() for e in self.e_off_meas]
        d['linearized_switch'] = [lsw.convert_to_dict() for lsw in self.linearized_switch]
        d['r_channel_th'] = [tr.convert_to_dict() for tr in self.r_channel_th]
        d['charge_curve'] = [q_v.convert_to_dict() for q_v in self.charge_curve]
        d['soa'] = [c.convert_to_dict() for c in self.soa]
        return d

    def find_next_gate_voltage(self, req_gate_vltgs: Dict, export_type: str, check_specific_curves: List = None,
                               switch_loss_dataset_type: str = "graph_i_e") -> Dict:
        """
        Find the switch gate voltage nearest to the specified values from the available gate voltages in curve datasets.

        Applicable to either plecs exporter or gecko exporter

        :param req_gate_vltgs: the provided gate voltages for find the nearest neighbour to the corresponding key-value pairs
        :type req_gate_vltgs: dict
        :param export_type: either 'gecko' or 'plecs'
        :type export_type: str
        :param check_specific_curves: indexes of chosen energy curve to be skipped are provided here
        :type check_specific_curves: list(list, list)
        :param switch_loss_dataset_type: dataset curve type to be specified

        :return: v_g_channel, v_supply, v_g_on, v_g_off
        :rtype: int
        """
        if check_specific_curves is None:
            check_specific_curves = [[], []]
        check_keys(req_gate_vltgs, export_type, 'switch')
        # recheck channel characteristics curves at v_supply
        channel_v_gs = np.array([0 if chan.v_g is None else chan.v_g for chan in self.channel])
        v_gs = min(channel_v_gs, key=lambda x: abs(x - req_gate_vltgs['v_channel_gs']))
        req_gate_vltgs['v_channel_gs'] = v_gs
        # gather e_on loss curves at required dataset_type and check for none
        e_ons = [e for i, e in enumerate(self.e_on) if e.dataset_type == switch_loss_dataset_type and \
                 (not any(check_specific_curves[0]) or i in check_specific_curves[0])]
        if not e_ons:
            raise MissingDataError(1102)
        # gather e_off loss curves at required dataset_type and check for none
        e_offs = [e for i, e in enumerate(self.e_off) if e.dataset_type == switch_loss_dataset_type and \
                  (not any(check_specific_curves[1]) or i in check_specific_curves[1])]
        if not e_offs:
            raise MissingDataError(1103)

        if export_type == 'plecs':
            # recheck turn on energy loss curves at v_on
            e_on_v_gs = np.array([0 if e.v_g is None else e.v_g for e in e_ons])
            v_on = min(e_on_v_gs, key=lambda x: abs(x - req_gate_vltgs['v_g_on']))
            req_gate_vltgs['v_g_on'] = v_on
            # recheck turn off energy loss curves at v_off
            e_off_v_gs = np.array([0 if e.v_g is None else e.v_g for e in e_offs])
            v_off = min(e_off_v_gs, key=lambda x: abs(x - req_gate_vltgs['v_g_off']))
            req_gate_vltgs['v_g_off'] = v_off

        if export_type == 'gecko':
            # recheck turn on energy loss curves at v_on
            e_on_v_gs = list()
            for e in e_ons:
                if e.v_g is None:
                    e.v_g = 0
                e_on_v_gs.append(e.v_g)
            v_on = min(e_on_v_gs, key=lambda x: abs(x - req_gate_vltgs['v_g_on']))
            req_gate_vltgs['v_g_on'] = v_on
            e_on_v_supply = [e.v_supply if e.v_g == v_on else None for e in e_ons]  # removed numpy array
            v_on_supply = min(e_on_v_supply, key=lambda x: abs(x - req_gate_vltgs['v_supply']))
            req_gate_vltgs['v_supply'] = v_on_supply

            # recheck turn off energy loss curves at v_off
            e_off_v_gs = list()
            for e in e_offs:
                if e.v_g is None:
                    e.v_g = 0
                e_off_v_gs.append(e.v_g)
            v_off = min(e_off_v_gs, key=lambda x: abs(x - req_gate_vltgs['v_g_off']))
            req_gate_vltgs['v_g_off'] = v_off
            e_off_v_supply = [e.v_supply if e.v_g == v_off else None for e in e_offs]
            v_off_supply = min(e_off_v_supply, key=lambda x: abs(x - req_gate_vltgs['v_supply']))
            if not req_gate_vltgs['v_supply'] == v_off_supply:
                raise ValueError("Not implemented: Mismatch in v_supply for the selected loss curves")

        print("--Switch Recheck--")
        for key, value in req_gate_vltgs.items():
            print(key + ': ', value)
        return req_gate_vltgs.values()

    def find_approx_wp(self, t_j: float, v_g: float, normalize_t_to_v: float = 10,
                       switch_energy_dataset_type: str = "graph_i_e") \
            -> Tuple[ChannelData, SwitchEnergyData, SwitchEnergyData]:
        """
        Search for the smallest distance to stored object value and returns this working point.

        :param t_j: junction temperature
        :type t_j: float
        :param v_g: gate voltage
        :type v_g: float
        :param normalize_t_to_v: ratio between t_j and v_g. e.g. 10 means 10°C is same difference as 1V
        :type normalize_t_to_v: float
        :param switch_energy_dataset_type: preferred dataset_type (single, graph_r_e, graph_i_e) for e_on and e_off
        :type switch_energy_dataset_type: str

        :raises KeyError: Raised when there no data for the specified SwitchEnergyData_dataset_type

        :return: channel-object, e_on-object, e_off-object
        :rtype: tuple[Transistor.ChannelData, Transistor.SwitchEnergyData, Transistor.SwitchEnergyData]
        """
        # Normalize t_j to v_g for distance metric
        node = np.array([[t_j / normalize_t_to_v, v_g]])
        # Find closest channeldata
        channeldata_t_js = np.array([chan.t_j for chan in self.channel])
        channeldata_v_gs = np.array([0 if chan.v_g is None else chan.v_g for chan in self.channel])
        nodes = np.array([channeldata_t_js / normalize_t_to_v, channeldata_v_gs]).transpose()
        index_channeldata = distance.cdist(node, nodes).argmin()

        # Find closest e_on
        e_ons = [e for e in self.e_on if e.dataset_type == switch_energy_dataset_type]
        if not e_ons:
            raise KeyError(f"There is no e_on data with type {switch_energy_dataset_type} for this Switch object.")
        e_on_t_js = np.array([e.t_j for e in e_ons])
        e_on_v_gs = np.array([0 if e.v_g is None else e.v_g for e in e_ons])
        nodes = np.array([e_on_t_js / normalize_t_to_v, e_on_v_gs]).transpose()
        index_e_on = distance.cdist(node, nodes).argmin()
        # Find closest e_off
        e_offs = [e for e in self.e_off if e.dataset_type == switch_energy_dataset_type]
        if not e_offs:
            raise KeyError(f"There is no e_off data with type {switch_energy_dataset_type} for this Switch object.")
        e_off_t_js = np.array([e.t_j for e in e_offs])
        e_off_v_gs = np.array([0 if e.v_g is None else e.v_g for e in e_offs])
        nodes = np.array([e_off_t_js / normalize_t_to_v, e_off_v_gs]).transpose()
        index_e_off = distance.cdist(node, nodes).argmin()
        print("run switch.find_approx_wp: closest working point for t_j = {0} °C and v_g = {1} V:".format(t_j, v_g))
        print(f"channel: t_j = {self.channel[index_channeldata].t_j} °C and v_g = {self.channel[index_channeldata].v_g} V")
        print(f"eon:     t_j = {e_ons[index_e_on].t_j} °C and v_g = {e_ons[index_e_on].v_g} V")
        print(f"eoff:    t_j = {e_offs[index_e_off].t_j} °C and v_g = {e_offs[index_e_off].v_g} V")

        return self.channel[index_channeldata], e_ons[index_e_on], e_offs[index_e_off]

    def plot_channel_data_vge(self, gatevoltage: float) -> None:
        """
        Plot channel data with a chosen gate-voltage.

        :param gatevoltage: gatevoltage at which the channel curves are selected and plotted
        :type gatevoltage: float

        :return: Respective plots are displayed
        :rtype: None
        """
        plt.figure()
        for i_channel in np.array(range(0, len(self.channel))):
            if self.channel[i_channel].v_g == gatevoltage:
                labelplot = f"vg = {self.channel[i_channel].v_g} V, T_J = {self.channel[i_channel].t_j} °C"
                plt.plot(self.channel[i_channel].graph_v_i[0], self.channel[i_channel].graph_v_i[1],
                         label=labelplot)

        plt.legend()
        plt.xlabel('Voltage in V')
        plt.ylabel('Current in A')
        plt.grid()
        plt.show()

    def plot_channel_data_temp(self, temperature: float) -> None:
        """
        Plot channel data with chosen temperature.

        :param temperature: junction temperature at which the channel curves are selected and plotted
        :param temperature: float

        :return: Respective plots are displayed
        :rtype: None
        """
        plt.figure()
        for i_channel in np.array(range(0, len(self.channel))):
            if self.channel[i_channel].t_j == temperature:
                labelplot = f"vg = {self.channel[i_channel].v_g} V, T_J = {self.channel[i_channel].t_j} °C"
                plt.plot(self.channel[i_channel].graph_v_i[0], self.channel[i_channel].graph_v_i[1],
                         label=labelplot)

        plt.legend()
        plt.xlabel('Voltage in V')
        plt.ylabel('Current in A')
        plt.grid()
        plt.show()

    def plot_all_channel_data(self, buffer_req: bool = False):
        """
        Plot all switch channel characteristic curves.

        :param buffer_req: internally required for generating virtual datasheets
        :param buffer_req: bool

        :return: Respective plots are displayed
        """
        # ToDo: only 12(?) colors available. Change linestyle for more curves.
        categorize_with_temp_plots = {}
        categorize_with_vgs_plots = {}
        categorized_plots = {}
        plt.figure()
        if len(self.channel) > 5:  # 5 - expecting only -40°,25°,50°,125°,175° curves at gate voltage 15V or 25° curves at 20,15,12,10,8V
            count = 0
            for channel in self.channel:
                try:
                    categorize_with_temp_plots[channel.t_j].append(channel)
                except KeyError:
                    categorize_with_temp_plots[channel.t_j] = [channel]
                try:
                    categorize_with_vgs_plots[channel.v_g].append(channel)
                except KeyError:
                    categorize_with_vgs_plots[channel.v_g] = [channel]
            for key, curve_list in categorize_with_temp_plots.items():
                if len(curve_list) > 1:
                    count += 1
                    for curve in curve_list:
                        plot_label = "$V_{{g}}$ = {0} V ".format(curve.v_g)
                        plt.plot(curve.graph_v_i[0], curve.graph_v_i[1], label=plot_label)
                    plt.legend(fontsize=8)
                    plt.xlabel('Voltage in V')
                    plt.ylabel('Current in A')
                    # plt.title('Channel at $T_{{J}}$ = {0} °C'.format(key))
                    plt.grid()
                    if buffer_req:
                        categorized_plots |= {key: get_img_raw_data(plt)}
                        plt.clf()
                    else:
                        plt.show()
            for key, curve_list in categorize_with_vgs_plots.items():
                if len(curve_list) > count:
                    for curve in curve_list:
                        plot_label = "$T_{{j}}$ = {0} °C".format(curve.t_j)
                        plt.plot(curve.graph_v_i[0], curve.graph_v_i[1], label=plot_label)
                    plt.legend(fontsize=8)
                    plt.xlabel('Voltage in V')
                    plt.ylabel('Current in A')
                    # plt.title('Channel at $V_{{g}}$ = {0} V'.format(key))
                    plt.grid()
                    if buffer_req:
                        categorized_plots |= {key: get_img_raw_data(plt)}
                        plt.clf()
                    else:
                        plt.show()
        else:
            for i_channel in np.array(range(0, len(self.channel))):
                plot_label = "$V_{{g}}$ = {0} V, $T_{{J}}$ = {1} °C".format(self.channel[i_channel].v_g, self.channel[i_channel].t_j)
                plt.plot(self.channel[i_channel].graph_v_i[0], self.channel[i_channel].graph_v_i[1], label=plot_label)
            plt.legend(fontsize=8)
            plt.xlabel('Voltage in V')
            plt.ylabel('Current in A')
            plt.grid()
            if buffer_req:
                return get_img_raw_data(plt)
            else:
                plt.show()
        return categorized_plots

    def plot_energy_data(self, buffer_req: bool = False):
        """
        Plot all switch energy i-e characteristic curves which are extracted from the manufacturer datasheet.

        :param buffer_req: internally required for generating virtual datasheets
        :param buffer_req: bool

        :return: Respective plots are displayed
        """
        e_on_i_e_curve_count, e_off_i_e_curve_count = [0, 0]
        for i_energy_data in np.array(range(0, len(self.e_on))):
            if self.e_on[i_energy_data].dataset_type == 'graph_i_e':
                e_on_i_e_curve_count += 1
        for i_energy_data in np.array(range(0, len(self.e_off))):
            if self.e_off[i_energy_data].dataset_type == 'graph_i_e':
                e_off_i_e_curve_count += 1
        if e_on_i_e_curve_count and e_on_i_e_curve_count == e_off_i_e_curve_count:
            plt.figure()
            # look for e_on losses
            for i_energy_data in np.array(range(0, len(self.e_on))):
                if self.e_on[i_energy_data].dataset_type == 'graph_i_e':
                    labelplot = "$e_{{on}}$: $V_{{supply}}$ = {0} V, $V_{{g}}$ = {1} V, $T_{{J}}$ = {2} °C, $R_{{g}}$ = {3} Ohm".format(
                        self.e_on[i_energy_data].v_supply, self.e_on[i_energy_data].v_g, self.e_on[i_energy_data].t_j, self.e_on[i_energy_data].r_g)
                    plt.plot(self.e_on[i_energy_data].graph_i_e[0], self.e_on[i_energy_data].graph_i_e[1], label=labelplot)
                    plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
                    plt.yticks(rotation=90)
            # look for e_off losses
            for i_energy_data in np.array(range(0, len(self.e_off))):
                if self.e_off[i_energy_data].dataset_type == 'graph_i_e':
                    labelplot = "$e_{{off}}$: $V_{{supply}}$ = {0} V, $V_{{g}}$ = {1} V, $T_{{J}}$ = {2} °C, $R_{{g}}$ = {3} Ohm".format(
                        self.e_off[i_energy_data].v_supply, self.e_off[i_energy_data].v_g, self.e_off[i_energy_data].t_j, self.e_off[i_energy_data].r_g)
                    plt.plot(self.e_off[i_energy_data].graph_i_e[0], self.e_off[i_energy_data].graph_i_e[1], label=labelplot)
                    plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
                    plt.yticks(rotation=90)
            plt.legend(fontsize=5)
            plt.xlabel('Current in A')
            plt.ylabel('Loss energy in J')
            plt.grid()
            if buffer_req:
                return get_img_raw_data(plt)
            else:
                plt.show()
        else:
            print("Switch energy i_e curves are not available for the chosen transistor")
            return None

    def plot_energy_data_r(self, buffer_req: bool = False):
        """
        Plot all switch energy r-e characteristic curves.

        :param buffer_req: internally required for generating virtual datasheets
        :param buffer_req: bool

        :return: Respective plots are displayed
        """
        e_on_r_e_curve_count, e_off_r_e_curve_count = [0, 0]
        for i_energy_data in np.array(range(0, len(self.e_on))):
            if self.e_on[i_energy_data].dataset_type == 'graph_r_e':
                e_on_r_e_curve_count += 1
        for i_energy_data in np.array(range(0, len(self.e_off))):
            if self.e_off[i_energy_data].dataset_type == 'graph_r_e':
                e_off_r_e_curve_count += 1
        if e_on_r_e_curve_count and e_on_r_e_curve_count == e_off_r_e_curve_count:
            plt.figure()
            # look for e_on losses
            for i_energy_data in np.array(range(0, len(self.e_on))):
                if self.e_on[i_energy_data].dataset_type == 'graph_r_e':
                    labelplot = "$e_{{on}}$: $V_{{supply}}$ = {0} V, $V_{{g}}$ = {1} V, $T_{{J}}$ = {2} °C, $i_{{ch}}$ = {3} A".format(
                        self.e_on[i_energy_data].v_supply, self.e_on[i_energy_data].v_g, self.e_on[i_energy_data].t_j, self.e_on[i_energy_data].i_x)
                    plt.plot(self.e_on[i_energy_data].graph_r_e[0], self.e_on[i_energy_data].graph_r_e[1], label=labelplot)
                    plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            # look for e_off losses
            for i_energy_data in np.array(range(0, len(self.e_off))):
                if self.e_off[i_energy_data].dataset_type == 'graph_r_e':
                    labelplot = "$e_{{off}}$: $V_{{supply}}$ = {0} V, $V_{{g}}$ = {1} V, $T_{{J}}$ = {2} °C, $i_{{ch}}$ = {3} A".format(
                        self.e_off[i_energy_data].v_supply, self.e_off[i_energy_data].v_g, self.e_off[i_energy_data].t_j, self.e_off[i_energy_data].i_x)
                    plt.plot(self.e_off[i_energy_data].graph_r_e[0], self.e_off[i_energy_data].graph_r_e[1], label=labelplot)
                    plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            plt.legend(fontsize=5)
            plt.xlabel('External Gate Resistor in Ohm')
            plt.ylabel('Loss energy in J')
            plt.grid()
            if buffer_req:
                return get_img_raw_data(plt)
            else:
                plt.show()
        else:
            print("Switch energy r_e curves are not available for the chosen transistor")
            return None

    def plot_energy_data_t(self, buffer_req: bool = False):
        """
        Plot all switch energy vs Tj characteristic curves.

        :param buffer_req: internally required for generating virtual datasheets
        :param buffer_req: bool

        :return: Respective plots are displayed
        """
        e_on_t_e_curve_count, e_off_t_e_curve_count = [0, 0]
        for i_energy_data in np.array(range(0, len(self.e_on))):
            if self.e_on[i_energy_data].dataset_type == 'graph_t_e':
                e_on_t_e_curve_count += 1
        for i_energy_data in np.array(range(0, len(self.e_off))):
            if self.e_off[i_energy_data].dataset_type == 'graph_t_e':
                e_off_t_e_curve_count += 1
        if e_on_t_e_curve_count and e_on_t_e_curve_count == e_off_t_e_curve_count:
            plt.figure()
            # look for e_on losses
            for i_energy_data in np.array(range(0, len(self.e_on))):
                if self.e_on[i_energy_data].dataset_type == 'graph_t_e':
                    labelplot = "$e_{{on}}$: $V_{{supply}}$ = {0} V, $V_{{g}}$ = {1} V, $R_{{g}}$ = {2} Ohm, $i_{{ch}}$ = {3} A".format(
                        self.e_on[i_energy_data].v_supply, self.e_on[i_energy_data].v_g, self.e_on[i_energy_data].r_g, self.e_on[i_energy_data].i_x)
                    plt.plot(self.e_on[i_energy_data].graph_t_e[0], self.e_on[i_energy_data].graph_t_e[1], label=labelplot)
                    plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            # look for e_off losses
            for i_energy_data in np.array(range(0, len(self.e_off))):
                if self.e_off[i_energy_data].dataset_type == 'graph_t_e':
                    labelplot = "$e_{{off}}$: $V_{{supply}}$ = {0} V, $V_{{g}}$ = {1} V, $R_{{g}}$ = {2} Ohm, $i_{{ch}}$ = {3} A".format(
                        self.e_off[i_energy_data].v_supply, self.e_off[i_energy_data].v_g, self.e_off[i_energy_data].r_g, self.e_off[i_energy_data].i_x)
                    plt.plot(self.e_off[i_energy_data].graph_t_e[0], self.e_off[i_energy_data].graph_t_e[1], label=labelplot)
                    plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            plt.legend(fontsize=5)
            plt.xlabel('Junction Temperature in °C')
            plt.ylabel('Loss energy in J')
            plt.grid()
            if buffer_req:
                return get_img_raw_data(plt)
            else:
                plt.show()
        else:
            print("Switch energy t_e curves are not available for the chosen transistor")
            return None
    
    def plot_all_on_resistance_curves(self, buffer_req: bool = False):
        """
        Plot and convert Temperature dependent on-resistance plots in raw data format. Helper function.

        :param buffer_req: internally required for generating virtual datasheets

        :return: Respective plots are displayed
        """
        if not self.r_channel_th:
            return None
        fig = plt.figure()
        ax = fig.add_subplot(111)
        if isinstance(self.r_channel_th, list) and self.r_channel_th:
            for curve in self.r_channel_th:
                line1, = curve.get_plots(ax)
        plt.xlabel('Junction Temperature [C°]')
        y_label = 'On Resistance [Ohm]' if self.r_channel_th[0].dataset_type == 't_r' else 'On Resistance [Ohm]- Normalized'
        plt.ylabel(y_label)
        props = dict(fill=False, edgecolor='black', linewidth=1)
        if len(self.r_channel_th) == 1:
            r_on_condition = '\n'.join(["conditions: ", "$V_{g}$ = " + str(self.r_channel_th[0].v_g) + " V", "$I_{channel}$= " + \
                                        str(self.r_channel_th[0].i_channel) + " A"])
            ax.text(0.1, 0.9, r_on_condition, transform=ax.transAxes, fontsize='small', bbox=props, ha='left', va='top')
        else:
            plt.legend(fontsize=8)
            r_on_condition = '\n'.join(["conditions: ", "$I_{channel} $ =" + str(self.r_channel_th[0].i_channel) + " A"])
            ax.text(0.65, 0.1, r_on_condition, transform=ax.transAxes, fontsize='small', bbox=props, ha='left', va='bottom')
        plt.grid()
        if buffer_req:
            return get_img_raw_data(plt)
        else:
            plt.show()

    def plot_all_charge_curves(self, buffer_req: bool = False):
        """
        Plot and convert gate emitter/source voltage dependant gate charge plots in raw data format. Helper function.

        :param buffer_req: internally required for generating virtual datasheets

        :return: Respective plots are displayed
        """
        if not self.charge_curve:
            return None
        fig = plt.figure()
        ax = fig.add_subplot(111)
        if isinstance(self.charge_curve, list) and self.charge_curve:
            for curve in self.charge_curve:
                line1, = curve.get_plots(ax)
        plt.xlabel('Gate Charge, $Q_{G} [nC]$')
        plt.ylabel('Gate source Voltage, $V_{gs} [V]$')
        props = dict(fill=False, edgecolor='black', linewidth=1)
        if len(self.charge_curve) == 1:
            charge_condition = '\n'.join(["conditions: ", "$I_{{channel}}$ = {0} [A]".format(self.charge_curve[0].i_channel),
                                          "$V_{{supply}}$= {0} [V]".format(self.charge_curve[0].v_supply),
                                          "$T_{{j}}$ = {0} [°C]".format(self.charge_curve[0].t_j),
                                          "$I_{{g}}$ = {0} ".format('NA' if self.charge_curve[0].i_g is None else (str(self.charge_curve[0].i_g) + ' [A]'))])
            ax.text(0.05, 0.95, charge_condition, transform=ax.transAxes, fontsize='small', bbox=props, ha='left', va='top')
        else:
            plt.legend(fontsize=8)
            charge_condition = '\n'.join(["conditions: ", "$I_{{channel}}$ = {0} [A]".format(self.charge_curve[0].i_channel),
                                          "$T_{{j}}$ = {0} [°C]".format(self.charge_curve[0].t_j),
                                          "$I_{{g}}$ = {0} ".format('NA' if self.charge_curve[0].i_g is None else (str(self.charge_curve[0].i_g) + ' [A]'))])
            ax.text(0.65, 0.1, charge_condition, transform=ax.transAxes, fontsize='small', bbox=props, ha='left', va='bottom')
        plt.grid()
        if buffer_req:
            return get_img_raw_data(plt)
        else:
            plt.show()

    def plot_soa(self, buffer_req: bool = False):
        """
        Plot and convert safe operating region characteristic plots in raw data format. Helper function.

        :param buffer_req: internally required for generating virtual datasheets

        :return: Respective plots are displayed
        """
        return plot_soa_lib(self.soa, buffer_req)

    def collect_data(self) -> Dict:
        """
        Collect switch data in form of dictionary for generating virtual datasheet.

        :return: Switch data in form of dictionary
        :rtype: dict
        """
        switch_data = {}
        switch_data['plots'] = {'channel_plots': self.plot_all_channel_data(True),
                                'energy_plots': self.plot_energy_data(True), 'energy_plots_r': self.plot_energy_data_r(True),
                                'energy_plots_t': self.plot_energy_data_t(True),
                                'r_channel_th_plot': self.plot_all_on_resistance_curves(True), 'charge_curve': self.plot_all_charge_curves(True),
                                'soa': self.plot_soa(True)}
        for attr in dir(self):
            if attr == 'thermal_foster':
                switch_data.update(getattr(self, attr).collect_data())
            elif not callable(getattr(self, attr)) and not attr.startswith("__") and not \
                    isinstance(getattr(self, attr), (list, np.ndarray, dict)) and (getattr(self, attr) is not None) and not getattr(self, attr) == "":
                switch_data[attr.capitalize()] = getattr(self, attr)
        return switch_data
