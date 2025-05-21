"""Contains important data classes like SOA, SwitchEnergyData, GateChargeCurve, ..."""
# Python standard libraries
from matplotlib import pyplot as plt
from datetime import datetime
import numpy as np
import numpy.typing as npt
import logging

# Local libraries
from transistordatabase.checker_functions import check_float
from transistordatabase.helper_functions import isvalid_dict, get_img_raw_data

logger = logging.getLogger(__name__)

class GateChargeCurve:
    """A class to hold gate charge characteristics of switch which is added as a optional attribute inside switch class."""

    v_supply: float  #: same as drain-to-source (v_ds)/ collector-emitter (v_ce) voltages
    t_j: float  #: junction temperature
    i_channel: float  #: channel current at which the graph is recorded
    i_g: float | None  #: gate to source/emitter current
    graph_q_v: npt.NDArray[np.float64]  #: a 2D numpy array to store gate charge dependant on gate to source voltage

    def __init__(self, args):
        """
        Initialize a GateChargeCurve object.

        :param args: arguments to be passed for initialization
        """
        # Validity of args is checked in the constructor of Switch class and thus does not need to be
        # checked again here.
        self.i_channel = args.get('i_channel')
        self.v_supply = args.get('v_supply')
        self.t_j = args.get('t_j')
        self.i_g = args.get('i_g')
        self.graph_q_v = args.get('graph_q_v')

    def convert_to_dict(self) -> dict:
        """
        Convert a GateChargeCurve object into dict datatype.

        :return: GateChargeCurve object of dict type
        :rtype: dict
        """
        d = dict(vars(self))
        for att_key in d:
            if isinstance(d[att_key], np.ndarray):
                d[att_key] = d[att_key].tolist()
        return d

    def get_plots(self, ax=None):
        """
        Plot the gate charge vs. gate source/ gate emitter voltage of switch type mosfet and igbt respectively.

        :param ax: figure axes to append the curves
        :type ax: figure axis

        :return: Respective plots are displayed if available else None is returned
        """
        if ax:
            label_plot = "$V_{{supply}}$ = {0} V".format(self.v_supply)
            return ax.plot(self.graph_q_v[0], self.graph_q_v[1], label=label_plot)
        else:
            plt.figure()  # needs rework because of this class being a list of transistor class members
            label_plot = " $V_{{supply}}$ = {0} V".format(self.v_supply)
            plt.plot(self.graph_q_v[0], self.graph_q_v[1], label=label_plot)
            plt.legend(fontsize=8)
            plt.xlabel('Gate Charge, $Q_{G} [nC]$')
            plt.ylabel('Gate source Voltage, $V_{gs} [V]$')
            plt.grid()
            plt.show()

class SOA:
    """Class to hold safe operating area characteristics of transistor type which is added as a optional attribute inside transistor class."""

    t_c: float | None  #: case temperature
    time_pulse: float | None  #: applied pulse duration
    graph_i_v: npt.NDArray[np.float64]  #: a 2D numpy array to store SOA characteristics curves

    def __init__(self, args: dict):
        """
        Initialize method for SOA object.

        :param args: arguments to be passed for initialization
        """
        # Validity of args is checked in the constructor of Transistor class and thus does not need to be
        # checked again here.
        self.time_pulse = args.get('time_pulse')
        self.t_c = args.get('t_c')
        self.graph_i_v = args.get('graph_i_v')

    def convert_to_dict(self) -> dict:
        """
        Convert SOA object into dict datatype.

        :return: SOA object of dict type
        :rtype: dict
        """
        d = dict(vars(self))
        for att_key in d:
            if isinstance(d[att_key], np.ndarray):
                d[att_key] = d[att_key].tolist()
        return d

    def get_plots(self, ax=None):
        """
        Plot drain current/reverse diode current vs drain-to-source voltage/diode applied reverse voltage of switch type mosfet/igbt.

        :param ax: figure axes to append the curves
        :type ax: figure axis

        :return: Respective plots are displayed if available else None is returned
        """
        if ax:
            label_plot = "$t_{{pulse}}$ = {0} s".format(self.time_pulse)
            return ax.loglog(self.graph_i_v[0], self.graph_i_v[1], label=label_plot)
        else:
            plt.figure()  # needs rework because of this class being a list of transistor class members
            label_plot = " $t_{{pulse}}$ = {0} V".format(self.time_pulse)
            plt.loglog(self.graph_i_v[0], self.graph_i_v[1], label=label_plot)
            plt.legend(fontsize=8)
            plt.xlabel('Drain-to-source ($V_{ds}$)/ reverse ($V_{ce}$) voltage')
            plt.ylabel('Drain $(I_d)$/ reverse $(I_c)$ current')
            plt.grid()
            plt.show()

