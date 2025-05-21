"""Diode class."""
# Python standard libraries
from matplotlib import pyplot as plt
from scipy.spatial import distance
import numpy as np
import logging

# Local libraries
from transistordatabase.helper_functions import get_img_raw_data, isvalid_dict
from transistordatabase.checker_functions import check_keys
from transistordatabase.data_classes import FosterThermalModel, ChannelData, SwitchEnergyData, LinearizedModel, SOA
from transistordatabase.exceptions import MissingDataError

logger = logging.getLogger(__name__)

class Diode:
    """Data associated with the (reverse) diode-characteristics of a MOSFET/SiC-MOSFET or IGBT. Can contain multiple channel- and e_rr- datasets."""

    # Metadata
    comment: str | None  #: Comment if any specified by the user. (Optional key)
    manufacturer: str | None  #: Name of the manufacturer. (Optional key)
    technology: str | None  #: Semiconductor technology. e.g. IGBT3/IGBT4/IGBT7. (Optional key)
    # These are documented in their respective class definitions.
    thermal_foster: FosterThermalModel | None  #: Transient thermal_foster model.
    channel: list[ChannelData] | None  #: Diode forward voltage and forward current data.
    e_rr: list[SwitchEnergyData] | None  #: Reverse recovery energy data.
    linearized_diode: list[LinearizedModel] | None  #: Static data. Valid for a specific operating point.
    t_j_max: float  #: Diode maximum junction temperature. Units in °C (Mandatory key)
    soa: list[SOA] | None  #: Safe operating area of Diode

    def __init__(self, diode_args: dict):
        """
        Initialize a Diode object.

        :param diode_args: argument to be passed for initialization
        :type diode_args: dict

        :raises KeyError: Expected during the channel/e_rr instance initialization
        :raises ValueError: Expected during the channel/e_rr instance initialization
        """
        # Current behavior on empty 'foster' dictionary: thermal_foster object is still created but with empty
        # attributes.

        # ToDo: Is this the right behavior or should the 'thermal_foster' attribute be left empty instead?
        self.thermal_foster = FosterThermalModel(diode_args.get('thermal_foster'))
        if isvalid_dict(diode_args, 'Diode'):
            self.comment = diode_args.get('comment')
            self.manufacturer = diode_args.get('manufacturer')
            self.technology = diode_args.get('technology')
            self.t_j_max = diode_args.get('t_j_max')
            # This currently accepts dictionaries and lists of dictionaries.
            self.channel = []  # Default case: Empty list
            try:
                if isinstance(diode_args.get('channel'), list):
                    # Loop through list and check each dict for validity. Only create ChannelData objects from valid
                    # dicts. 'None' and empty dicts are ignored.
                    for dataset in diode_args.get('channel'):
                        if isvalid_dict(dataset, 'Diode_ChannelData'):
                            self.channel.append(ChannelData(dataset))
                            # If  occurs during this, raise KeyError and add index of list occurrence to the message
                elif isvalid_dict(diode_args.get('channel'), 'Diode_ChannelData'):
                    # Only create ChannelData objects from valid dicts
                    self.channel.append(ChannelData(diode_args.get('channel')))
            except KeyError as error:
                dict_list = diode_args.get('channel')
                if not error.args:
                    error.args = ('',)  # This syntax is necessary because error.args is a tuple
                error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                              f"Diode_ChannelData dictionaries: ",) + error.args
                raise
            except ValueError as error:
                dict_list = diode_args.get('channel')
                raise Exception(f"for index [{str(dict_list.index(dataset))}] in list of Diode_ChannelData dictionaries:" + str(error))

            self.e_rr = []  # Default case: Empty list
            if isinstance(diode_args.get('e_rr'), list):
                # Loop through list and check each dict for validity. Only create SwitchEnergyData objects from
                # valid dicts. 'None' and empty dicts are ignored.
                for dataset in diode_args.get('e_rr'):
                    try:
                        if isvalid_dict(dataset, 'SwitchEnergyData'):
                            self.e_rr.append(SwitchEnergyData(dataset))
                    # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                    except KeyError as error:
                        dict_list = diode_args.get('e_rr')
                        if not error.args:
                            error.args = ('',)  # This syntax is necessary because error.args is a tuple
                        error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                      f"Diode-SwitchEnergyData dictionaries for e_rr: ",) + error.args
                        raise
            elif isvalid_dict(diode_args.get('e_rr'), 'SwitchEnergyData'):
                # Only create SwitchEnergyData objects from valid dicts
                self.e_rr.append(SwitchEnergyData(diode_args.get('e_rr')))

            self.linearized_diode = []  # Default case: Empty list
            if isinstance(diode_args.get('linearized_diode'), list):
                # Loop through list and check each dict for validity. Only create LinearizedModel objects from
                # valid dicts. 'None' and empty dicts are ignored.
                for dataset in diode_args.get('linearized_diode'):
                    try:
                        if isvalid_dict(dataset, 'Diode_LinearizedModel'):
                            self.linearized_diode.append(LinearizedModel(dataset))
                    # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                    except KeyError as error:
                        dict_list = diode_args.get('linearized_diode')
                        if not error.args:
                            error.args = ('',)  # This syntax is necessary because error.args is a tuple
                        error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                      f"Diode-LinearizedModel dictionaries: ",) + error.args
                        raise
            elif isvalid_dict(diode_args.get('linearized_diode'), 'Diode_LinearizedModel'):
                # Only create LinearizedModel objects from valid dicts
                self.linearized_diode.append(LinearizedModel(diode_args.get('linearized_diode')))

            self.soa = []  # Default case: Empty list
            if isinstance(diode_args.get('soa'), list):
                # Loop through list and check each dict for validity. Only create SOA objects from
                # valid dicts. 'None' and empty dicts are ignored.
                for dataset in diode_args.get('soa'):
                    try:
                        if isvalid_dict(dataset, 'SOA'):
                            self.soa.append(SOA(dataset))
                    # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                    except KeyError as error:
                        dict_list = diode_args.get('soa')
                        if not error.args:
                            error.args = ('',)  # This syntax is necessary because error.args is a tuple
                        error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of soa "
                                      f"dictionaries: ",) + error.args
                        raise
            elif isvalid_dict(diode_args.get('soa'), 'SOA'):
                # Only create SOA objects from valid dicts
                self.soa.append(SOA(diode_args.get('soa')))

        else:  # Can be constructed from empty or 'None' argument dictionary since no attributes are mandatory.
            self.comment = None
            self.manufacturer = None
            self.technology = None
            self.channel = []
            self.e_rr = []
            self.linearized_diode = []

    def convert_to_dict(self) -> dict:
        """
        Convert a Diode object into dict datatype.

        :return: Diode object of dict type
        :rtype: dict
        """
        d = dict(vars(self))
        d['thermal_foster'] = self.thermal_foster.convert_to_dict()
        d['channel'] = [c.convert_to_dict() for c in self.channel]
        d['e_rr'] = [e.convert_to_dict() for e in self.e_rr]
        d['linearized_diode'] = [ld.convert_to_dict() for ld in self.linearized_diode]
        d['soa'] = [c.convert_to_dict() for c in self.soa]
        return d

    def find_next_gate_voltage(self, req_gate_vltgs: dict, export_type: str, check_specific_curves: list = None,
                               diode_loss_dataset_type: str = "graph_i_e"):
        """
        Find the diode gate voltage nearest to the specified values from the available gate voltages in curve datasets.

        The diode has only turn-off gate voltage which is the switch turn-on gate voltage

        :param req_gate_vltgs: the provided gate voltages to find the nearest neighbour to the corresponding key-value pairs
        :type req_gate_vltgs: dict
        :param export_type: either 'gecko' or 'plecs'
        :type export_type: str
        :param check_specific_curves: indexes of chosen energy curve to be skipped are provided here
        :type check_specific_curves: list(list, list)
        :param diode_loss_dataset_type: 'graph_i_e' or 'graph_r_e' dataset curve type to be specified
        :type diode_loss_dataset_type: str

        :return: v_d_channel, v_supply, v_d_off
        :rtype: int
        """
        if check_specific_curves is None:
            check_specific_curves = []
        check_keys(req_gate_vltgs, export_type, 'diode')
        # recheck channel characteristics curves at v_supply
        channel_v_gs = np.array([0 if chan.v_g is None else chan.v_g for chan in self.channel])
        req_gate_vltgs['v_channel_gs'] = min(channel_v_gs, key=lambda x: abs(x - req_gate_vltgs['v_channel_gs']))
        # gather data for err curves of required dataset_type and check if empty
        e_rrs = [e for i, e in enumerate(self.e_rr) if e.dataset_type == diode_loss_dataset_type and \
                 (not any(check_specific_curves) or i in check_specific_curves)]
        if not e_rrs:
            raise MissingDataError(1202)
        if export_type == 'plecs':
            # recheck turn off energy loss curves at v_supply
            e_rr_v_gs = np.array([0 if e.v_g is None else e.v_g for e in e_rrs])
            req_gate_vltgs['v_d_off'] = min(e_rr_v_gs, key=lambda x: abs(x - req_gate_vltgs['v_d_off']))

        if export_type == 'gecko':
            # recheck turn off loss energy characteristics curves at v_off, v_supply, r_g_off
            e_rr_v_gs = list()
            for e in e_rrs:
                if e.v_g is None:
                    e.v_g = 0
                e_rr_v_gs.append(e.v_g)
            v_d_off = min(e_rr_v_gs, key=lambda x: abs(x - req_gate_vltgs['v_d_off']))
            req_gate_vltgs['v_d_off'] = v_d_off
            e_rr_v_supply = [e.v_supply if e.v_g == v_d_off else None for e in e_rrs]
            v_supply = min(e_rr_v_supply, key=lambda x: abs(x - req_gate_vltgs['v_supply']))
            req_gate_vltgs['v_supply'] = v_supply

        logger.info("--Diode Recheck--")
        for key, value in req_gate_vltgs.items():
            logger.info(key + ': ', value)
        return req_gate_vltgs.values()

    def find_approx_wp(self, t_j: float, v_g: float, normalize_t_to_v: float = 10,
                       switch_energy_dataset_type: str = "graph_i_e") \
            -> tuple[ChannelData, SwitchEnergyData]:
        """
        Search for the smallest distance to stored object value and returns this working point.

        :param t_j: junction temperature
        :type t_j: float
        :param v_g: gate voltage
        :type v_g: float
        :param normalize_t_to_v: ratio between t_j and v_g. e.g. 10 means 10°C is same difference as 1V
        :type normalize_t_to_v: float
        :param switch_energy_dataset_type: 'graph_i_e' or 'graph_r_e'
        :type switch_energy_dataset_type: str
        :return: channel-object, e_rr-object
        :rtype: tuple[Transistor.ChannelData, Transistor.SwitchEnergyData]
        """
        # Normalize t_j to v_g for distance metric
        node = np.array([[t_j / normalize_t_to_v, v_g]])
        # Find closest channeldata
        channeldata_t_js = np.array([chan.t_j for chan in self.channel])
        channeldata_v_gs = np.array([0 if chan.v_g is None else chan.v_g for chan in self.channel])
        nodes = np.array([channeldata_t_js / normalize_t_to_v, channeldata_v_gs]).transpose()
        index_channeldata = distance.cdist(node, nodes).argmin()
        # Find closest e_rr
        e_rrs = [e for e in self.e_rr if e.dataset_type == switch_energy_dataset_type]
        if not e_rrs:
            # raise KeyError(f"There is no e_rr data with type {SwitchEnergyData_dataset_type} for this Diode object.")
            e_rrs = [None]
            index_e_rr = 0
        else:
            e_rr_t_js = np.array([e.t_j for e in e_rrs])
            e_rr_v_gs = np.array([0 if e.v_g is None else e.v_g for e in e_rrs])
            nodes = np.array([e_rr_t_js / normalize_t_to_v, e_rr_v_gs]).transpose()
            index_e_rr = distance.cdist(node, nodes).argmin()

            logger.info("run diode.find_approx_wp: closest working point for t_j = {0} °C and v_g = {1} V:".format(t_j, v_g))
            logger.info("channel: t_j = {0} °C and v_g = {1} V".format(self.channel[index_channeldata].t_j, self.channel[index_channeldata].v_g))
            logger.info("err:     t_j = {0} °C and v_g = {1} V".format(e_rrs[index_e_rr].t_j, e_rrs[index_e_rr].v_g))

        return self.channel[index_channeldata], e_rrs[index_e_rr]

    def plot_all_channel_data(self, buffer_req: bool = False):
        """
        Plot all diode channel characteristic curves.

        :param buffer_req: internally required for generating virtual datasheets
        :param buffer_req: bool

        :return: Respective plots are displayed
        """
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
                    # plt.title('$T_{{J}}$ = {0} °C'.format(key))
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
                    # plt.title('$V_{{g}}$ = {0} V'.format(key))
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
        Plot all diode reverse recovery energy i-e characteristic curves which are extracted from the manufacturer datasheet.

        :param buffer_req: internally required for generating virtual datasheets
        :type buffer_req: bool

        :return: Respective plots are displayed

        """
        e_rr_i_e_curve_count = 0
        for i_energy_data in np.array(range(0, len(self.e_rr))):
            if self.e_rr[i_energy_data].dataset_type == 'graph_i_e':
                e_rr_i_e_curve_count += 1
        # look for e_off losses
        if e_rr_i_e_curve_count > 0:
            plt.figure()
            for i_energy_data in np.array(range(0, len(self.e_rr))):
                # check if data is available as 'graph_i_e'
                if self.e_rr[i_energy_data].dataset_type == 'graph_i_e':
                    # add label plot
                    labelplot = "$e_{{rr}}$: $v_{{supply}}$ = {0} V, $T_{{J}}$ = {1} °C, $R_{{g}}$ = {2} Ohm".format(self.e_rr[i_energy_data].v_supply,
                                                                                                                     self.e_rr[i_energy_data].t_j,
                                                                                                                     self.e_rr[i_energy_data].r_g)
                    # check if gate voltage is given (GaN Transistor, SiC-MOSFET)
                    # if ture, add gate-voltage to label
                    if isinstance(self.e_rr[i_energy_data].v_g, (int, float)):
                        labelplot = labelplot + ", $v_{{g}}$ = {0} V".format(self.e_rr[i_energy_data].v_g)
                    # plot
                    plt.plot(self.e_rr[i_energy_data].graph_i_e[0], self.e_rr[i_energy_data].graph_i_e[1], label=labelplot)
                    plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            plt.legend(fontsize=5)
            plt.xlabel('Current in A')
            plt.ylabel('Loss energy in J')
            plt.grid()
            if buffer_req:
                return get_img_raw_data(plt)
            else:
                plt.show()
        else:
            logger.info("Diode reverse recovery energy i_e curves are not available for the chosen transistor")
            return None

    def plot_energy_data_r(self, buffer_req: bool = False):
        """
        Plot all diode energy r-e characteristic curves.

        :param buffer_req: internally required for generating virtual datasheets
        :type buffer_req: bool

        :return: Respective plots are displayed
        """
        e_rr_r_e_curve_count = 0
        for i_energy_data in np.array(range(0, len(self.e_rr))):
            if self.e_rr[i_energy_data].dataset_type == 'graph_r_e':
                e_rr_r_e_curve_count += 1
        # look for e_off losses
        if e_rr_r_e_curve_count > 0:
            plt.figure()
            for i_energy_data in np.array(range(0, len(self.e_rr))):
                # check if data is available as 'graph_i_e'
                if self.e_rr[i_energy_data].dataset_type == 'graph_r_e':
                    # add label plot
                    labelplot = "$e_{{rr}}$: $v_{{supply}}$ = {0} V, $T_{{J}}$ = {1} °C, $I_{{ch}}$ = {2} A".format(self.e_rr[i_energy_data].v_supply,
                                                                                                                    self.e_rr[i_energy_data].t_j,
                                                                                                                    self.e_rr[i_energy_data].i_x)
                    # check if gate voltage is given (GaN Transistor, SiC-MOSFET)
                    # if ture, add gate-voltage to label
                    if isinstance(self.e_rr[i_energy_data].v_g, (int, float)):
                        labelplot = labelplot + ", $v_{{g}}$ = {0} V".format(self.e_rr[i_energy_data].v_g)

                    # plot
                    plt.plot(self.e_rr[i_energy_data].graph_r_e[0], self.e_rr[i_energy_data].graph_r_e[1], label=labelplot)
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
            logger.info("Diode reverse recovery energy r_e curves are not available for the chosen transistor")
            return None

    def plot_soa(self, buffer_req: bool = False):
        """
        Plot and convert safe operating region characteristic plots in raw data format (Helper function).

        :param buffer_req: internally required for generating virtual datasheets

        :return: Respective plots are displayed
        """
        if not self.soa:
            return None
        fig = plt.figure()
        ax = fig.add_subplot(111)
        if isinstance(self.soa, list) and self.soa:
            for curve in self.soa:
                line1, = curve.get_plots(ax)
        plt.xlabel('$V_{ds}$ / $V_r$ [V]')
        plt.ylabel('$I_d$ / $I_r$ [A]')
        props = dict(fill=False, edgecolor='black', linewidth=1)
        if len(self.soa):
            plt.legend(fontsize=8)
            r_on_condition = '\n'.join(["conditions: ", "$T_{c} $ =" + str(self.soa[0].t_c) + " [°C]"])
            ax.text(0.65, 0.1, r_on_condition, transform=ax.transAxes, fontsize='small', bbox=props, ha='left', va='bottom')
        plt.grid()
        if buffer_req:
            return get_img_raw_data(plt)
        else:
            plt.show()

    def collect_data(self) -> dict:
        """
        Collect diode data in form of dictionary for generating virtual datasheet.

        :return: Diode data in form of dictionary
        :rtype: dict
        """
        diode_data = {}
        diode_data['plots'] = {'channel_plots': self.plot_all_channel_data(True), 'energy_plots': self.plot_energy_data(True),
                               'energy_plots_r': self.plot_energy_data_r(True), 'soa': self.plot_soa(True)}
        for attr in dir(self):
            if attr == 'thermal_foster':
                diode_data.update(getattr(self, attr).collect_data())
            elif not callable(getattr(self, attr)) and not attr.startswith("__") and not \
                    isinstance(getattr(self, attr), (list, np.ndarray, dict)) and (getattr(self, attr) is not None) and not getattr(self, attr) == "":
                diode_data[attr.capitalize()] = getattr(self, attr)
        return diode_data