class TemperatureDependResistance:
    """Store temperature dependant resistance curve."""

    i_channel: float  #: channel current at which the graph is recorded
    v_g: float  #: gate voltage
    dataset_type: str  #: curve datatype, can be either 't_r' or 't_factor'. 't_factor' is used to denote normalized gate curves
    graph_t_r: npt.NDArray[np.float64]  #: a 2D numpy array to store the temperature related channel on resistance
    r_channel_nominal: float | None  #: a mandatory field if the dataset_type is 't_factor'

    def __init__(self, args):
        """
        Initialize method for TemperatureDependResistance object.

        :param args: arguments to be passed for initialization
        """
        # Validity of args is checked in the constructor of Switch class and thus does not need to be
        # checked again here.
        self.i_channel = args.get('i_channel')
        self.v_g = args.get('v_g')
        self.dataset_type = args.get('dataset_type')
        self.r_channel_nominal = args.get('r_channel_nominal')
        self.graph_t_r = args.get('graph_t_r')

    def convert_to_dict(self) -> dict:
        """
        Convert a TemperatureDependResistance object into dict datatype.

        :return: TemperatureDependResistance object of dict type
        :rtype: dict
        """
        d = dict(vars(self))
        for att_key in d:
            if isinstance(d[att_key], np.ndarray):
                d[att_key] = d[att_key].tolist()
        return d

    def get_plots(self, ax=None):
        """
        Plot the on-resistance vs. Junction temperature.

        :param ax: figure axes to append the curves
        :type ax: figure axis

        :return: Respective plots are displayed if available else None is returned
        """
        if ax:
            label_plot = "$V_{{G}}$ = {0} V".format(self.v_g)
            return ax.plot(self.graph_t_r[0], self.graph_t_r[1], label=label_plot)
        else:
            plt.figure()  # needs rework because of this class being a list of transistor class members
            label_plot = " $V_{{G}}$ = {0} V".format(self.v_g)
            plt.plot(self.graph_t_r[0], self.graph_t_r[1], label=label_plot)
            plt.legend(fontsize=8)
            plt.xlabel('Junction Temperature [C°]')
            y_label = 'On Resistance [Ohm]' if self.dataset_type == 't_factor' else 'On Resistance'
            plt.ylabel(y_label)
            plt.grid()
            plt.show()

class EffectiveOutputCapacitance:
    """Record energy related or time related output capacitance of the switch."""

    c_o: float  #: Value of the fixed output capacitance. Units in F
    v_gs: float  #: Gate to source voltage of the switch. Units in V
    v_ds: float  #: Drain to source voltage of the switch ex: V_DS = (0-400V) i.e v_ds=400 (max value, min assumed a 0). Units in V

    def __init__(self, args):
        """
        Initialize the EffectiveOutputCapacitance object.

        :param args: arguments to be passed for initialization
        """
        # Validity of args is checked in the constructor of Diode/Switch class and thus does not need to be
        # checked again here.
        self.c_o = args.get('c_o')
        self.v_gs = args.get('v_gs')
        self.v_ds = args.get('v_ds')

    def convert_to_dict(self) -> dict:
        """
        Convert a EffectiveOutputCapacitance object into dict datatype.

        :return: EffectiveOutputCapacitance object of dict type
        :rtype: dict
        """
        d = dict(vars(self))
        for att_key in d:
            if isinstance(d[att_key], np.ndarray):
                d[att_key] = d[att_key].tolist()
        return d

    # ToDO: To be implemented for future boundary conditions in virtual datasheet
    def collect_data(self):
        """Get the effective output capacitance from the data."""
        c_oss_related = {}
        skipIds = []
        for attr in dir(self):
            if attr not in skipIds and not callable(getattr(self, attr)) and not attr.startswith("__") and not isinstance(getattr(self, attr), (list, dict)) \
                    and (getattr(self, attr) is not None):
                c_oss_related[attr.capitalize()] = getattr(self, attr)
        return c_oss_related

class SwitchEnergyData:
    """
    Data storage for switching losses (on/off/rr).

    - Contains switching energy data for either switch or diode. The type of Energy (E_on, E_off or E_rr) is already implicitly
    specified by how the respective objects of this class are used in a Diode- or Switch-object.
    - For each set (e.g. every curve in the datasheet) of switching energy data a separate object should be created.
    - This also includes the reference values in a datasheet given without a graph. (Those are considered as data sets with just a single data point.)
    - Data sets with more than one point are given as graph_i_e with an r_g parameter or as graph_r_e with an i_x parameter.
    - Unused parameters or datasets should be left empty.
    - Which of these cases (single point, E vs I dataset, E vs R dataset) is valid for the current object also needs to be specified by the
    dataset_type-property.
    """

    # Type of the dataset:
    # single: e_x, r_g, i_x are scalars. Given e.g. by a table in the datasheet.
    # graph_r_e: r_e is a 2-dim numpy array with two rows. i_x is a scalar. Given e.g. by an E vs R graph.
    # graph_i_e: i_e is a 2-dim numpy array with two rows. r_g is a scalar. Given e.g. by an E vs I graph.
    dataset_type: str  #: Single, graph_r_e, graph_i_e (Mandatory key)
    # Additional measurement information.
    comment: str | None  #: Comment for additional information e.g. on who made these measurements
    measurement_date: datetime | None  #: Specifies the date and time at which the measurement was done.
    measurement_testbench: str | None  #: Specifies the testbench used for the measurement.
    commutation_device: str | None  #: Second device used in half-bridge test condition
    # Test conditions. These must be given as scalars. Create additional objects for e.g. different temperatures.
    t_j: float  #: Junction temperature. Units in °C (Mandatory key)
    v_supply: float  #: Supply voltage. Units in V (Mandatory key)
    v_g: float  #: Gate voltage. Units in V (Mandatory key)
    v_g_off: float | None  #: Gate voltage for turn off. Units in V
    load_inductance: float | None  #: Load inductance. Units in H
    commutation_inductance: float | None  #: Commutation inductance. Units in H
    # Scalar dataset-parameters. Some of these can be 'None' depending on the dataset_type.
    e_x: float | None  #: Scalar dataset-parameter - switching energy. Units in J
    r_g: float | None  #: Scalar dataset-parameter - gate resistance. Units in Ohm
    i_x: float | None  #: Scalar dataset-parameter - current rating. Units in A
    # Dataset. Only one of these is allowed. The other should be 'None'.
    graph_i_e: npt.NDArray[np.float64] | None  #: Units for Row 1 = A; Row 2 = J
    graph_r_e: npt.NDArray[np.float64] | None  #: Units for Row 1 = Ohm; Row 2 = J

    # ToDo: Add MOSFET capacitance. Discuss with Philipp.
    # ToDo: Add additional class for linearized switching loss model with capacities. (See infineon application
    #  note.)
    # ToDo: Option 1: Look up table like it's currently implemented.
    # ToDo: Option 2: https://application-notes.digchip.com/070/70-41484.pdf
    # ToDO: Option 3: K_i, K_v, G_i. Add as empty class with pass.

    def __init__(self, args):
        # Validity of args is checked in the constructor of Diode/Switch class and thus does not need to be
        # checked again here.
        """
        Initialize the VoltageDependentCapacitance object.

        :param args: arguments to be passed for initialization

        .. todo:: Add warning if data is ignored because of dataset_type?
        """
        # ToDo: Add warning if data is ignored because of dataset_type?
        self.dataset_type = args.get('dataset_type')
        self.v_supply = args.get('v_supply')
        self.v_g = args.get('v_g')
        self.v_g_off = args.get('v_g_off')
        self.t_j = args.get('t_j')
        self.load_inductance = args.get('load_inductance')
        self.measurement_date = args.get('measurement_date')
        self.measurement_testbench = args.get('measurement_testbench')
        self.commutation_inductance = args.get('commutation_inductance')
        self.commutation_device = args.get('commutation_device')
        self.comment = args.get('comment')
        if self.dataset_type == 'single':
            self.e_x = args.get('e_x')
            self.r_g = args.get('r_g')
            self.i_x = args.get('i_x')
            self.t_j = args.get('t_j')
            self.graph_i_e = None
            self.graph_r_e = None
            self.graph_t_e = None
        elif self.dataset_type == 'graph_i_e':
            self.e_x = None
            self.r_g = args.get('r_g')
            self.i_x = None
            self.t_j = args.get('t_j')
            self.graph_r_e = None
            self.graph_i_e = args.get('graph_i_e')            
            self.graph_t_e = None
        elif self.dataset_type == 'graph_r_e':
            self.e_x = None
            self.r_g = None
            self.i_x = args.get('i_x')
            self.t_j = args.get('t_j')
            self.graph_r_e = args.get('graph_r_e')
            self.graph_i_e = None
            self.graph_t_e = None            
        elif self.dataset_type == 'graph_t_e':
            self.e_x = None
            self.r_g = args.get('r_g')
            self.i_x = args.get('i_x')
            self.t_j = None
            self.graph_r_e = None
            self.graph_i_e = None
            self.graph_t_e = args.get('graph_t_e')

    def convert_to_dict(self) -> dict:
        """
        Convert a SwitchEnergyData object into dict datatype.

        :return: SwitchEnergyData object of dict type
        :rtype: dict
        """
        d = dict(vars(self))
        for att_key in d:
            if isinstance(d[att_key], np.ndarray):
                d[att_key] = d[att_key].tolist()
        return d

    def plot_graph(self) -> None:
        """Plot switch / diode energy curve characteristics (either from graph_i_e or graph_r_e dataset)."""
        plt.figure()
        if self.dataset_type == 'graph_i_e':
            label = f"v_g = {self.v_g} V, v_supply = {self.v_supply} V, r_g = {self.r_g} Ohm, t_j = {self.t_j} °C"
            plt.plot(self.graph_i_e[0], self.graph_i_e[1], label=label)
            plt.xlabel('current in A')
        elif self.dataset_type == 'graph_r_e':
            label = f"v_g = {self.v_g} V, v_supply = {self.v_supply} V, i_x = {self.i_x} Ohm, t_j = {self.t_j} °C"
            plt.plot(self.graph_r_e[0], self.graph_r_e[1], label=label)
            plt.xlabel('r_g in Ohm')

        plt.legend()
        plt.grid()
        plt.ylabel('Energy in J')
        plt.show()

    def copy(self):
        """
        Copy the existing SwitchEnergyData object and create a new object of same type.

        Created to allow deep copy of object when using gecko exporter

        :return: SwitchEnergyData object
        :rtype: SwitchEnergyData
        """
        args = {
            'dataset_type': 'graph_i_e',
            'v_supply': self.v_supply,
            'graph_i_e': self.graph_i_e,
            'graph_r_e': self.graph_r_e,
            'r_g': self.r_g,
            'i_x': self.i_x,
            'e_x': self.e_x,
            't_j': self.t_j,
            'v_g': self.v_g,
        }
        # check dictionary
        isvalid_dict(args, 'SwitchEnergyData')
        return SwitchEnergyData(args)

class ChannelData:
    """
    V-I data for either switch or diode. Data is given for only one junction temperature t_j.

    For different temperatures: Create additional ChannelData-objects and store them as a list in the respective
    Diode- or Switch-object.
    This data can be used to linearize the transistor at a specific operating point
    """

    # # Test condition: Must be given as scalar. Create additional objects for different temperatures.
    t_j: float  #: Junction temperature of switch\diode. (Mandatory key)
    v_g: float  #: Switch: Mandatory key, Diode: optional (standard diode useless, for GaN 'diode' necessary
    # Dataset: Represented as a 2xm Matrix where row 1 is the voltage and row 2 the current.
    graph_v_i: npt.NDArray[np.float64]  #: Represented as a numpy 2D array where row 1 is the voltage and row 2 the current.
    # Units of Row 1 = V; Row 2 = A (Mandatory key)

    def __init__(self, args):
        """
        Initialize a ChannelData object.

        :param args: arguments to be passed for initialization
        """
        # Validity of args is checked in the constructor of Diode/Switch class and thus does not need to be
        # checked again here.
        self.t_j = args.get('t_j')
        self.graph_v_i = args.get('graph_v_i')
        self.v_g = args.get('v_g')

    def convert_to_dict(self) -> dict:
        """
        Convert a ChannelData object into dict datatype.

        :return: ChannelData object of dict type
        :rtype: dict
        """
        d = dict(vars(self))
        for att_key in d:
            if isinstance(d[att_key], np.ndarray):
                d[att_key] = d[att_key].tolist()
        return d

    def plot_graph(self) -> None:
        """Plot the channel curve v_i characteristics called by using any ChannelData object."""
        plt.figure()
        label = f"v_g = {self.v_g} V, t_j = {self.t_j} °C"
        plt.plot(self.graph_v_i[0], self.graph_v_i[1], label=label)
        plt.legend()
        plt.grid()
        plt.xlabel('Voltage in V')
        plt.ylabel('Current in A')
        plt.show()

class LinearizedModel:
    """
    Data for a linearized Switch/Diode depending on given operating point.

    Operating point specified by t_j, i_channel and (not for all diode types) v_g.
    """

    t_j: float  #: Junction temperature of diode\switch. Units in K  (Mandatory key)
    v_g: float | None  #: Gate voltage of switch or diode. Units in V (Mandatory for Switch, Optional for some Diode types)
    i_channel: float  #: Channel current of diode\switch. Units in A (Mandatory key)
    r_channel: float  #: Channel resistance of diode\switch. Units in Ohm (Mandatory key)
    v0_channel: float  #: Channel voltage of diode\switch. Unis in V (Mandatory key)

    def __init__(self, args):
        """
        Initialize a linearizedmodel object.

        :param args: arguments to passed for initialization
        """
        self.t_j = args.get('t_j')
        self.v_g = args.get('v_g')
        self.i_channel = args.get('i_channel')
        self.r_channel = args.get('r_channel')
        self.v0_channel = args.get('v0_channel')

    def convert_to_dict(self) -> dict:
        """
        Convert LinearizedModel object into dict datatype.

        :return: LinearizedModel object of dict type
        :rtype: dict
        """
        d = dict(vars(self))
        return d

class VoltageDependentCapacitance:
    """
    Graph_v_c data for transistor class. Data is given for only one junction temperature t_j.

    For different temperatures: Create additional VoltageDependentCapacitance-objects and store them as a list in the transistor-object.
    """

    # # Test condition: Must be given as scalar. Create additional objects for different temperatures.
    t_j: float  #: Junction temperature (Mandatory key)
    # Dataset: Represented as a 2xm Matrix where row 1 is the voltage and row 2 the capacitance.
    graph_v_c: npt.NDArray[np.float64]  #: Represented as a 2D numpy array where row 1 is the voltage and row 2 the capacitance.
    # Units of Row 1 = V; Row 2 = A  (Mandatory key)

    def __init__(self, args):
        """
        Initialize the VoltageDependentCapacitance object.

        :param args: arguments to be passed for initialization
        """
        # Validity of args is checked in the constructor of Diode/Switch class and thus does not need to be
        # checked again here.
        self.t_j = args.get('t_j')
        self.graph_v_c = args.get('graph_v_c')

    def convert_to_dict(self) -> dict:
        """
        Convert a VoltageDependentCapacitance object into dict datatype.

        :return: VoltageDependentCapacitance object of dict type
        :rtype: dict
        """
        d = dict(vars(self))
        for att_key in d:
            if isinstance(d[att_key], np.ndarray):
                d[att_key] = d[att_key].tolist()
        return d

    def get_plots(self, ax=None, label=None):
        """
        Plot the voltage dependant capacitance graph_v_c of the VoltageDependentCapacitance object.

        Also attaches the plot to figure axes for the purpose virtual datasheet if ax argument is specified

        :param ax: figure axes for making the graph_v_c plot in virtual datasheet
        :type ax: axis
        :param label: label of the plot for virtual datasheet plot
        :type label: str
        """
        if ax:
            label_plot = label + ", $T_{{J}}$ = {0} °C".format(self.t_j)
            return ax.semilogy(self.graph_v_c[0], self.graph_v_c[1], label=label_plot)
        else:
            plt.figure()  # needs rework because of this class being a list of transistor class members
            label_plot = "$T_{{J}}$ = {0}".format(self.t_j)
            plt.semilogy(self.graph_v_c[0], self.graph_v_c[1], label=label_plot)
            plt.legend(fontsize=8)
            plt.xlabel('Voltage in V')
            plt.ylabel('Capacitance in F')
            plt.grid()
            plt.show()

class FosterThermalModel:
    """
    Data to specify parameters of the Foster thermal_foster model.

    This model describes the transient
    temperature behavior as a thermal_foster RC-network. The necessary parameters can be estimated by curve-fitting
    transient temperature data supplied in graph_t_rthjc or by manually specifying the individual 2 out of 3 of the
    parameters R, C, and tau.

    .. todo::
        - Add function to estimate parameters from transient data.
        - Add function to automatically calculate missing parameters from given ones.
        - Do these need to be numpy array or should they be lists instead?
    """

    # Thermal resistances of RC-network (array).
    r_th_vector: list[float] | None  #: Thermal resistances of RC-network (array). Units in K/W (Optional key)
    # Sum of thermal_foster resistances of n-pole RC-network (scalar).
    r_th_total: float | None  #: Sum of thermal_foster resistances of n-pole RC-network (scalar). Units in K/W  (Optional key)
    # Thermal capacities of n-pole RC-network (array).
    c_th_vector: list[float] | None  #: Thermal capacities of n-pole RC-network (array). Units in J/K (Optional key)
    # Sum of thermal_foster capacities of n-pole low pass as (scalar).
    c_th_total: float | None  #: Sum of thermal_foster capacities of n-pole low pass as (scalar). Units in J/K  (Optional key)
    # Thermal time constants of n-pole RC-network (array).
    tau_vector: list[float] | None  #: Thermal time constants of n-pole RC-network (array). Units in s  (Optional key)
    # Sum of thermal_foster time constants of n-pole RC-network (scalar).
    tau_total: float | None  #: Sum of thermal_foster time constants of n-pole RC-network (scalar). Units in s (Optional key)
    # Transient data for extraction of the thermal_foster parameters specified above.
    # Represented as a 2xm Matrix where row 1 is the time and row 2 the temperature.
    graph_t_rthjc: npt.NDArray[np.float64] | None  #: Transient data for extraction of the thermal_foster parameters specified above.
    # Units of Row 1 in s; Row 2 in K/W  (Optional key)

    def __init__(self, args):
        """
        Initialize a FosterThermalModel object.

        :param args: argument to be passed for initialization
        :type args: dict

        .. note:: Can be constructed from empty or 'None' argument dictionary since no attributes are mandatory.
        """
        if isvalid_dict(args, 'FosterThermalModel'):
            self.r_th_total = args.get('r_th_total')
            self.r_th_vector = args.get('r_th_vector')
            self.c_th_total = args.get('c_th_total')
            self.c_th_vector = args.get('c_th_vector')
            self.tau_total = args.get('tau_total')
            self.tau_vector = args.get('tau_vector')
            self.graph_t_rthjc = args.get('graph_t_rthjc')
        else:  # Can be constructed from empty or 'None' argument dictionary since no attributes are mandatory.
            self.r_th_total = None
            self.r_th_vector = None
            self.c_th_total = None
            self.c_th_vector = None
            self.tau_total = None
            self.tau_vector = None
            self.graph_t_rthjc = None

    def convert_to_dict(self) -> dict:
        """
        Convert a FosterThermalModel object into dict datatype.

        :return: FosterThermalModel of dict type
        :rtype: dict
        """
        d = dict(vars(self))
        for att_key in d:
            if isinstance(d[att_key], np.ndarray):
                d[att_key] = d[att_key].tolist()
        return d

    def get_plots(self, buffer_req: bool = False):
        """
        Plot tau vs rthjc.

        :param buffer_req: Internally required for generating virtual datasheets
        :type buffer_req: bool

        :return: Respective plots are displayed if available else None is returned
        """
        if self.graph_t_rthjc is None:
            logger.info('No Foster impedance information exists!')
            return None
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.loglog(self.graph_t_rthjc[0], self.graph_t_rthjc[1])
        ax.set_xlabel('Time : $t$ [sec]')
        ax.set_ylabel('Thermal impedance: $Z_{th(j-c)}$ [K/W ]')
        ax.grid()
        # self.r_th_vector and self.tau_vector are optional.
        if self.r_th_vector is not None and self.tau_vector is not None:
            r_tau_vector = '\n'.join([
                '$R_{th}$ :' + " ".join(str("{:4.3f}".format(x)) for x in self.r_th_vector),
                'tau :' + " ".join(str("{:4.3f}".format(x)) for x in self.tau_vector)
            ])
            props = dict(fill=False, edgecolor='black', linewidth=2)
            ax.text(0.9, 0.2, r_tau_vector, fontsize='small', transform=ax.transAxes, bbox=props, ha='right')
        if buffer_req:
            return get_img_raw_data(plt)
        else:
            plt.show()

    def collect_data(self) -> dict:
        """
        Collect foster data in form of dictionary for generating virtual datasheet.

        :return: foster data in form of dictionary
        :rtype: dict
        """
        foster_data = {}
        foster_data['foster_plot'] = {'imp_plot': self.get_plots(True)}
        skipIds = ['graph_t_rthjc']
        for attr in dir(self):
            if attr not in skipIds and not callable(getattr(self, attr)) and not attr.startswith("__") and not isinstance(getattr(self, attr), (list, dict)) \
                    and (getattr(self, attr) is not None):
                foster_data[attr.capitalize()] = getattr(self, attr)
        return foster_data

class RawMeasurementData:
    """RAW measurement data. e.g. for voltage and current graphs from a double pulse test."""

    # Type of the dataset:
    # dpt_u_i: U/t I/t graph from double pulse measurements
    dataset_type: str  #: e.g. dpt_u_i (Mandatory key)
    dpt_on_vds: list[npt.NDArray[np.float64]] | None  #: measured Vds data at turn on event. Units in V and s
    dpt_on_id: list[npt.NDArray[np.float64]] | None  #: measured Id data at turn on event. Units in A and s
    dpt_off_vds: list[npt.NDArray[np.float64]] | None  #: measured Vds data at turn off event. Units in V and s
    dpt_off_id: list[npt.NDArray[np.float64]] | None  #: measured Vds data at turn off event. Units in A and s
    measurement_date: datetime | None  #: Specifies the measurements date and time
    measurement_testbench: str | None  #: Specifies the testbench used for the measurement.
    commutation_device: str | None  #: Second device used in half-bridge test condition
    comment: str | None  #: Comment for additional information e.g. on who made these measurements
    # Test conditions. These must be given as scalars. Create additional objects for e.g. different temperatures.
    t_j: float | None  #: Junction temperature. Units in °C
    v_supply: float | None  #: Supply voltage. Units in V
    v_g: float | None  #: Gate voltage. Units in V
    v_g_off: float | None  #: Gate voltage for turn off. Units in V
    r_g: list[npt.NDArray[np.float64]] | None  #: gate resistance. Units in Ohm
    r_g_off: list[npt.NDArray[np.float64]] | None  #: gate resistance. Units in Ohm
    load_inductance: float | None  #: Load inductance. Units in µH
    commutation_inductance: float | None  #: Commutation inductance. Units in µH

    e_off_meas = dict | None
    e_on_meas = dict | None

    def __init__(self, args):
        """
        Initialize a RawMeasurementData object.

        :param args: arguments to be passed for initialization
        """
        self.dataset_type = args.get('dataset_type')
        self.comment = args.get('dataset_type')
        if self.dataset_type == 'dpt_u_i' or self.dataset_type == 'dpt_u_i_r':
            self.dpt_on_vds = args.get('dpt_on_vds')
            self.dpt_on_id = args.get('dpt_on_id')
            self.dpt_off_vds = args.get('dpt_off_vds')
            self.dpt_off_id = args.get('dpt_off_id')
            self.v_supply = args.get('v_supply')
            self.v_g = args.get('v_g')
            self.v_g_off = args.get('v_g_off')
            self.t_j = args.get('t_j')
            self.load_inductance = args.get('load_inductance')
            self.commutation_inductance = args.get('commutation_inductance')
            self.commutation_device = args.get('commutation_device')
            self.r_g = args.get('r_g')
            self.r_g_off = args.get('r_g_off')
            self.measurement_date = args.get('measurement_date')
            self.measurement_testbench = args.get('measurement_testbench')
        else:
            self.dpt_on_vds = []
            self.dpt_on_id = []
            self.dpt_off_vds = []
            self.dpt_off_id = []

    def convert_to_dict(self) -> dict:
        """
        Convert RawMeasurementData object into dict datatype.

        :return: Switch object of dict type
        :rtype: dict
        """
        d = dict(vars(self))
        d['dpt_on_vds'] = [c.tolist() for c in self.dpt_on_vds]
        d['dpt_on_id'] = [c.tolist() for c in self.dpt_on_id]
        d['dpt_off_vds'] = [c.tolist() for c in self.dpt_off_vds]
        d['dpt_off_id'] = [c.tolist() for c in self.dpt_off_id]
        return d

    def dpt_calculate_energies(self, integration_interval: str, dataset_type: str, energies: str, mode: str):
        """
        Import double pulse measurements and calculates switching losses to each given working point.

        [1] options for the integration interval are based on following paper:
        Link: https://ieeexplore.ieee.org/document/8515553

        :param integration_interval: calculation standards for switching losses
        :type integration_interval: str
        :param dataset_type: defines what measurement set should should be calculated
        :type dataset_type: str
        :param energies: defines which switching energies should be calculated
        :type energies: str
        :param mode: Can be 'analyze'
        :type mode: str

        """
        if integration_interval == 'IEC 60747-9':
            off_vds_limit = 0.1
            off_is_limit = 0.02
            on_vds_limit = 0.02
            on_is_limit = 0.1
        elif integration_interval == 'Mitsubishi':
            off_vds_limit = 0.1
            off_is_limit = 0.1
            on_vds_limit = 0.1
            on_is_limit = 0.1
        elif integration_interval == 'Infineon':
            off_vds_limit = 0.1
            off_is_limit = 0.02
            on_vds_limit = 0.02
            on_is_limit = 0.1
        elif integration_interval == 'Wolfspeed':
            off_vds_limit = 0
            off_is_limit = -0.1
            on_vds_limit = -0.1
            on_is_limit = 0
        else:
            off_vds_limit = 0.1
            off_is_limit = 0.1
            on_vds_limit = 0.1
            on_is_limit = 0.1

        label_x_plot = 'Id / A'

        if dataset_type == 'graph_r_e':
            label_x_plot = 'Ron / Ohm'

        if energies == 'e_off' or energies == 'both':

            sample_point = 0
            measurement_points = len(self.dpt_off_id)
            e_off = []
            dv_dt_off = []
            di_dt_off = []
            time_correction = 0
            time_input = 0

            while measurement_points > sample_point:
                # Load Uds and Id pairs in increasing order
                vds_temp = self.dpt_off_vds[sample_point]
                id_temp = self.dpt_off_id[sample_point]

                sample_length = len(vds_temp)
                sample_interval = abs(vds_temp[1, 0] - vds_temp[2, 0])
                avg_interval = int(sample_length * 0.05)

                vds_avg_max = 0
                id_avg_max = 0

                ##############################
                # Find the max. Id in steady state
                ##############################
                i = 0
                while i <= avg_interval:
                    id_avg_max = id_avg_max + id_temp[i, 1] / avg_interval
                    i += 1

                ##############################
                # Find the max. Uds in steady state
                ##############################
                i = 0
                while i <= avg_interval:
                    vds_avg_max = vds_avg_max + vds_temp[(sample_length - 1 - i), 1] / avg_interval
                    i += 1

                ##############################
                # Find the starting point of the Eoff integration
                # i equals the lower integration limit
                ##############################
                i = 0
                e_off_temp = 0
                while vds_temp[i, 1] < (vds_avg_max * off_vds_limit):
                    i += 1

                lower_integration_limit = i

                # calculate di/dt, dv/dt
                di_dt_counter_low = 0
                while id_temp[di_dt_counter_low, 1] > (id_avg_max * 0.8):
                    di_dt_counter_low += 1

                di_dt_counter_high = di_dt_counter_low
                while id_temp[di_dt_counter_high, 1] > (id_avg_max * 0.2):
                    di_dt_counter_high += 1

                dv_dt_counter_low = 0
                while vds_temp[dv_dt_counter_low, 1] < (vds_avg_max * 0.2):
                    dv_dt_counter_low += 1

                dv_dt_counter_high = dv_dt_counter_low
                while vds_temp[dv_dt_counter_high, 1] < (vds_avg_max * 0.8):
                    dv_dt_counter_high += 1

                ##############################
                # Integrate the power with predefined integration limits
                ##############################
                while id_temp[i - time_correction, 1] >= (id_avg_max * off_is_limit):
                    e_off_temp = e_off_temp + (vds_temp[i, 1] * id_temp[i - time_correction, 1] * sample_interval)
                    i += 1

                upper_integration_limit = i

                if mode == 'analyze':
                    text1 = f"E_off = {(e_off_temp * 1000000).round(2)} µJ, time correction = {(time_correction * sample_interval * 1000000000).round(2)} ns"
                    text2 = f"Integration time = {((id_temp[upper_integration_limit, 0] - id_temp[lower_integration_limit, 0]) * 1000000000).round(2)} ns"
                    fig, ax1 = plt.subplots()
                    ax1.set_xlabel("t / ns")
                    ax1.set_ylabel("Id / A", color='r')
                    ax1.plot(((id_temp[:, 0] * 1000000000) + int(time_input)), id_temp[:, 1], color='r')
                    plt.axvline(id_temp[upper_integration_limit, 0] * 1000000000, color='green', linestyle='dotted',
                                linewidth=2)
                    plt.axvline(id_temp[lower_integration_limit, 0] * 1000000000, color='green', linestyle='dotted',
                                linewidth=2)
                    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
                    ax1.text(0.02, 1.05, text1, transform=ax1.transAxes, fontsize=12,
                             verticalalignment='bottom', horizontalalignment='left', bbox=props)
                    ax1.text(0.02, .5, text2, transform=ax1.transAxes, fontsize=12,
                             verticalalignment='center', horizontalalignment='left', bbox=props)
                    plt.grid(axis='both', color='grey', linestyle='--', linewidth=1)
                    ax2 = ax1.twinx()
                    ax2.set_ylabel('Uds / V', color='b')
                    ax2.plot(vds_temp[:, 0] * 1000000000, vds_temp[:, 1], color='b')
                    plt.show()
                    time_input = input('Please give a value for time correction in ns')
                    if check_float(time_input):
                        time_correction = int(float(time_input) / (sample_interval * 1000000000))
                        continue
                    else:
                        time_correction = 0
                        time_input = 0

                if dataset_type == 'graph_r_e':
                    e_off.append([self.r_g[sample_point], e_off_temp])
                else:
                    e_off.append([id_avg_max, e_off_temp])

                di_dt_off.append((id_temp[di_dt_counter_high, 1] - id_temp[di_dt_counter_low, 1]) / (
                    abs(id_temp[di_dt_counter_high, 0] - id_temp[di_dt_counter_low, 0]) * 1000000000))
                dv_dt_off.append((vds_temp[dv_dt_counter_high, 1] - vds_temp[lower_integration_limit, 1]) / (
                    abs(vds_temp[dv_dt_counter_high, 0] - vds_temp[lower_integration_limit, 0]) * 1000000000))

                sample_point += 1

            e_off_0 = [item[0] for item in e_off]
            e_off_1 = [item[1] for item in e_off]

            e_off_meas = {
                'dataset_type': dataset_type,
                't_j': self.t_j,
                'load_inductance': self.load_inductance,
                'commutation_inductance': self.commutation_inductance,
                'commutation_device': self.commutation_device,
                'comment': self.comment,
                'measurement_date': self.measurement_date,
                'measurement_testbench': self.measurement_testbench,
                'v_supply': self.v_supply,
                'v_g': self.v_g,
                'v_g_off': self.v_g_off,
                'r_g': self.r_g,
                'r_g_off': self.r_g_off,
                'graph_i_e': np.array([e_off_0, e_off_1]),
                'graph_r_e': np.array([e_off_0, e_off_1]),
                'e_x': float(e_off_1[0]),
                'i_x': id_avg_max,
                'di_dt': di_dt_off,
                'dv_dt': dv_dt_off}

            ##############################
            # Plot Eoff
            ##############################
            x = [sub[0] for sub in e_off]
            y = [sub[1] * 1000000 for sub in e_off]
            fig, ax1 = plt.subplots()
            color = 'tab:red'
            ax1.set_xlabel(label_x_plot)
            ax1.set_ylabel("Eoff / µJ", color=color)
            ax1.plot(x, y, marker='o', color=color)
            plt.grid('both')
            plt.show(block=True)

        if energies == 'e_on' or energies == 'both':

            sample_point = 0
            measurement_points = len(self.dpt_on_id)
            e_on = []
            dv_dt_on = []
            di_dt_on = []
            time_correction = 0
            time_input = 0

            while measurement_points > sample_point:
                # Load Uds and Id pairs in increasing order
                vds_temp = self.dpt_on_vds[sample_point]
                id_temp = self.dpt_on_id[sample_point]

                sample_length = len(vds_temp)
                sample_interval = abs(vds_temp[1, 0] - vds_temp[2, 0])
                avg_interval = int(sample_length * 0.05)
                vds_avg_max = 0
                id_avg_max = 0

                ##############################
                # Find the max. Id in steady state
                ##############################
                i = 0
                while i <= avg_interval:
                    id_avg_max = id_avg_max + (id_temp[(sample_length - 3 - i), 1] / avg_interval)
                    i += 1

                ##############################
                # Find the max. Uds in steady state
                ##############################
                i = 0
                while i <= avg_interval:
                    vds_avg_max = vds_avg_max + (vds_temp[i, 1] / avg_interval)
                    i += 1

                ##############################
                # Find the starting point of the Eon integration
                # i equals the lower integration limit
                ##############################
                i = 0
                e_on_temp = 0
                while id_temp[i, 1] < (id_avg_max * on_is_limit):
                    i += 1

                lower_integration_limit = i

                ##############################
                # Integrate the power with predefined integration limits
                ##############################
                while vds_temp[i - time_correction, 1] >= (vds_avg_max * on_vds_limit):
                    e_on_temp = e_on_temp + (vds_temp[i - time_correction, 1] * id_temp[i, 1] * sample_interval)
                    i += 1

                upper_integration_limit = i

                if mode == 'analyze':
                    text1 = f"E_on = {(e_on_temp * 1000000).round(2)} µJ, time correction = {(time_correction * sample_interval * 1000000000).round(2)} ns"
                    text2 = f"Integration time = {((id_temp[upper_integration_limit, 0] - id_temp[lower_integration_limit, 0]) * 1000000000).round(2)} ns"
                    fig, ax1 = plt.subplots()
                    ax1.set_xlabel("t / ns")
                    ax1.set_ylabel("Id / A", color='r')
                    ax1.plot(id_temp[:, 0] * 1000000000, id_temp[:, 1], color='r')
                    plt.axvline(id_temp[upper_integration_limit, 0] * 1000000000, color='green', linestyle='dotted',
                                linewidth=2)
                    plt.axvline(id_temp[lower_integration_limit, 0] * 1000000000, color='green', linestyle='dotted',
                                linewidth=2)
                    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
                    ax1.text(0.02, 1.05, text1, transform=ax1.transAxes, fontsize=12,
                             verticalalignment='bottom', horizontalalignment='left', bbox=props)
                    ax1.text(0.02, .5, text2, transform=ax1.transAxes, fontsize=12,
                             verticalalignment='center', horizontalalignment='left', bbox=props)
                    plt.grid(axis='both', color='grey', linestyle='--', linewidth=1)
                    ax2 = ax1.twinx()
                    ax2.set_ylabel('Uds / V', color='b')
                    ax2.plot(vds_temp[:, 0] * 1000000000 + int(time_input), vds_temp[:, 1], color='b')
                    plt.show()
                    time_input = input('Please give a value for time correction in ns')
                    if time_input.isnumeric():
                        time_correction = int(int(time_input) / (sample_interval * 1000000000))
                        continue
                    else:
                        time_correction = 0
                        time_input = 0

                if dataset_type == 'graph_r_e':
                    e_on.append([self.r_g[sample_point], e_on_temp])
                else:
                    e_on.append([id_avg_max, e_on_temp])

                dv_dt_on.append((vds_temp[dv_dt_counter_high, 1] - vds_temp[dv_dt_counter_low, 1]) / (
                    abs(vds_temp[dv_dt_counter_high, 0] - vds_temp[dv_dt_counter_low, 0]) * 1000000000))
                di_dt_on.append((id_temp[di_dt_counter_high, 1] - id_temp[di_dt_counter_low, 1]) / (
                    abs(vds_temp[di_dt_counter_high, 0] - vds_temp[di_dt_counter_low, 0]) * 1000000000))
                sample_point += 1

            e_on_0 = [item[0] for item in e_on]
            e_on_1 = [item[1] for item in e_on]

            e_on_meas = {
                'dataset_type': dataset_type,
                't_j': self.t_j,
                'load_inductance': self.load_inductance,
                'commutation_inductance': self.commutation_inductance,
                'commutation_device': self.commutation_device,
                'comment': self.comment,
                'measurement_date': self.measurement_date,
                'measurement_testbench': self.measurement_testbench,
                'v_supply': self.v_supply,
                'v_g': self.v_g,
                'v_g_off': self.v_g_off,
                'r_g': self.r_g,
                'r_g_off': self.r_g_off,
                'graph_i_e': np.array([e_on_0, e_on_1]),
                'graph_r_e': np.array([e_on_0, e_on_1]),
                'e_x': float(e_on_1[0]),
                'i_x': id_avg_max,
                'dv_dt': dv_dt_on,
                'di_dt': di_dt_on}

            ##############################
            # Plot Eon
            ##############################
            x = [sub[0] for sub in e_on]
            y = [sub[1] * 1000000 for sub in e_on]
            fig, ax1 = plt.subplots()
            color = 'tab:red'
            ax1.set_xlabel(label_x_plot)
            ax1.set_ylabel("Eon / µJ", color=color)
            ax1.plot(x, y, marker='o', color=color)
            plt.grid('both')
            plt.show(block=True)

        dpt_dict = {'e_off_meas': e_off_meas, 'e_on_meas': e_on_meas}
        return dpt_dict
