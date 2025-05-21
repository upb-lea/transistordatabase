"""Provide the transistor class."""
# Python standard libraries
from __future__ import annotations
import matplotlib.pyplot as plt
from scipy import integrate
from scipy.spatial import distance
from scipy.optimize import curve_fit
from datetime import datetime
import numpy as np
import numpy.typing as npt
import re
import os
import json
import scipy.io as sio
import collections
import copy
import base64
import io
import warnings
import logging

# Third party libraries
from jinja2 import Environment, FileSystemLoader
from bson.objectid import ObjectId
from bson import json_util

# Local libraries
from transistordatabase.constants import *
from transistordatabase.checker_functions import check_duplicates
from transistordatabase.helper_functions import *
from transistordatabase.data_classes import *
from transistordatabase.switch import Switch
from transistordatabase.diode import Diode
from transistordatabase.exceptions import MissingDataError
from transistordatabase.exporter import dict2matlab
import transistordatabase.colors as tdb_colors

logger = logging.getLogger(__name__)

class Transistor:
    """
    Transistor object which is the core class of transistordatabase module.

    Contains subclasses like Switch, Diode, FosterThermalModel etc, and other child classes
    using which all the features and functionalities of this module are based and developed.

    .. todo::
        - Groups data of all other classes for a single transistor. Methods are specified in such a way that only user-interaction with this class is necessary
        - Documentation on how to add or extract a transistor-object to/from the database can be found in
    """

    # ToDo: Add database id as attribute
    _id: int  #: ID of the object being created. (Automatic key) Only Used in MongoDB
    name: str  #: Name of the transistor. Choose as specific as possible. (Mandatory key)
    type: str  #: Specifies the type of module either e.g IGBT, MOSFET, SiC MOSFET etc. (Mandatory key)
    # User-specific data
    author: str  #: The author of the module specific object. Usually added when creating and adding a new datasheet module using template.py. (Mandatory key)
    comment: str | None  #: Any user specific comment created when adding a new datasheet module. (Optional key)
    # Date and template data. Should not be changed manually
    # ToDo: Add methods to automatically determine dates and template_version on construction or update.
    template_version: str  #: Specifies the template version using which a new datasheet module is created. (Mandatory/Automatic)
    template_date: datetime  #: Specifies the date and time at which the template in created. (Mandatory/Automatic)
    creation_date: datetime  #: Specifies the date and time of the new transistor module that is created using template. (Mandatory/Automatic)
    # Manufacturer- and part-specific data
    manufacturer: str  #: Provides information of the module manufacturer. (Mandatory key)
    datasheet_hyperlink: str | None  #: As the name specifies, provides the hyperlink of the datasheet that is being referred to.
    # Should be a valid link if specified(Optional)
    datasheet_date: datetime | None  #: pymongo cannot encode date => always save as datetime. (Optional key)
    datasheet_version: str | None  #: Specifies the version of the module manufacturer datasheet. (Optional key)
    housing_area: float  #: Housing area extracted from datasheet. Units in m^2. (Mandatory key)
    cooling_area: float  #: Housing area extracted from datasheet. Units in m^2. (Mandatory key)
    housing_type: str  #: e.g. TO-220, etc. Must be from a list of specific strings. (Mandatory key)
    # These are documented in their respective class definitions
    switch: Switch  #: Member instance for class type Switch (Mandatory key)
    diode: Diode  #: Member instance for class type Diode (Mandatory key)
    # Recommended gate resistors
    r_g_on_recommended: float | None  #: Recommended turn on gate resistance of switch (Optional key)
    r_g_off_recommended: float | None  #: Recommended turn off gate resistance of switch (Optional key)
    raw_measurement_data: list[RawMeasurementData] | None  #: Member instance for class type RawMeasurementData
    # Thermal data. See git for equivalent thermal_foster circuit diagram.
    r_th_cs: float | None  #: Module specific case to sink thermal resistance.  Units in K/W  (Mandatory key)
    r_th_switch_cs: float | None  #: Switch specific case to sink thermal resistance. Units in K/W  (Mandatory key)
    r_th_diode_cs: float | None  #: Diode specific case to sink thermal resistance. Units in K/W  (Mandatory key)
    # Absolute maximum ratings
    v_abs_max: float  #: Absolute maximum voltage rating. Units in V  (Mandatory key)
    i_abs_max: float  #: Absolute maximum current rating. Units in A  (Mandatory key)
    # Time and Energy related capacitance
    c_oss_er: EffectiveOutputCapacitance | None  #: Energy related effective output capacitance. Units in F (Optional key)
    c_oss_tr: EffectiveOutputCapacitance | None  #: Time related effective output capacitance. Units in F (Optional key)
    # Constant capacities
    c_oss_fix: float | None  #: Parasitic constant capacitance. Units in F  (Optional key)
    c_iss_fix: float | None  #: Parasitic constant capacitance. Units in F  (Optional key)
    c_rss_fix: float | None  #: Parasitic constant capacitance. Units in F  (Optional key)
    # Voltage dependent capacities
    c_oss: list[VoltageDependentCapacitance] | None  #: list of VoltageDependentCapacitance. (Optional key)
    c_iss: list[VoltageDependentCapacitance] | None  #: list of VoltageDependentCapacitance. (Optional key)
    c_rss: list[VoltageDependentCapacitance] | None  #: list of VoltageDependentCapacitance. (Optional key)
    # Energy stored in c_oss
    graph_v_ecoss: npt.NDArray[np.float64] | None  #: Member instance for storing voltage dependant capacitance graph in the form of 2D numpy array.
    # Units of Row 1 = V; Row 2 = J  (Optional key)
    # Rated operation region
    i_cont: float | None  #: Module specific continuous current. Units in  A e.g. Fuji = I_c, Semikron = I_c,nom (Mandatory key)
    t_c_max: float  #: Module specific maximum junction temperature. Units in °C (Optional key)
    r_g_int: float  #: Internal gate resistance. Units in Ohm (Mandatory key)
    # raw_measurement_plots = []

    def __init__(self, transistor_args: dict, switch_args: dict, diode_args: dict, possible_housing_types: list[str],
                 possible_module_manufacturers: list[str]) -> None:
        """
        Create a transistor element.

        Takes in the following dictionary arguments for creating and initializing the transistor object.
        isvalid_dict() method is applied on transistor_args object to validate the argument.
        Else TypeError exception is raised. Module manufacturer type and housing type data validations are performed for matching the given
        values to the pre-existed types stored in the form of 'housing.txt' and 'module_manufacturer.txt' files.

        :param transistor_args: transistor argument object
        :type transistor_args: dict
        :param switch_args: switch argument object
        :type switch_args: dict
        :param diode_args: diode argument object
        :type diode_args: dict
        :param possible_housing_types: list of housing types which are valid
        :type possible_housing_types: list[str]
        :param possible_module_manufacturers: List of module manufacturers which are valid
        :type possible_module_manufacturers: list[str]

        :raises TypeError: Raised if isvalid_dict() return false
        :raises ValueError: Raised if index based search for module_manufacturer or housing_type values fails
        """
        try:
            if isvalid_dict(transistor_args, 'Transistor'):
                if transistor_args.get('_id') is not None:
                    self._id = transistor_args.get('_id')
                else:
                    self._id = ObjectId()
                self.name = transistor_args.get('name')
                self.type = transistor_args.get('type')
                self.author = transistor_args.get('author')
                self.technology = transistor_args.get('technology')
                self.template_version = transistor_args.get('template_version')
                self.template_date = transistor_args.get('template_date')
                self.creation_date = transistor_args.get('creation_date')
                self.last_modified = transistor_args.get('last_modified')
                self.comment = transistor_args.get('comment')
                self.datasheet_hyperlink = transistor_args.get('datasheet_hyperlink')
                self.datasheet_date = transistor_args.get('datasheet_date')
                self.datasheet_version = transistor_args.get('datasheet_version')
                self.housing_area = transistor_args.get('housing_area')
                self.cooling_area = transistor_args.get('cooling_area')
                self.t_c_max = transistor_args.get('t_c_max')
                self.r_g_int = transistor_args.get('r_g_int')
                self.r_g_on_recommended = transistor_args.get('r_g_on_recommended')
                self.r_g_off_recommended = transistor_args.get('r_g_off_recommended')
                self.c_oss_fix = transistor_args.get('c_oss_fix')
                self.c_iss_fix = transistor_args.get('c_iss_fix')
                self.c_rss_fix = transistor_args.get('c_rss_fix')
            
                # Check housing type and module manufacturer for validity
                # TODO Could be own function?
                found = False
                given_housing_type = transistor_args.get('housing_type')
                if given_housing_type is not None:
                    for housing_type in possible_housing_types:
                        if housing_type.lstrip().lower() == given_housing_type.lstrip().lower():
                            self.housing_type = housing_type
                            found = True
                            break
                if not found:
                    raise ValueError(f"Housing type {given_housing_type} is not valid.")
                
                found = False
                given_module_manufacturer = transistor_args.get('manufacturer')
                if given_module_manufacturer is not None:
                    for module_manufacturer in possible_module_manufacturers:
                        if module_manufacturer.lstrip().lower() == given_module_manufacturer.lstrip().lower():
                            self.manufacturer = module_manufacturer
                            found = True
                            break
                if not found:
                    raise ValueError(f"Module manufacturer {given_module_manufacturer} is not valid.")

                self.r_th_cs = transistor_args.get('r_th_cs')
                self.r_th_switch_cs = transistor_args.get('r_th_switch_cs')
                self.r_th_diode_cs = transistor_args.get('r_th_diode_cs')
                self.v_abs_max = transistor_args.get('v_abs_max')
                self.i_abs_max = transistor_args.get('i_abs_max')
                self.i_cont = transistor_args.get('i_cont')
                self.c_oss = self.convert_voltage_dependent_capacitance(transistor_args.get('c_oss'), "c_oss")
                self.c_iss = self.convert_voltage_dependent_capacitance(transistor_args.get('c_iss'), "c_iss")
                self.c_rss = self.convert_voltage_dependent_capacitance(transistor_args.get('c_rss'), "c_rss")
                self.raw_measurement_data = self.convert_raw_measurement_data(transistor_args.get('raw_measurement_data'), "raw_measurement_data")
                self.graph_v_ecoss = transistor_args.get('graph_v_ecoss')

                self.c_oss_er = None
                if isvalid_dict(transistor_args.get('c_oss_er'), 'EffectiveOutputCapacitance'):
                    # Only create EffectiveOutputCapacitance objects from valid dicts
                    self.c_oss_er = EffectiveOutputCapacitance(transistor_args.get('c_oss_er'))

                self.c_oss_tr = None
                if isvalid_dict(transistor_args.get('c_oss_tr'), 'EffectiveOutputCapacitance'):
                    # Only create EffectiveOutputCapacitance objects from valid dicts
                    self.c_oss_tr = EffectiveOutputCapacitance(transistor_args.get('c_oss_tr'))
            else:
                # ToDo: Is this a value or a type error?
                # ToDo: Move these raises to isvalid_dict() by checking dict_type for 'None' or empty dicts?
                # ToDo: Use info in isvalid_dict() to print the list of mandatory values automatically
                raise TypeError("Dictionary 'transistor_args' is empty or 'None'. This is not allowed since following keys"
                                "are mandatory: 'name', 'type', 'author', 'manufacturer', 'housing_area', "
                                "'cooling_area', 'housing_type', 'v_abs_max', 'i_abs_max', 'i_cont'")
            self.diode = Diode(diode_args)
            self.switch = Switch(switch_args)

            # calculate r_th and c_th from impedance curves
            # This will be uncommented, due to re-assigning the parameters at every transistor reload or at transistor
            # generation.
            # self.calc_thermal_params(input_type='switch')
            # self.calc_thermal_params(input_type='diode')
            self.wp = self.WP()
            logger.info(f"Transistor {self.name} generated / loaded successfully!")
        except Exception as e:
            logger.error('Exception occurred: Selected datasheet or module could not be created or loaded\n' + str(e))
            raise

    def convert_raw_measurement_data(self, input: list | dict, name: str = None) -> list[RawMeasurementData]:
        """
        Convert input (list or dict) to list of raw_measurement_data.

        :param input: Input data
        :type input: list | dict
        :param name: Name of variable, only used for error message, optional
        :type name: str, optional
        :return: List of RawMeasurementData objects
        :rtype: list[RawMeasurementData]
        """
        output_list = []
        if isinstance(input, list):
            # Loop through list and check each dict for validity. Only create RawMeasurementData objects from
            # valid dicts. 'None' and empty dicts are ignored.
            for index, dataset in enumerate(input):
                try:
                    if isvalid_dict(dataset, 'RawMeasurementData'):
                        output_list.append(RawMeasurementData(dataset))
                # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                except KeyError as error:
                    if not error.args:
                        error.args = ('',)  # This syntax is necessary because error.args is a tuple
                    if name is None:
                        error.args = (f"KeyError occurred for index [{index}] in list {input} "
                                      f"dictionaries: ",) + error.args
                    else:
                        error.args = (f"KeyError occurred for index [{index}] in list of {name} "
                                      f"dictionaries: ",) + error.args
                    raise
        elif isvalid_dict(input, 'RawMeasurementData'):
            # Only create RawMeasurementData objects from valid dicts
            output_list.append(RawMeasurementData(input))

        return output_list

    def convert_voltage_dependent_capacitance(self, input: list | dict, name: str = None) -> list[VoltageDependentCapacitance]:
        """
        Convert input (list or dict) to list of raw_measurement_data.

        :param input: Input data
        :type input: list | dict
        :param name: Name of variable, only used for error message, optional
        :type name: str, optional
        :return: List of VoltageDependentCapacitance objects
        :rtype: list[VoltageDependentCapacitance]
        """
        output_list = []
        if isinstance(input, list):
            # Loop through list and check each dict for validity. Only create VoltageDependentCapacitance objects from
            # valid dicts. 'None' and empty dicts are ignored.
            for index, dataset in enumerate(input):
                try:
                    if isvalid_dict(dataset, 'VoltageDependentCapacitance'):
                        output_list.append(VoltageDependentCapacitance(dataset))
                # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                except KeyError as error:
                    if not error.args:
                        error.args = ('',)  # This syntax is necessary because error.args is a tuple
                    if name is None:
                        error.args = (f"KeyError occurred for index [{index}] in list {input} "
                                      f"dictionaries: ",) + error.args
                    else:
                        error.args = (f"KeyError occurred for index [{index}] in list of {name} "
                                      f"dictionaries: ",) + error.args
                    raise
        elif isvalid_dict(input, 'VoltageDependentCapacitance'):
            # Only create VoltageDependentCapacitance objects from valid dicts
            output_list.append(VoltageDependentCapacitance(input))

        return output_list

    def __eq__(self, other: Transistor) -> bool:
        """
        Check if the passed transistor object and the transistor object in scope are both same.

        This works by converting them to dict and checking the dict for equality (without the id).

        :param other: Expects transistor object
        :type other: Transistor
        :return: True or False
        :rtype: bool
        """
        # TODO Is this the fastest way to check for equality?
        if not isinstance(other, Transistor):
            # don't attempt to compare against unrelated types
            return NotImplemented
        
        my_dict = self.convert_to_dict()
        other_dict = other.convert_to_dict()

        if "_id" in my_dict:
            del my_dict["_id"]
        if "_id" in other_dict:
            del other_dict["_id"]

        return my_dict == other_dict

    def __repr__(self) -> str:
        """Transistor object string representation."""
        return f"{self.name}, {self.type}, {self.manufacturer}"

    def convert_to_dict(self) -> dict:
        """
        Convert the transistor object in scope to a dictionary datatype.

        :return: Transistor object in dict type
        :rtype: dict
        """
        # TODO Maybe move this function to the DatabaseManager class as a static function? Since the load from dict function is there too.
        if isinstance(self._id, ObjectId):
            # Set to none so there is no problem with serializing it.
            # Since the name is the new identifier, _id is not needed, but is created within the mongodb database
            self._id = None
        d = dict(vars(self))
        d.pop('wp', None)  # remove wp from converting. wp will not be stored to .json files
        d.pop('_id', None)
        d['diode'] = self.diode.convert_to_dict()
        d['switch'] = self.switch.convert_to_dict()
        d['c_oss_er'] = self.c_oss_er.convert_to_dict() if self.c_oss_er is not None else None
        d['c_oss_tr'] = self.c_oss_tr.convert_to_dict() if self.c_oss_tr is not None else None
        d['c_oss'] = [c.convert_to_dict() for c in self.c_oss]
        d['c_iss'] = [c.convert_to_dict() for c in self.c_iss]
        d['c_rss'] = [c.convert_to_dict() for c in self.c_rss]
        d['raw_measurement_data'] = [c.convert_to_dict() for c in self.raw_measurement_data]
        if isinstance(self.graph_v_ecoss, np.ndarray):
            d['graph_v_ecoss'] = self.graph_v_ecoss.tolist()
        return d

    def update_wp(self, t_j: float, v_g: float, i_channel: float, switch_or_diode: str = "both", normalize_t_to_v=10) -> None:
        """
        Fill the .wp-class, a temporary storage for self-written user-programs.

        Searches for the input values and fills the .wp-class with data next to this points.

        :param t_j: junction temperature
        :type t_j: float
        :param v_g: gate voltage
        :type v_g: float
        :param i_channel: channel current for linearization
        :type i_channel: float
        :param switch_or_diode: 'switch' or 'diode' or 'both'
        :type switch_or_diode: str
        :param normalize_t_to_v: ratio between t_j and v_g. e.g. 10 means 10°C is same difference as 1V
        :type normalize_t_to_v: float
        """
        if switch_or_diode in ["diode", "both"]:
            self.wp.diode_channel, self.wp.e_rr = self.diode.find_approx_wp(t_j, v_g, normalize_t_to_v)
            if self.wp.e_rr is None:
                logger.info("run diode.find_approx_wp: closest working point for t_j = {0} °C and {1} V:".format(t_j, v_g))
                logger.info("There is no err, may due to MOSFET, SiC-MOSFET or GaN device: Set err to [[0, 0], [0, 0]]")
                logger.info("Note: Values are set to t_j = 25°C, v_g = 15V, r_g = 1 Ohm")
                args = {"dataset_type": "graph_i_e",
                        "t_j": 25,
                        'v_g': 15,
                        'v_supply': 1,
                        'r_g': 1,
                        "graph_i_e": [np.array([[0, 0], [0, 0]]), np.array([[0, 0], [0, 0]])]}
                self.wp.e_rr = SwitchEnergyData(args)
            # ToDo: This could be handled more nicely by implementing another method for Diode and Channel class so the
            #  object can "linearize itself".
            self.wp.diode_v_channel, self.wp.diode_r_channel = \
                self.calc_lin_channel(self.wp.diode_channel.t_j, self.wp.diode_channel.v_g, i_channel, switch_or_diode="diode")

        if switch_or_diode in ["switch", "both"]:
            self.wp.switch_channel, self.wp.e_on, self.wp.e_off = self.switch.find_approx_wp(t_j, v_g, normalize_t_to_v)
            # ToDo: This could be handled more nicely by implementing another method for Diode and Channel class so the
            #  object can "linearize itself".
            self.wp.switch_v_channel, self.wp.switch_r_channel = \
                self.calc_lin_channel(self.wp.switch_channel.t_j, self.wp.switch_channel.v_g, i_channel, switch_or_diode="switch")

        self.wp.graph_v_coss = self.c_oss[0].graph_v_c

        # working point, fill e_oss
        if self.graph_v_ecoss is None:
            self.wp.graph_v_eoss = self.calc_v_eoss
        else:
            self.wp.graph_v_eoss = self.calc_v_eoss()

        # working point, calculate q_oss
        self.wp.graph_v_qoss = self.calc_v_qoss()

    def init_loss_matrices(self):
        """Experimental."""
        self.init_switch_channel_matrix()

    def init_switch_channel_matrix(self):
        """Experimental function."""
        # -----------------------------------------------------------
        # find out max values for v_g, v_channel, i_channel and t_j
        # -----------------------------------------------------------
        t_j_max = self.switch.channel[0].t_j
        t_j_min = self.switch.channel[0].t_j
        i_channel_max = 0
        v_channel_max = 0
        v_g_on_max = 0
        for channel_object in self.switch.channel:
            if channel_object.t_j > t_j_max:
                t_j_max = channel_object.t_j
            if t_j_min > channel_object.t_j:
                t_j_min = channel_object.t_j
            if channel_object.graph_v_i[0][-1] > v_channel_max:
                v_channel_max = channel_object.graph_v_i[0][-1]
            if channel_object.graph_v_i[1][-1] > i_channel_max:
                i_channel_max = channel_object.graph_v_i[1][-1]
            if channel_object.v_g > v_g_on_max:
                v_g_on_max = channel_object.v_g

        # -----------------------------------------------------------
        # Interpolate channel data
        # -----------------------------------------------------------
        v_g_linspace = np.linspace(0, v_g_on_max, 100)
        t_j_linspace = np.linspace(t_j_min, t_j_max, 100)
        i_channel_linspace = np.linspace(0, i_channel_max, 100)

        # -----------------------------------------------------------
        # setup mesh grid
        # -----------------------------------------------------------
        # m_i_channel, m_t_j = np.meshgrid(i_channel_linspace, t_j_linspace)

        # -----------------------------------------------------------
        # Interpolate channel data
        # -----------------------------------------------------------
        for channel_object in self.switch.channel:
            v_channel_interpolated = np.interp(i_channel_linspace, channel_object.graph_v_i[1],
                                               channel_object.graph_v_i[0])

            logger.info(f"{channel_object.t_j=}")
        logger.info(f"{t_j_max=}")
        logger.info(f"{t_j_min=}")
        logger.info(f"{v_channel_max=}")
        logger.info(f"{i_channel_max=}")

    def quickstart_wp(self) -> None:
        """
        Fill out the .wp-class by just one command 'quickstart_wp()'.

        Uses typical working points
         - channel linearization next to v_g = 15V, i_cont and t_j = t_j_abs_max - 25 degree
         - switching loss curves next to t_j = t_j_abs_max - 25 degree
        """
        # ToDo: may separate data for IGBT, MOSFET, SiC-MOSFET and GaN-Transistor
        self.update_wp(self.switch.t_j_max - 25, 15, self.i_cont)

    def calc_v_eoss(self) -> np.array:
        """
        Calculate e_oss stored in c_oss depend on the voltage. Uses transistor.c_oss[0].graph_v_coss.

        :return: e_oss numpy array
        :rtype: np.array
        """
        # energy_cumtrapz = np.zeros_like(self.c_oss[0].graph_v_c[1], dtype=np.float32)
        energy_cumtrapz = integrate.cumulative_trapezoid(self.c_oss[0].graph_v_c[0] * self.c_oss[0].graph_v_c[1],
                                                         self.c_oss[0].graph_v_c[0], initial=0)
        return np.array([self.c_oss[0].graph_v_c[0], energy_cumtrapz])

    def calc_v_qoss(self) -> np.array:
        """
        Calculate q_oss stored in c_oss depend on the voltage. Uses transistor.c_oss[0].graph_v_coss.

        :return: q_oss numpy array
        :rtype: np.array
        """
        charge_cumtrapz = integrate.cumulative_trapezoid(self.c_oss[0].graph_v_c[1], self.c_oss[0].graph_v_c[0],
                                                         initial=0)

        return np.array([self.c_oss[0].graph_v_c[0], charge_cumtrapz])

    def plot_v_eoss(self, buffer_req: bool = False):
        """
        Plot v_eoss with method calc_v_eoss.

        :param buffer_req: Internally required for generating virtual datasheets
        :type buffer_req: bool

        :return: Respective plots are displayed
        """
        v_eoss = self.calc_v_eoss()
        plt.figure()
        plt.plot(v_eoss[0], v_eoss[1])
        plt.xlabel('Voltage in V')
        plt.ylabel('Energy in J')
        plt.grid()
        if buffer_req:
            return get_img_raw_data(plt)
        else:
            plt.show()

    def plot_v_qoss(self, buffer_req: bool = False):
        """
        Plot v_qoss with method calc_v_qoss.

        :param buffer_req: Internally required for generating virtual datasheets
        :type buffer_req: bool

        :return: Respective plots are displayed
        """
        v_qoss = self.calc_v_qoss()
        plt.figure()
        plt.plot(v_qoss[0], v_qoss[1])
        plt.xlabel('Voltage in V')
        plt.ylabel('Charge in C')
        plt.grid()
        plt.show()
        if buffer_req:
            return get_img_raw_data(plt)
        else:
            plt.show()

    def plot_v_coss(self, buffer_req: bool = False):
        """
        Plot the output capacitance C_oss.

        :param buffer_req: Internally required for generating virtual datasheets
        :type buffer_req: bool

        :return: Respective plots are displayed
        """
        plt.figure()
        plt.semilogy(self.c_oss[0].graph_v_c[0], self.c_oss[0].graph_v_c[1])
        plt.xlabel('Voltage in V')
        plt.ylabel('Capacitance in F')
        plt.grid()
        plt.show()
        if buffer_req:
            return get_img_raw_data(plt)
        else:
            plt.show()

    def plot_half_bridge_equivalent_coss(self, v_dc: float, figure_size_mm: tuple | None = None, buffer_req: bool = False):
        """
        Plot the half-bridge equivalent output capacitance C_oss.

        :param v_dc: DC voltage for the half-bridge
        :type v_dc: float
        :param buffer_req: Internally required for generating virtual datasheets
        :type buffer_req: bool
        :param figure_size_mm: figure size in mm as a tuple (x mm, y mm)
        :type figure_size_mm: tuple

        :return: Respective plots are displayed
        """
        v_original = self.c_oss[0].graph_v_c[0]
        c_original = self.c_oss[0].graph_v_c[1]

        # clip datasheet voltage at the given max. v_dc for a virtual low-side transistor
        v_dc_low_side = v_original[v_original < v_dc]
        c_dc_low_side = c_original[v_original < v_dc]

        # interpolate datasets, generate high-side coss
        v_dc_low_side_interp = np.linspace(0, v_dc)
        c_dc_low_side_interp = np.interp(v_dc_low_side_interp, v_dc_low_side, c_dc_low_side)
        c_dc_high_side_interp = c_dc_low_side_interp[::-1]

        # add both capacitances
        c_dc_common_interp = c_dc_low_side_interp + c_dc_high_side_interp

        plt.figure(figsize=[x/25.4 for x in figure_size_mm] if figure_size_mm is not None else None)
        plt.semilogy(v_dc_low_side_interp, c_dc_low_side_interp, label=r'$C_\mathrm{oss,LS}$', color=tdb_colors.gnome_colors["red"])
        plt.semilogy(v_dc_low_side_interp, c_dc_high_side_interp, label=r'$C_\mathrm{oss,HS}$', color=tdb_colors.gnome_colors["green"])
        plt.semilogy(v_dc_low_side_interp, c_dc_common_interp, label=r'$C_\mathrm{oss,HS+LS}$', color=tdb_colors.gnome_colors["blue"])

        plt.xlabel('Voltage in V')
        plt.ylabel('Capacitance in F')
        plt.title(f"{self.name}")
        plt.legend()
        plt.grid()
        plt.tight_layout()
        plt.show()
        if buffer_req:
            return get_img_raw_data(plt)
        else:
            plt.show()

    def plot_half_bridge_equivalent_eoss(self, v_dc: float, figure_size_mm: tuple | None = None, buffer_req: bool = False, yunits: str = 'J'):
        """
        Plot the half-bridge equivalent output capacitance C_oss.

        :param v_dc: DC voltage for the half-bridge
        :type v_dc: float
        :param buffer_req: Internally required for generating virtual datasheets
        :type buffer_req: bool
        :param figure_size_mm: figure size in mm as a tuple (x mm, y mm)
        :type figure_size_mm: tuple
        :param yunits: Unit for the y-axis, e.g. "J"
        :type yunits: str

        :return: Respective plots are displayed
        """
        v_original = self.c_oss[0].graph_v_c[0]
        c_original = self.c_oss[0].graph_v_c[1]

        # clip datasheet voltage at the given max. v_dc for a virtual low-side transistor
        v_dc_low_side = v_original[v_original < v_dc]
        c_dc_low_side = c_original[v_original < v_dc]

        # interpolate datasets, generate high-side coss
        v_dc_low_side_interp = np.linspace(0, v_dc)
        c_dc_low_side_interp = np.interp(v_dc_low_side_interp, v_dc_low_side, c_dc_low_side)
        c_dc_high_side_interp = c_dc_low_side_interp[::-1]

        # add both capacitances
        c_dc_common_interp = c_dc_low_side_interp + c_dc_high_side_interp

        energy_cumtrapz_low_side = integrate.cumulative_trapezoid(v_dc_low_side_interp * c_dc_low_side_interp, v_dc_low_side_interp, initial=0)
        energy_cumtrapz_high_side = energy_cumtrapz_low_side[::-1]
        energy_cumtrapz_common = energy_cumtrapz_low_side + energy_cumtrapz_high_side

        if yunits.lower() == 'mj':
            energy_cumtrapz_low_side = energy_cumtrapz_low_side * 1e3
            energy_cumtrapz_high_side = energy_cumtrapz_high_side * 1e3
            energy_cumtrapz_common = energy_cumtrapz_common * 1e3
        if yunits.lower() == 'uj':
            energy_cumtrapz_low_side = energy_cumtrapz_low_side * 1e6
            energy_cumtrapz_high_side = energy_cumtrapz_high_side * 1e6
            energy_cumtrapz_common = energy_cumtrapz_common * 1e6
            yunits = 'µJ'
        if yunits.lower() == 'nj':
            energy_cumtrapz_low_side = energy_cumtrapz_low_side * 1e9
            energy_cumtrapz_high_side = energy_cumtrapz_high_side * 1e9
            energy_cumtrapz_common = energy_cumtrapz_common * 1e9

        plt.figure(figsize=[x/25.4 for x in figure_size_mm] if figure_size_mm is not None else None)
        plt.plot(v_dc_low_side_interp, energy_cumtrapz_low_side, label=r'$E_\mathrm{oss,LS}$', color=tdb_colors.gnome_colors["red"])
        plt.plot(v_dc_low_side_interp, energy_cumtrapz_high_side, label=r'$E_\mathrm{oss,HS}$', color=tdb_colors.gnome_colors["green"])
        plt.plot(v_dc_low_side_interp, energy_cumtrapz_common, label=r'$E_\mathrm{oss,HS+LS}$', color=tdb_colors.gnome_colors["blue"])

        plt.xlabel('Voltage in V')
        plt.ylabel(f'Energy in {yunits}')
        plt.title(f"{self.name}")
        plt.legend()
        plt.grid()
        plt.tight_layout()
        plt.show()
        if buffer_req:
            return get_img_raw_data(plt)
        else:
            plt.show()

    @staticmethod
    def calc_energy_object_voltage_correction(energy_object: SwitchEnergyData, v_op: float):
        """
        Calculate the switch loss energy for a different output voltage.

        :param energy_object: Energy object (e.g. turn-on)
        :type energy_object: SwitchEnergyData
        :param v_op: Operating voltage in V
        :type v_op: float
        """
        e_voltage = copy.deepcopy(energy_object)
        e_voltage.graph_i_e[1] = e_voltage.graph_i_e[1] * v_op / energy_object.v_supply
        e_voltage.v_supply = v_op

        return e_voltage

    def calc_real_on_off_loss(self, e_on: SwitchEnergyData, e_off: SwitchEnergyData, v_op: float):
        """
        Correct the turn-on and turn-off energy by the energy stored in C_oss.

        :param e_on: e_on object
        :type e_on: SwitchEnergyData
        :param e_off: e_off object
        :type e_off: SwitchEnergyData
        :param v_op: voltage of interest
        :type v_op: float
        """
        # read e_on and e_off, perform voltage corrections
        e_on_corrected = copy.deepcopy(e_on)
        e_on_corrected.graph_i_e[1] = e_on_corrected.graph_i_e[1] * v_op / e_on.v_supply
        e_on_corrected.v_supply = v_op
        e_off_corrected = copy.deepcopy(e_off)
        e_off_corrected.graph_i_e[1] = e_off_corrected.graph_i_e[1] * v_op / e_off.v_supply
        e_off_corrected.v_supply = v_op

        eoss_v, eoss_e = self.calc_v_eoss()
        e_oss_v_op = np.interp(v_op, eoss_v, eoss_e)
        logger.info(f"{e_oss_v_op=}")

        e_on_corrected.graph_i_e[1] = e_on_corrected.graph_i_e[1] + e_oss_v_op
        e_off_corrected.graph_i_e[1] = e_off_corrected.graph_i_e[1] - e_oss_v_op

        return e_on_corrected, e_off_corrected

    @staticmethod
    def plot_energy_objects(*energy_objects: SwitchEnergyData, energy_scale: str = "µJ",
                            figure_size: tuple | None = None, figure_directory: str | None = None,
                            additional_label: list | None = None, line_style: list = None, color: list = None):
        """
        Plot multiple energy objects into one plot.

        :param energy_objects: SwitchEnergyData
        :type energy_objects: SwitchEnergyData
        :param energy_scale: Choose y-label, e.g. 'µJ' or 'mJ' or 'nJ'
        :type energy_scale: str
        :param figure_size: figures size in mm (width, height)
        :type figure_size: tuple
        :param figure_directory: Directory to store the figure
        :type figure_directory: str
        :param additional_label: addition to the existing label
        :type additional_label: Optional[list]
        :param line_style: line style, see also matplotlib documentation
        :type line_style: list[str]
        :param color: color
        :type color: list[str]
        """
        plt.figure(figsize=[x / 25.4 for x in figure_size] if figure_size is not None else None, dpi=80)
        for count, eo in enumerate(energy_objects):
            if energy_scale == "mJ":
                energy = eo.graph_i_e[1] * 1e3
            elif energy_scale == "µJ":
                energy = eo.graph_i_e[1] * 1e6
            elif energy_scale == "nJ":
                energy = eo.graph_i_e[1] * 1e9

            plt.plot(eo.graph_i_e[0], energy,
                     label=f"V_g = {eo.v_g} V, V_supply = {eo.v_supply} V, T_j = {eo.t_j} °C"
                           f"{additional_label[count] if additional_label[count] is not None else ''}",
                     linestyle=line_style[count],
                     color=color[count],
                     )

        plt.grid()
        plt.legend()
        plt.xlabel("Current in A")
        plt.ylabel(f"Energy in {energy_scale}")
        plt.tight_layout()
        if figure_directory is not None:
            plt.savefig(figure_directory, bbox_inches="tight")
        plt.show()

    def get_object_v_i(self, switch_or_diode: str, t_j: float, v_g: float) -> list:
        """
        Get a channel curve including boundary conditions.

        :param switch_or_diode: 'switch' or 'diode'
        :type switch_or_diode: float
        :param t_j: junction temperature
        :type t_j: float
        :param v_g: gate voltage
        :type v_g: float

        :raises ValueError: When no data is available
        :return: v_i-object (channel curve including boundary conditions)
        :rtype: list
        """
        dataset = None
        if switch_or_diode == 'switch':
            candidate_datasets = [channel for channel in self.switch.channel if
                                  (channel.t_j == t_j and channel.v_g == v_g)]
            if len(candidate_datasets) == 0:
                available_datasets = [(channel.t_j, channel.v_g) for channel in self.switch.channel]
                logger.info("Available operating points: (t_j, v_g)")
                logger.info(available_datasets)
                raise ValueError("No data available for linearization at the given operating point. "
                                 "A list of available operating points is printed above.")
            elif len(candidate_datasets) > 1:
                logger.info("Multiple datasets were found that are consistent with the chosen "
                            "operating point. The first of these sets is automatically chosen because selection of a "
                            "different dataset is not yet implemented.")
            dataset = candidate_datasets[0]

        elif switch_or_diode == 'diode':
            if self.type in ['SiC-MOSFET', 'GaN-Transistor']:
                candidate_datasets = [channel for channel in self.diode.channel if
                                      (channel.t_j == t_j and channel.v_g == v_g)]
                if len(candidate_datasets) == 0:
                    available_datasets = [(channel.t_j, channel.v_g) for channel in self.diode.channel]
                    logger.info("Available operating points: (t_j, v_g)")
                    logger.info(available_datasets)
                    raise ValueError("No data available for linearization at the given operating point. "
                                     "A list of available operating points is printed above.")
                elif len(candidate_datasets) > 1:
                    logger.info("Multiple datasets were found that are consistent with the chosen "
                                "operating point. The first of these sets is automatically chosen because selection of a "
                                "different dataset is not yet implemented.")
                dataset = candidate_datasets[0]
            else:
                candidate_datasets = [channel for channel in self.diode.channel
                                      if channel.t_j == t_j]
                if len(candidate_datasets) == 0:
                    available_datasets = [channel.t_j for channel in self.diode.channel]
                    logger.info("Available operating points: (t_j)")
                    logger.info(available_datasets)
                    raise ValueError("No data available for linearization at the given operating point. "
                                     "A list of available operating points is printed above.")
                elif len(candidate_datasets) > 1:
                    logger.info("Multiple datasets were found that are consistent with the chosen "
                                "operating point. The first of these sets is automatically chosen because selection of a "
                                "different dataset is not yet implemented.")
                dataset = candidate_datasets[0]

        return dataset

    def get_object_i_e(self, e_on_off_rr: str, t_j: float, v_g: float, v_supply: float, r_g: float) -> list:
        """
        Get the loss graphs out of the transistor class.

        :param e_on_off_rr: can be the following: 'e_on', 'e_off' or 'e_rr'
        :type e_on_off_rr: str
        :param t_j: junction temperature
        :type t_j: float
        :param v_g: gate voltage at turn-on / turn-off
        :type v_g: float
        :param v_supply: dc link voltage
        :type v_supply: float
        :param r_g: gate resistor
        :type r_g: float

        :return: e_on.graph_i_e or e_off.graph_i_e or e_rr.graph_i_e
        :rtype: list
        """
        dataset = None
        if e_on_off_rr == 'e_on':
            candidate_datasets = [e_on for e_on in self.switch.e_on if (
                e_on.t_j == t_j and e_on.v_g == v_g and e_on.v_supply == v_supply and e_on.r_g == r_g)]
            if len(candidate_datasets) == 0:
                available_datasets = [(e_on.t_j, e_on.v_g, e_on.v_supply, e_on.r_g) for e_on in self.switch.e_on]
                logger.info("Available operating points: (t_j, v_g, v_supply, r_g)")
                logger.info(available_datasets)
                raise ValueError("No data available for get_graph_i_e at the given operating point. "
                                 "A list of available operating points is printed above.")
            elif len(candidate_datasets) > 1:
                logger.info("multiple datasets were found that are consistent with the chosen "
                            "operating point. The first of these sets is automatically chosen because selection of a "
                            "different dataset is not yet implemented.")
            dataset = candidate_datasets[0]

        if e_on_off_rr == 'e_off':
            candidate_datasets = [e_off for e_off in self.switch.e_off if (
                e_off.t_j == t_j and e_off.v_g == v_g and e_off.v_supply == v_supply and e_off.r_g == r_g)]
            if len(candidate_datasets) == 0:
                available_datasets = [(e_off.t_j, e_off.v_g, e_off.v_supply, e_off.r_g) for e_off in self.switch.e_off]
                logger.info("Available operating points: (t_j, v_g, v_supply, r_g)")
                logger.info(available_datasets)
                raise ValueError("No data available for get_graph_i_e at the given operating point. "
                                 "A list of available operating points is printed above.")
            elif len(candidate_datasets) > 1:
                logger.info("multiple datasets were found that are consistent with the chosen "
                            "operating point. The first of these sets is automatically chosen because selection of a "
                            "different dataset is not yet implemented.")
            dataset = candidate_datasets[0]

        if e_on_off_rr == 'e_rr':
            candidate_datasets = [e_rr for e_rr in self.diode.e_rr if (
                e_rr.t_j == t_j and e_rr.v_g == v_g and e_rr.v_supply == v_supply and e_rr.r_g == r_g)]
            if len(candidate_datasets) == 0:
                available_datasets = [(e_rr.t_j, e_rr.v_g, e_rr.v_supply, e_rr.r_g) for e_rr in self.diode.e_rr]
                logger.info("Available operating points: (t_j, v_g, v_supply, r_g)")
                logger.info(available_datasets)
                raise ValueError("No data available for get_graph_i_e at the given operating point. "
                                 "A list of available operating points is printed above.")
            elif len(candidate_datasets) > 1:
                logger.info("multiple datasets were found that are consistent with the chosen "
                            "operating point. The first of these sets is automatically chosen because selection of a "
                            "different dataset is not yet implemented.")
            dataset = candidate_datasets[0]
        return dataset

    def get_object_i_e_simplified(self, e_on_off_rr: str, t_j: float):
        """
        Get the loss graphs out of the transistor class, simplified version.

        :param e_on_off_rr: can be the following: 'e_on', 'e_off' or 'e_rr'
        :type e_on_off_rr: str
        :param t_j: junction temperature
        :type t_j: float

        :raises ValueError: Raised when no graph_i_e information is available at the given operating point
        :return: e_on.graph_i_e or e_off.graph_i_e or e_rr.graph_i_e, e_on.graph_r_e or e_off.graph_r_e or e_rr.graph_r_e
        :rtype: list, list or None
        """
        # Note: this is necessary due to e_on/e_off and e_rr are stored to switch and diode
        if e_on_off_rr == 'e_on' or e_on_off_rr == 'e_off':
            # s_d stands for 'switch or diode'
            s_d = 'switch'
        else:
            s_d = 'diode'

        # use eval function to choose variable e_on/e_off/e_rr
        # compile is necessary due to using eval combined with if-statement
        # https://realpython.com/python-eval-function/
        code = compile(
            f"[{e_on_off_rr} for {e_on_off_rr} in self.{s_d}.{e_on_off_rr} if ({e_on_off_rr}.t_j == {t_j} and "
            f"{e_on_off_rr}.dataset_type == 'graph_i_e')],[{e_on_off_rr} for {e_on_off_rr} in self.{s_d}.{e_on_off_rr} if "
            f"{e_on_off_rr}.dataset_type == 'graph_r_e']",
            "<string>", "eval")
        ie_datasets, re_datasets = eval(code)
        i_e_dataset, r_e_dataset = None, None
        if len(ie_datasets) == 0 or re_datasets == 0:
            code = compile(
                f"[({e_on_off_rr}.t_j, {e_on_off_rr}.v_g, {e_on_off_rr}.v_supply, {e_on_off_rr}.r_g) for {e_on_off_rr} in self.{s_d}.{e_on_off_rr}]",
                "<string>", "eval")
            available_datasets = eval(code)
            logger.info("Available operating points: (t_j, v_g, v_supply, r_g)")
            logger.info(available_datasets)
            raise ValueError("No data available for get_graph_i_e at the given operating point. "
                             "A list of available operating points is printed above.")
        elif len(ie_datasets) > 1:
            logger.info("multiple datasets were found that are consistent with the chosen operating point.")
            match = False
            for re_curve in re_datasets:
                for curve in ie_datasets:
                    if curve.v_supply == re_curve.v_supply and curve.t_j == re_curve.t_j and curve.v_g == re_curve.v_g:
                        i_e_dataset = curve
                        r_e_dataset = re_curve
                        match = True
            text_to_print = "A match found in r_e characteristics for the chosen operating point and therefore will be used" \
                if match else "The first of these sets is automatically chosen because selection of a different dataset is not yet implemented."
            logger.info(text_to_print)
        elif len(ie_datasets) == 1:
            # function get_object_r_e_simplified can be called here instead of calling in a separate line of calc_object_i_e method
            i_e_dataset = ie_datasets[0]
        return i_e_dataset, r_e_dataset

    def get_object_r_e_simplified(self, e_on_off_rr: str, t_j: float, v_g: float, v_supply: float, normalize_t_to_v: float) -> list:
        """
        Get the loss graphs out of the transistor class, simplified version.

        :param e_on_off_rr: can be the following: 'e_on', 'e_off' or 'e_rr'
        :type e_on_off_rr: str
        :param t_j: junction temperature
        :type t_j: float
        :param v_g: gate voltage
        :type v_g: float
        :param normalize_t_to_v: factor t:v (junction-temperature divided by gate voltage)
        :type normalize_t_to_v: float
        :param v_supply: supply voltage
        :type v_supply: float

        :return: e_on.graph_r_e or e_off.graph_r_e or e_rr.graph_r_e
        :rtype: list
        """
        # Note: this is necessary due to e_on/e_off and e_rr are stored to switch and diode
        if e_on_off_rr == 'e_on' or e_on_off_rr == 'e_off':
            # s_d stands for 'switch or diode'
            s_d = 'switch'
        else:
            s_d = 'diode'

        # use eval function to choose variable e_on/e_off/e_rr
        # compile is necessary due to using eval combined with if-statement
        # https://realpython.com/python-eval-function/
        code = compile(
            f"[{e_on_off_rr} for {e_on_off_rr} in self.{s_d}.{e_on_off_rr} if {e_on_off_rr}.dataset_type == 'graph_r_e' and "
            f"{e_on_off_rr}.v_supply == {v_supply}]",
            "<string>", "eval")
        candidate_datasets = eval(code)
        # Find closest loss curve
        node = np.array([[t_j / normalize_t_to_v, v_g]])
        lossdata_t_js = np.array([curve.t_j for curve in candidate_datasets])
        lossdata_v_gs = np.array([0 if curve.v_g is None else curve.v_g for curve in candidate_datasets])
        nodes = np.array([lossdata_t_js / normalize_t_to_v, lossdata_v_gs]).transpose()
        index_lossdata = distance.cdist(node, nodes).argmin()
        dataset = candidate_datasets[index_lossdata]
        if dataset is None:
            code = compile(
                f"[({e_on_off_rr}.t_j, {e_on_off_rr}.v_g, {e_on_off_rr}.v_supply, {e_on_off_rr}.r_g) for {e_on_off_rr} in self.{s_d}.{e_on_off_rr}]",
                "<string>", "eval")
            available_datasets = eval(code)
            logger.info("Available operating points: (t_j, v_g, v_supply, r_g)")
            logger.info(available_datasets)
            raise ValueError("No data available for get_graph_r_e at the given operating point. "
                             "A list of available operating points is printed above.")
        return dataset

    def calc_object_i_e(self, e_on_off_rr: str, r_g: float, t_j: float, v_supply: float, normalize_t_to_v: float) \
            -> SwitchEnergyData:
        """
        Calculate loss curves for other gate resistor than the standard one.

        This function uses i_e loss curve in combination with r_e loss curve, to calculate a new i_e loss curve for
        a chosen gate resistor. Also voltage correction is implemented (e.g. half voltage compared to datasheet means half losses)

        :param e_on_off_rr: 'e_on', 'e_off', 'e_rr'
        :type e_on_off_rr: str
        :param r_g: gate resistor of interest
        :type r_g: float
        :param t_j: junction temperature of interest
        :type t_j: float
        :param v_supply: supply voltage of interest
        :type v_supply: float
        :param normalize_t_to_v: a normalize value used to evaluate cartesian distance
        :type normalize_t_to_v: float

        :raises Exception: When given gate resistance exceeds the existing maximum

        :return: object with corrected i_e curves due to r_g and v_supply at given t_j
        :rtype: list

        .. note:: r_e_object may has not same voltage as i_e_object.
        .. todo:: r_e_object may has not same voltage as i_e_object.

        """
        try:
            # search for graph_i_e, simplified version
            i_e_object, r_e_object = self.get_object_i_e_simplified(e_on_off_rr, t_j)
            r_e_object = r_e_object if r_e_object else self.get_object_r_e_simplified(e_on_off_rr, t_j, i_e_object.v_g, i_e_object.v_supply, normalize_t_to_v)
            r_g_max = np.amax(r_e_object.graph_r_e[0])
            v_supply_chosen = v_supply
            if r_g > r_g_max:
                raise Exception("Given r_g exceeds the graph range : r_g_max = {0}".format(r_g_max))
            if not v_supply or v_supply > self.v_abs_max:
                v_supply_chosen = i_e_object.v_supply
                logger.info("Invalid v_supply provided : v_supply = {0} and choosing v_supply = {1} ".format(v_supply, v_supply_chosen))

            args = {
                'dataset_type': 'graph_i_e',
                'r_g': r_g,
                'v_supply': v_supply_chosen,
                'graph_i_e': self.calc_i_e_curve_using_r_e_curve(i_e_object, r_e_object, r_g, v_supply_chosen),
                't_j': i_e_object.t_j,
                'v_g': i_e_object.v_g,
            }
            # check dictionary
            isvalid_dict(args, 'SwitchEnergyData')
            # pack to object
            object_i_e_calc = SwitchEnergyData(args)
            return object_i_e_calc
        except Exception as e:
            logger.info("{0} loss at chosen parameters: R_g = {1}, T_j = {2}, v_supply = {3} could not be possible due to \n {4}".format(
                e_on_off_rr, r_g, t_j, v_supply, e.args[0]))
            raise e

    def calc_i_e_curve_using_r_e_curve(self, i_e_object: SwitchEnergyData, r_e_object: SwitchEnergyData,
                                       r_g: float, v_supply_chosen: float) -> np.array:
        """
        Calculate the loss energy curve at the provided gate resistance value based on the r_e_graph data.

        :param i_e_object: selected loss energy curve object of datatype = 'graph_i_e'
        :type i_e_object: Transistor.SwitchEnergyData
        :param r_e_object: associated loss energy curve object of datatype = 'graph_r_e'
        :type r_e_object: Transistor.SwitchEnergyData
        :param r_g: selected gate resistance for curve re-estimation
        :type r_g: int
        :param v_supply_chosen: selected supply voltage for curve re-estimation
        :type v_supply_chosen: int

        :return: numpy 2d data representing loss energy of datatype = 'graph_i_e'
        :rtype: np.array
        """
        # generate copy
        object_i_e_calc = i_e_object.graph_i_e.copy()

        # calculate factor for new gate resistor to nominal gate resistor
        loss_at_rg = np.interp(r_g, r_e_object.graph_r_e[0], r_e_object.graph_r_e[1])
        loss_at_rgnom = np.interp(i_e_object.r_g, r_e_object.graph_r_e[0], r_e_object.graph_r_e[1])
        factor_current = loss_at_rg / loss_at_rgnom

        # current correction with factor
        object_i_e_calc[1] = factor_current * object_i_e_calc[1]

        # voltage correction, linear
        object_i_e_calc[1] = v_supply_chosen / i_e_object.v_supply * object_i_e_calc[1]
        # generate dictionary for class SwitchEnergyData
        return object_i_e_calc

    def calc_lin_channel(self, t_j: float, v_g: float, i_channel: float, switch_or_diode: str) -> tuple[float, float]:
        """
        Get interpolated channel parameters.

        This function searches for ui_graphs with the chosen t_j and v_g. At
        the desired current, the equivalent parameters for u_channel and r_channel are returned

        :param t_j: junction temperature
        :type t_j: float
        :param v_g: gate voltage
        :type v_g: float
        :param i_channel: current to linearize the channel
        :type i_channel: float
        :param switch_or_diode: 'switch' or 'diode'
        :type switch_or_diode: str

        :raises ValueError: Raised when the given arguments either exceed the maximum values or not the expected values

        :return: Linearized parameters for v_channel, r_channel
        :rtype: tuple[float, float]

        .. todo::
            - rethink method name. May include switch or diode as a parameter and use one global function
            - check if this function works for all types of transistors
            - Error handling
            - Unittest for this method
        """
        # in case of failure, return None
        v_channel = None
        r_channel = None

        if i_channel > self.i_abs_max:
            raise ValueError(
                f"In calc_lin_channel: linearizing current ({i_channel} A) higher than i_absmax ({self.i_abs_max} A)")

        if switch_or_diode == 'switch':
            candidate_datasets = [channel for channel in self.switch.channel
                                  if (channel.t_j == t_j and channel.v_g == v_g)]
            if len(candidate_datasets) == 0:
                available_datasets = [(channel.t_j, channel.v_g) for channel in self.switch.channel]
                logger.info("Available operating points: (t_j, v_g)")
                logger.info(available_datasets)
                raise ValueError("No data available for linearization at the given operating point. "
                                 "A list of available operating points is printed above.")
            elif len(candidate_datasets) > 1:
                logger.info("During linearization, multiple datasets were found that are consistent with the chosen "
                            "operating point. The first of these sets is automatically chosen because selection of a "
                            "different dataset is not yet implemented.")

            # interpolate data
            voltage_interpolated = np.interp(i_channel, candidate_datasets[0].graph_v_i[1],
                                             candidate_datasets[0].graph_v_i[0])
            # check kind of transistor type due to forward voltage value
            if self.type in ['MOSFET', 'SiC-MOSFET']:
                # transistor has no forward voltage
                # return values
                v_channel = 0  # no forward voltage du to resistance behaviour
                r_channel = voltage_interpolated / i_channel
            else:
                # transistor has forward voltage. Other interpolating point will be with 10% more current
                # ToDo: Test this function if IGBT is available
                voltage_interpolated_2 = np.interp(i_channel * 0.9, candidate_datasets[0].graph_v_i[1],
                                                   candidate_datasets[0].graph_v_i[0])
                r_channel = (voltage_interpolated - voltage_interpolated_2) / (0.1 * i_channel)
                v_channel = voltage_interpolated - r_channel * i_channel
        elif switch_or_diode == 'diode':
            if self.type in ['SiC-MOSFET', 'GaN-Transistor']:
                candidate_datasets = [channel for channel in self.diode.channel
                                      if (channel.t_j == t_j and channel.v_g == v_g)]
                if len(candidate_datasets) == 0:
                    available_datasets = [(channel.t_j, channel.v_g) for channel in self.diode.channel]
                    logger.info("Available operating points: (t_j, v_g)")
                    logger.info(available_datasets)
                    raise ValueError("No data available for linearization at the given operating point. "
                                     "A list of available operating points is printed above.")
                elif len(candidate_datasets) > 1:
                    logger.info("During linearization, multiple datasets were found that are consistent with the chosen "
                                "operating point. The first of these sets is automatically chosen because selection of a "
                                "different dataset is not yet implemented.")
            else:
                candidate_datasets = [channel for channel in self.diode.channel
                                      if channel.t_j == t_j]
                if len(candidate_datasets) == 0:
                    available_datasets = [channel.t_j for channel in self.diode.channel]
                    logger.info("Available operating points: (t_j)")
                    logger.info(available_datasets)
                    raise ValueError("No data available for linearization at the given operating point. "
                                     "A list of available operating points is printed above.")
                elif len(candidate_datasets) > 1:
                    logger.info("During linearization, multiple datasets were found that are consistent with the chosen "
                                "operating point. The first of these sets is automatically chosen because selection of a "
                                "different dataset is not yet implemented.")
            # interpolate data
            voltage_interpolated = np.interp(i_channel, candidate_datasets[0].graph_v_i[1],
                                             candidate_datasets[0].graph_v_i[0])
            voltage_interpolated_2 = np.interp(i_channel * 0.9, candidate_datasets[0].graph_v_i[1],
                                               candidate_datasets[0].graph_v_i[0])
            r_channel = (voltage_interpolated - voltage_interpolated_2) / (0.1 * i_channel)
            v_channel = voltage_interpolated - r_channel * i_channel
        else:
            raise ValueError("switch_or_diode must be either specified as 'switch' or 'diode' for channel "
                             "linearization.")
        return round(v_channel, 6), round(r_channel, 9)

    def calc_thermal_params(self, input_type: str = None, order: int = 4, plotbit: bool = False) -> None:
        """
        Generate thermal parameters like Rth_total, tau_total, Cth_total and vectors like Rth_vector, tau_vector, Cth_vector.

        Based on data availability passed by the user while creating a new transistor object.

        +-------------------------------------------+-------------------+-----------------+-----------------------------+
        | Cases                                     | Vectors           | Total           | To be computed              |
        +===========================================+===================+=================+=============================+
        | Only curve available                      | R_th, C_th, tau   | R_th, C_th, tau |  Compute all parameters     |
        +-------------------------------------------+-------------------+-----------------+-----------------------------+
        | Curve and R_th_total available            | R_th, C_th, tau   | C_th, tau       |  No overwrite of R_th_total |
        +-------------------------------------------+-------------------+-----------------+-----------------------------+
        | Total values available, no curve available| C_th              |  None           |  Compute only C_th_total    |
        +-------------------------------------------+-------------------+-----------------+-----------------------------+
        | Vectors available AND/OR                  | Cth               | Cth             |- No curve fitting necessary |
        | Curve available                           |                   |                 |- Do not overwrite R_th_total|
        +-------------------------------------------+-------------------+-----------------+-----------------------------+

        :param order: The length of the polynomial to be used for curve fitting based parameters extraction. (cannot be more than 5)
        :type order: int
        :param input_type: The type of object for which the thermal parameters need to computed. Can be either 'switch' or 'diode' type
        :type input_type: str
        :param plotbit: A boolean flag to visualize the fitted curve using matplotlib plotting features
        :type plotbit: bool

        :return: Foster object filled with missing parameters within the input_type object of transistor object
        :rtype: None
        """
        try:
            code = compile(f"self.{input_type}.thermal_foster", "<string>", "eval")
            foster_args = eval(code)
            if foster_args.r_th_vector is not None and foster_args.tau_vector is not None and len(foster_args.tau_vector) == len(foster_args.r_th_vector):
                foster_args.c_th_vector = [x / y for x, y in zip(foster_args.r_th_vector, foster_args.tau_vector)]
                if foster_args.tau_total is None:
                    foster_args.tau_total = round(sum(foster_args.tau_vector), 4)
                if foster_args.r_th_total is None:
                    foster_args.r_th_total = round(sum(foster_args.r_th_vector), 4)
                foster_args.c_th_total = round(foster_args.tau_total / foster_args.r_th_total, 4)
            else:
                if order > 5:
                    raise ValueError("Summation is limited to only n = 5")
                if foster_args.graph_t_rthjc is not None and foster_args.graph_t_rthjc.any():
                    rth = foster_args.graph_t_rthjc[1]
                    time = foster_args.graph_t_rthjc[0]
                    func = gen_exp_func(order)
                    rth_max = max(rth)

                    def upper_limit(x):
                        return {1: 1, 2: 0.5, 3: 0.33, 4: 0.25, 5: 0.2}.get(x, 1)

                    popt, _ = curve_fit(func, time, rth, maxfev=5000, bounds=([0] * 2 * order, [rth_max * upper_limit(order)] * 2 * order))
                    rth_op = func(time, *popt)
                    tau_values = popt[1::2]
                    rth_values = popt[0::2]
                    tuple_list = sorted(zip(tau_values, rth_values))
                    cap_values = [x / y for x, y in tuple_list]
                    tau_values, rth_values = (list(t) for t in zip(*tuple_list))
                    residuals = rth - rth_op
                    ss_res = np.sum(residuals ** 2)
                    ss_tot = np.sum((rth - np.mean(rth)) ** 2)
                    r_squared = 1 - (ss_res / ss_tot)
                    logger.info("R^2 score:", r_squared)
                    if len(rth_values) > 1:
                        foster_args.r_th_vector = [round(x, 5) for x in rth_values]
                        foster_args.tau_vector = [round(x, 5) for x in tau_values]
                        foster_args.c_th_vector = [round(x, 5) for x in cap_values]
                    if foster_args.r_th_total is None:
                        foster_args.r_th_total = round(sum(rth_values), 4)
                    foster_args.tau_total = round(sum(tau_values), 4)
                    foster_args.c_th_total = round(foster_args.tau_total / foster_args.r_th_total, 4)
                    if plotbit:
                        logger.info("Computed Rth values: ", rth_values)
                        logger.info("Computed tau values: ", tau_values)
                        logger.info("Computed Cth values: ", cap_values)
                        fig = plt.figure()
                        ax = fig.add_subplot(111)
                        ax.loglog(time, rth)
                        ax.loglog(time, func(time, *popt))
                        ax.set_xlabel('Time : $t$ [sec]')
                        ax.set_ylabel('Thermal impedance: $Z_{th(j-c)}$ [K/W ]')
                        ax.grid()
                        plt.show()
                elif foster_args.r_th_total is not None and foster_args.tau_total is not None:
                    foster_args.c_th_total = round(foster_args.tau_total / foster_args.r_th_total, 4)
                else:
                    raise Exception(f"graph_t_rthjc in {input_type}'s foster thermal object is empty!")
        except Exception as e:
            logger.info("Thermal parameter computation failed: {0}".format(e))
            logger.info("This also occurs when there is no thermal impedance given.")
        else:
            exec(f"self.{input_type}.thermal_foster = foster_args")
            logger.info(input_type, ':Thermal parameters re-assigned to foster object')

    def compare_channel_linearized(self, i_channel: float, t_j: float = 150, v_g: float = 15) -> None:
        """
        Show channel plots for switch and diode comparing the linearized graph and the original graph.

        This function searches for the closest available curves for given arguments t_j and v_g

        :param i_channel: current to linearize the channel
        :type i_channel: float
        :param t_j: junction temperature of interest, default set to 150 degree
        :type t_j: float
        :param v_g: gate voltage of interest, default set to 15V
        :type v_g: float
        """
        # search for closest objects
        switch_channel, eon, eoff = self.switch.find_approx_wp(t_j, v_g, normalize_t_to_v=10, switch_energy_dataset_type="graph_i_e")
        diode_channel, err = self.diode.find_approx_wp(t_j, v_g, normalize_t_to_v=10,
                                                       switch_energy_dataset_type="graph_i_e")
        # linearize channels at given points
        s_v_channel, s_r_channel = self.calc_lin_channel(switch_channel.t_j, switch_channel.v_g, i_channel, 'switch')
        d_v_channel, d_r_channel = self.calc_lin_channel(diode_channel.t_j, diode_channel.v_g, i_channel, 'diode')

        logger.info('Linearized values. Switch at {0} °C and {1} V, diode at {2} °C and {3} V'.format(switch_channel.t_j, switch_channel.v_g,
                                                                                                      diode_channel.t_j, diode_channel.v_g))
        logger.info(" s_v_channel = {0} V".format(s_v_channel))
        logger.info(" s_r_channel = {0} Ohm".format(s_r_channel))
        logger.info(" d_v_channel = {0} V".format(d_v_channel))
        logger.info(" d_r_channel = {0} Ohm".format(d_r_channel))

        i_vec = np.linspace(0, self.i_abs_max)
        s_v_vec = s_v_channel + s_r_channel * i_vec
        d_v_vec = d_v_channel + d_r_channel * i_vec

        # insert zeros to start linearized curve from zero
        i_vec = np.insert(i_vec, 0, 0)
        s_v_vec = np.insert(s_v_vec, 0, 0)
        d_v_vec = np.insert(d_v_vec, 0, 0)

        plt.figure()
        # generate switch curve
        plt.subplot(1, 2, 1)
        plt.plot(switch_channel.graph_v_i[0], switch_channel.graph_v_i[1], label=f"Datasheet, t_j = {switch_channel.t_j} °C, v_g = {switch_channel.v_g} V")
        plt.plot(s_v_vec, i_vec, label=f"Linearized curve, t_j = {switch_channel.t_j} °C, v_g = {switch_channel.v_g} V")
        plt.xlabel('Voltage in V')
        plt.ylabel('Current in A')
        plt.title('Switch')
        plt.grid()
        plt.legend()

        # generate diode curve
        plt.subplot(1, 2, 2)
        plt.plot(diode_channel.graph_v_i[0], diode_channel.graph_v_i[1], label=f"Datasheet, t_j = {diode_channel.t_j} °C, v_g = {diode_channel.v_g} V")
        plt.plot(d_v_vec, i_vec, label=f"Linearized curve, t_j = {diode_channel.t_j} °C, v_g = {diode_channel.v_g} V")
        plt.xlabel('Voltage in V')
        plt.ylabel('Current in A')
        plt.title('Diode')
        plt.grid()
        plt.legend()

        # plt.tight_layout()
        plt.show()
     
    def raw_measurement_data_plots(self) -> list:
        """
        Plot raw measurement data.

        Take the raw measurement data attribute and traverses through
        the list for each present method and loads the ids and vds data for
        in 3 separate lists. The three lists are used as input for plot_curves function which
        returns the combined and scaled plots for the data. The combined plots are returned in img bytes format
        using the get_img_raw_data function. The img plots are then stored in plots_vds_id_t list.
        The test conditions of the data are then also added in a list form to the plots_vds_id_t. 
        
        return  plots in img form along test conditions in a list   
        rtype list of img plots along test conditions
        """
        graph_count = 0
        plots_vds_id_t = []
        plots_with_conditions = []     
        for raw_measurements in self.raw_measurement_data:
            graph_count = 0
            conditions = {}
            plots_vds_id_t = []
            raw_data_vds = raw_measurements.dpt_on_vds
            raw_data_ids = raw_measurements.dpt_on_id
            for measurement_count, measurement in enumerate(raw_data_ids):
                time_val = []
                vds_val = []
                id_val = []
                for measurement_point, point_data in enumerate(measurement):
                    time_val.append(point_data[0])
                    vds_val.append(raw_data_vds[measurement_count][measurement_point][1])
                    id_val.append(point_data[1])
                plots_vds_id_t.append(self.plot_curves(time_val, vds_val, id_val))
                graph_count += 1
            conditions['T_j'] = [raw_measurements.t_j, '°C']
            conditions['V_supply'] = [raw_measurements.v_supply, 'V']
            conditions['V_gate'] = [raw_measurements.v_g, 'V']
            conditions['V_gate_off'] = [raw_measurements.v_g_off, 'V']
            conditions['R_g'] = [raw_measurements.r_g, 'Ohms']
            conditions['R_goff'] = [raw_measurements.r_g_off, 'Ohms']
            conditions['L_load'] = [raw_measurements.load_inductance, 'uH']
            conditions['L_commutation'] = [raw_measurements.commutation_inductance, 'uH']
            conditions["total graphs"] = graph_count
            plots_with_conditions.append([conditions, plots_vds_id_t, ])
        return plots_with_conditions

    def plot_curves(self, time_array, vds_values, ids_values, buffer_req: bool = False):
        """ 
        Take three lists of time, vds and id values and generates a combined plot.

        Calls the get_img_raw_data function for returning img form of the plot and returns the images.
        
        :param time_array : time values in the raw measurement data
        :type time_array: list
        :param vds_values : vds values in the raw measurement data
        :type vds_values: list
        :param ids_values : id values in the raw measurement data
        :type ids_values: list
        :param buffer_req: True to set a buffer
        :type buffer_req: bool
        return image form of the plot
        rtype decoded raw image data to utf-8
        """
        color = 'tab:blue'
        plt.xlabel('time (s)')
        plt.ylabel('Voltage (V)', color=color)
        plt.plot(time_array, vds_values, color=color)
        plt.tick_params(axis='y', labelcolor=color)
        plot_ids = plt.twinx()
        color = 'tab:red'
        plot_ids.set_ylabel('Current (A)', color=color)
        plot_ids.plot(time_array, ids_values, color=color)
        plot_ids.tick_params(axis='y', labelcolor=color)
        plt.tight_layout()
        plt.grid(color='green', linestyle='--', linewidth=0.5)
        return get_img_raw_data(plt)

    def export_datasheet(self, build_collection: bool = False) -> str | None:
        """
        Generate and export the virtual datasheet in form of a pdf-file.

        :param build_collection:
        :type build_collection: bool
        :return: pdf file is created in the current working directory
        :rtype: None

        :Example:

        >>> import transistordatabase as tdb
        >>> transistor = tdb.load('Fuji_2MBI100XAA120-50')
        >>> transistor.export_datasheet()

        .. todo:: Instead of html file, generating a pdf file without third party requirements is a better option
        """
        pdf_data = {}
        raw_measurement_plots = {}
        devices = {}
        skip_ids = ['_id', 'wp', 'c_oss', 'c_iss', 'c_rss', 'graph_v_ecoss', 'c_oss_er', 'c_oss_tr']
        cap_plots = {'$c_{oss}$': self.c_oss, '$c_{rss}$': self.c_rss, '$c_{iss}$': self.c_iss}
        if (len(self.raw_measurement_data) > 0):
            raw_measurement_plots = self.raw_measurement_data_plots()
            # logger.info(raw_measurement_plots)
            # conditions = raw_measurement_plots[-1]
            # plots = raw_measurement_plots[:-1]
            logger.info(raw_measurement_plots[0])
            pdf_data['plots'] = {'c_plots': get_vc_plots(cap_plots)}
            pdf_data.update({'raw_measurement_data': raw_measurement_plots})    
        else:
            pdf_data['plots'] = {'c_plots': get_vc_plots(cap_plots)}
        # pdfData['c_plots'] = get_vc_plots(cap_plots)
        # pdfData['soa'] = self.plot_soa(True)
        for attr in dir(self):
            if not callable(getattr(self, attr)) and not attr.startswith("__"):
                if attr == 'switch' or attr == 'diode':
                    devices[attr] = getattr(self, attr).collect_data()
                elif attr not in skip_ids and getattr(self, attr):
                    pdf_data[attr.capitalize()] = getattr(self, attr)
                elif (attr == 'c_oss_er' or attr == 'c_oss_tr') and getattr(self, attr) is not None:  # to be modified for boundary case
                    pdf_data[attr.capitalize()] = getattr(self, attr).c_o
        trans, diode, switch = attach_units(pdf_data, devices)
        img_path = os.path.join(os.path.dirname(__file__), 'images', 'lea-upb.png')
        image_file_obj = open(img_path, "rb")
        image_binary_bytes = image_file_obj.read()
        buf = io.BytesIO(image_binary_bytes)
        encoded_img_data = base64.b64encode(buf.getvalue())
        client_img = encoded_img_data.decode('UTF-8')
        # loaded data into jinja html template for generating the pdf
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=True, extensions=['jinja2.ext.loopcontrols', 'jinja2.ext.do'])
        template = env.get_template('VirtualDatasheet_TransistorTemplate.html')
        html = template.render(trans=trans, switch=switch, diode=diode, image=client_img)
        pdf_name = trans['Name'][0] + ".pdf"
        pdf_path = os.path.join(os.getcwd(), pdf_name)

        if not build_collection:
            html_to_pdf(html, pdf_name, pdf_path)
        else:
            return html  
        
    def export_simulink_loss_model(self, r_g_on: float = None, r_g_off: float = None, v_supply: float = None,
                                   normalize_t_to_v: float = 10) -> None:
        """
        Export a simulation model for simulink inverter loss models.

        .mat file for import in matlab/simulink

        See also: https://de.mathworks.com/help/physmod/sps/ug/loss-calculation-in-a-three-phase-3-level-inverter.html

        :param r_g_on: gate turn on resistance, optional
        :type r_g_on: float
        :param r_g_off: gate turn off resistance, optional
        :type r_g_off: float
        :param v_supply: switch supply voltage, optional
        :type v_supply: float
        :param normalize_t_to_v: a normalize value used in computing cartesian distance
        :type normalize_t_to_v: float

        :raises Exception: Re-raised excception by calling calc_object_i_e(..)
        :raises ValueError: Raised when the switch type is other than IGBT

        :Example:

        >>> import transistordatabase as tdb
        >>> transistor = tdb.load('Infineon_FF200R12KE3')
        >>> transistor.export_simulink_loss_model()

        .. note::
            - temperature next to 25 and 150 degree at 15V gate voltage will be used for channel and switching loss
            - in case of just one temperature curve, the upper temperature will increased (+1K) to bring a small temperature change in the curves.
            - only necessary data from tdb will be exported to simulink
            - Simulink model need switching energy loss in 'mJ'
            - in case of no complete curve (e.g. not starting from zero), this tool will interpolate the curve

        .. todo:: C_th is fixed at the moment to 1e-6 for switch an diode. Needs to be calculated from ohter data
        """
        try:
            # Notes on exporting the file:
            # values need to be exported as np.double(), otherwise the Simulink-model can not interpolate the data (but displaying the curves is working...)

            if self.type.lower() != 'igbt':
                raise ValueError("In export_simulink_loss_model: Function is working for IGBTs only")

            t_j_lower = 25
            t_j_upper = 150
            v_g = 15

            logger.info("---------------------IGBT properties----------------------")
            switch_channel_object_lower, eon_object_lower, eoff_object_lower = self.switch.find_approx_wp(t_j_lower, v_g, normalize_t_to_v,
                                                                                                          switch_energy_dataset_type="graph_i_e")
            switch_channel_object_upper, eon_object_upper, eoff_object_upper = self.switch.find_approx_wp(t_j_upper, v_g, normalize_t_to_v,
                                                                                                          switch_energy_dataset_type="graph_i_e")
            if r_g_on:
                try:
                    eon_object_lower_calc = self.calc_object_i_e('e_on', r_g_on, eon_object_lower.t_j, v_supply, normalize_t_to_v)
                    eon_object_upper_calc = self.calc_object_i_e('e_on', r_g_on, eon_object_upper.t_j, v_supply, normalize_t_to_v)
                    if eon_object_lower_calc.t_j >= eon_object_upper_calc.t_j:
                        raise ValueError('Junction temperatures remain same')
                    else:
                        eon_object_lower = eon_object_lower_calc
                        eon_object_upper = eon_object_upper_calc
                except Exception as e:
                    logger.info('Choosing the default curve properties for e_on')
                else:
                    logger.info('Generated curve properties for e_on')
                    logger.info("Lower : R_g(on) = {0}, v_g(on)= {1}, T_j = {2}, v_supply = {3}".format(eon_object_lower.r_g, eon_object_lower.v_g,
                                                                                                        eon_object_lower.t_j, eon_object_lower.v_supply))
                    logger.info("Upper : R_g(on) = {0}, v_g(on)= {1}, T_j = {2}, v_supply = {3}".format(
                        eon_object_upper.r_g, eon_object_upper.v_g, eon_object_upper.t_j, eon_object_upper.v_supply))
            if r_g_off:
                try:
                    eoff_object_lower_calc = self.calc_object_i_e('e_off', r_g_off, eoff_object_lower.t_j, v_supply, normalize_t_to_v)
                    eoff_object_upper_calc = self.calc_object_i_e('e_off', r_g_off, eoff_object_upper.t_j, v_supply, normalize_t_to_v)
                    if eoff_object_lower_calc.t_j >= eoff_object_upper_calc.t_j:
                        raise ValueError('Junction temperatures remain same')
                    else:
                        eoff_object_lower = eoff_object_lower_calc
                        eoff_object_upper = eoff_object_upper_calc
                except Exception as e:
                    logger.info('Choosing the default curve properties for e_off')
                else:
                    logger.info('Generated curve properties for e_off')
                    logger.info("Lower : R_g(off) = {0}, v_g(off) = {1}, T_j = {2}, v_supply = {3}".format(eoff_object_lower.r_g, eoff_object_lower.v_g,
                                                                                                           eoff_object_lower.t_j, eoff_object_lower.v_supply))
                    logger.info("Upper : R_g(off) = {0}, v_g(off) = {1}, T_j = {2}, v_supply = {3}".format(
                        eoff_object_upper.r_g, eoff_object_upper.v_g, eoff_object_upper.t_j, eoff_object_upper.v_supply))

            # all elements need the same current vector size
            i_interp = np.linspace(0, self.i_abs_max, 10)

            switch_channel_lower_interp = np.interp(i_interp, switch_channel_object_lower.graph_v_i[1], switch_channel_object_lower.graph_v_i[0])
            switch_channel_upper_interp = np.interp(i_interp, switch_channel_object_upper.graph_v_i[1], switch_channel_object_upper.graph_v_i[0])
            switch_channel_array = np.array([switch_channel_lower_interp, switch_channel_upper_interp])

            e_on_lower_interp = np.interp(i_interp, eon_object_lower.graph_i_e[0], eon_object_lower.graph_i_e[1])
            e_on_upper_interp = np.interp(i_interp, eon_object_upper.graph_i_e[0], eon_object_upper.graph_i_e[1])
            e_on_array = np.array([e_on_lower_interp, e_on_upper_interp])

            e_off_lower_interp = np.interp(i_interp, eoff_object_lower.graph_i_e[0], eoff_object_lower.graph_i_e[1])
            e_off_upper_interp = np.interp(i_interp, eoff_object_upper.graph_i_e[0], eoff_object_upper.graph_i_e[1])
            e_off_array = np.array([e_off_lower_interp, e_off_upper_interp])

            # Simulink-power-electronic loss model can not handle curves in case of the temperatures are the same
            temp_t_j_switch_channel_upper = switch_channel_object_upper.t_j + 1 \
                if switch_channel_object_lower.t_j == switch_channel_object_upper.t_j else switch_channel_object_upper.t_j
            temp_t_j_eon_upper = eon_object_upper.t_j + 1 if eon_object_lower.t_j == eon_object_upper.t_j else eon_object_upper.t_j
            temp_t_j_eoff_upper = eoff_object_upper.t_j + 1 if eoff_object_lower.t_j == eoff_object_upper.t_j else eoff_object_upper.t_j

            switch_dict = {'T_j_channel': np.double([switch_channel_object_lower.t_j, temp_t_j_switch_channel_upper]),
                           'T_j_ref_on': np.double([eon_object_lower.t_j, temp_t_j_eon_upper]),
                           'T_j_ref_off': np.double([eoff_object_lower.t_j, temp_t_j_eoff_upper]),
                           'R_th_total': matlab_compatibility_test(self, 'Transistor.switch.thermal_foster.r_th_total')
                           if self.switch.thermal_foster.r_th_total != 0 else 1e-6,
                           'C_th_total': np.double(1),
                           'V_ref_on': np.double(eon_object_upper.v_supply),
                           'V_ref_off': np.double(eon_object_upper.v_supply),
                           'Eon': np.double(e_on_array * 1000),
                           'Eoff': np.double(e_off_array * 1000),
                           'v_channel': np.double(switch_channel_array),
                           'i_vec': np.double(i_interp),
                           }
            logger.info("---------------------Diode properties----------------------")
            diode_channel_object_lower, err_object_lower = self.diode.find_approx_wp(t_j_lower, v_g)
            diode_channel_object_upper, err_object_upper = self.diode.find_approx_wp(t_j_upper, v_g)
            if r_g_on:
                try:
                    err_object_lower_calc = self.calc_object_i_e('e_rr', r_g_on, err_object_lower.t_j, v_supply, normalize_t_to_v)
                    err_object_upper_calc = self.calc_object_i_e('e_rr', r_g_on, err_object_upper.t_j, v_supply, normalize_t_to_v)
                    if err_object_lower_calc.t_j >= err_object_upper_calc.t_j:
                        raise ValueError('Junction temperatures remain same')
                    else:
                        err_object_lower = err_object_lower_calc
                        err_object_upper = err_object_upper_calc
                except Exception as e:
                    logger.info('Choosing the default properties for e_rr')
                else:
                    logger.info('Generated curve properties for e_rr')
                    logger.info("Lower : R_g = {0}, v_g = {1}, T_j = {2}, v_supply = {3}".format(err_object_lower.r_g, err_object_lower.v_g,
                                                                                                 err_object_lower.t_j, err_object_lower.v_supply))
                    logger.info("Upper : R_g = {0}, v_g = {1}, T_j = {2}, v_supply = {3}".format(
                        err_object_upper.r_g, err_object_upper.v_g, err_object_upper.t_j, err_object_upper.v_supply))

            diode_channel_lower_interp = np.interp(i_interp, diode_channel_object_lower.graph_v_i[1], diode_channel_object_lower.graph_v_i[0])
            diode_channel_upper_interp = np.interp(i_interp, diode_channel_object_upper.graph_v_i[1], diode_channel_object_upper.graph_v_i[0])
            diode_channel_array = np.array([diode_channel_lower_interp, diode_channel_upper_interp])

            e_rr_lower_interp = np.interp(i_interp, err_object_lower.graph_i_e[0], err_object_lower.graph_i_e[1])
            e_rr_upper_interp = np.interp(i_interp, err_object_upper.graph_i_e[0], err_object_upper.graph_i_e[1])
            err_array = np.array([e_rr_lower_interp, e_rr_upper_interp])

            # Simulink-power-electronic loss model can not handle curves in case of the temperatures are the same
            temp_t_j_switch_channel_upper = diode_channel_object_upper.t_j + 1 \
                if diode_channel_object_lower.t_j == diode_channel_object_upper.t_j else diode_channel_object_upper.t_j
            temp_t_j_err_upper = err_object_upper.t_j + 1 if err_object_lower.t_j == err_object_upper.t_j else err_object_upper.t_j

            diode_dict = {
                'T_j_channel': np.double([diode_channel_object_lower.t_j, temp_t_j_switch_channel_upper]),
                'T_j_ref_rr': np.double([err_object_lower.t_j, temp_t_j_err_upper]),
                'R_th_total': matlab_compatibility_test(self,
                                                        'Transistor.diode.thermal_foster.r_th_total') if self.diode.thermal_foster.r_th_total != 0 else 1e-6,
                'C_th_total': np.double(1),
                'V_ref_rr': np.double(err_object_lower.v_supply),
                'v_channel': np.double(diode_channel_array),
                'i_vec': np.double(i_interp),
                'Err': np.double(err_array * 1000)

            }

            transistor_dict = {'Name': matlab_compatibility_test(self, 'Transistor.name'),
                               'R_th_CS': matlab_compatibility_test(self, 'Transistor.r_th_cs') if self.r_th_cs != 0 else 1e-6,
                               'R_th_Switch_CS': matlab_compatibility_test(self, 'Transistor.r_th_switch_cs') if self.r_th_switch_cs != 0 else 1e-6,
                               'R_th_Diode_CS': matlab_compatibility_test(self, 'Transistor.r_th_diode_cs') if self.r_th_diode_cs != 0 else 1e-6,
                               'Switch': switch_dict,
                               'Diode': diode_dict,
                               'file_generated': f"{datetime.today()}",
                               'file_generated_by': "https://github.com/upb-lea/transistordatabase",
                               'datasheet_hyperlink': self.datasheet_hyperlink,
                               'r_g_on': np.double(eon_object_lower.r_g),
                               'r_g_off': np.double(eoff_object_lower.r_g),
                               }

            sio.savemat(self.name.replace('-', '_') + '_Simulink_lossmodel.mat', {self.name.replace('-', '_'): transistor_dict})
            logger.info(f"Export files {self.name}_Simulink_lossmodel.mat to {os.getcwd()}")
        except Exception as e:
            logger.info("Simulink exporter failed: {0}".format(e))

    def export_matlab(self) -> None:
        """
        Export a transistor dictionary to a matlab dictionary.

        :Example:

        >>> import transistordatabase as tdb
        >>> transistor = tdb.load('Fuji_2MBI100XAA120-50')
        >>> transistor.export_matlab()
        """
        transistor_dict = self.convert_to_dict()
        dict_str = json.dumps(transistor_dict, default=json_util.default)

        # Note: Dict must be cleaned from 'None's to np.nan (= NaN in Matlab)
        # see https://stackoverflow.com/questions/35985923/replace-none-in-a-python-dictionary
        transistor_clean_dict = json.loads(dict_str, object_pairs_hook=dict2matlab)
        transistor_clean_dict['file_generated'] = f"{datetime.today()}"
        transistor_clean_dict['file_generated_by'] = "https://github.com/upb-lea/transistordatabase",

        sio.savemat(self.name.replace('-', '_') + '_Matlab.mat', {self.name.replace('-', '_'): transistor_clean_dict})
        logger.info(f"Export files {self.name.replace('-', '_')}_Matlab.mat to {os.getcwd()}")

    def collect_i_e_and_r_e_combination(self, switch_type: str, loss_type: str) -> tuple[list, list]:
        """
        Gather the i_e and r_e graph combinations from the available energy curves which are further used in gecko circuit exporter function.

        :param switch_type: argument to specify if either 'switch' or 'diode' energy curve to be considered
        :type switch_type: str
        :param loss_type: loss type 'e_on' and 'e_off' for switch type and 'e_rr' for diode type applicable
        :type loss_type: str

        :return: i_e, r_e indexes referencing to list[SwitchEnergyData] from the chosen switch_type
        :rtype: list, list
        """
        r_e_indexes = list()
        i_e_indexes = list()
        code = compile(f"self.{switch_type}.{loss_type}", "<string>", "eval")
        curves_set = eval(code)
        for index, _ in enumerate(curves_set):
            for next_index in range(index + 1, len(curves_set)):
                if not curves_set[index].dataset_type == curves_set[next_index].dataset_type and \
                        curves_set[index].t_j == curves_set[next_index].t_j and curves_set[index].v_g == curves_set[next_index].v_g \
                        and curves_set[index].v_supply == curves_set[next_index].v_supply:
                    if curves_set[index].dataset_type == 'graph_i_e':
                        i_e_indexes.append(index)
                        r_e_indexes.append(next_index)
                    else:
                        i_e_indexes.append(next_index)
                        r_e_indexes.append(index)
        # If no combos available then providing indexes of only dataset_type == graph_i_e
        if not any(i_e_indexes):
            for index, _ in enumerate(curves_set):
                if curves_set[index].dataset_type == 'graph_i_e':
                    i_e_indexes.append(index)
        return i_e_indexes, r_e_indexes

    def export_geckocircuits(self, recheck: bool = True, v_supply: float = None, v_g_on: float = None,
                             v_g_off: float = None, r_g_on: float = None, r_g_off: float = None) -> None:
        """
        Export transistor data to GeckoCIRCUITS.

        Two output files: 'Transistor.name'_Switch.scl and 'Transistor.name'_Diode.scl created in the current working directory

        :param recheck: Default to set to true, to enable the neighbouring select feature of the exporter
        :type recheck: bool
        :param v_supply: supply voltage for turn-on/off losses
        :type v_supply: float
        :param v_g_on: gate turn-on voltage
        :type v_g_on: float
        :param v_g_off: gate turn-off voltage
        :type v_g_off: float
        :param r_g_on: gate resistor for turn-on
        :type r_g_on: float
        :param r_g_off: gate resistor for turn-off
        :type r_g_off: float

        :Example:

        >>> import transistordatabase as tdb
        >>> transistor = tdb.load('Fuji_2MBI100XAA120-50')
        >>> transistor.export_geckocircuits(True, v_supply=600, v_g_on=15, v_g_off=-4, r_g_on=2.5, r_g_off=2.5)

        .. note:: These .scl files are then imported as semiconductor characteristics inside geckoCIRCUITS
        """
        # programming notes
        # exporting the diode:
        # diode off losses:
        # diode on losses: these on losses must be generated, even if they are zero
        # diode channel: it is not allowed to use more than one current that is zero (otherwise geckocircuits can not calculate the losses)
        # v_supply, v_g_on, v_g_off, r_g_on, r_g_off
        v_supply = v_supply if v_supply else self.v_abs_max / 2
        defaults_list = get_gatedefaults(self.type)

        v_d_channel = defaults_list[2] if v_g_off is None else v_g_off  # diode channel voltage
        v_d_err = defaults_list[3] if v_g_on is None else v_g_on  # diode reverse recovery gate voltage
        v_g_on = defaults_list[0] if v_g_on is None else v_g_on  # switch turn on gate voltage and channel voltage
        v_g_off = defaults_list[1] if v_g_off is None else v_g_off  # switch turn off gate voltage
        r_g_on = r_g_on if r_g_on else self.r_g_on_recommended
        r_g_off = r_g_off if r_g_off else self.r_g_off_recommended
        r_g_err = r_g_on

        # In future re-estimated neighbouring values
        switch_v_supply = v_supply
        diode_v_supply = v_supply
        switch_channel_vg = v_g_on  # initial set
        diode_channel_vg = v_d_channel  # initial value

        # get i_e and r_e curves combinations for neighbouring estimations
        eon_i_e_indexes, eon_r_e_indexes = self.collect_i_e_and_r_e_combination('switch', 'e_on')
        eoff_i_e_indexes, eoff_r_e_indexes = self.collect_i_e_and_r_e_combination('switch', 'e_off')
        err_i_e_indexes, err_r_e_indexes = self.collect_i_e_and_r_e_combination('diode', 'e_rr')
        # Find nearest neighbours for the recommended or provided defaults of v_supply, r_g, v_g
        if recheck:
            sw_selected_params = {'v_channel_gs': v_g_on, 'v_supply': switch_v_supply, 'v_g_on': v_g_on, 'v_g_off': v_g_off}
            diode_selected_params = {'v_channel_gs': v_g_off, 'v_supply': diode_v_supply, 'v_d_off': v_g_on}
            try:
                switch_channel_vg, switch_v_supply, v_g_on, v_g_off = self.switch.find_next_gate_voltage(sw_selected_params, export_type='gecko',
                                                                                                         check_specific_curves=[eon_i_e_indexes,
                                                                                                                                eoff_i_e_indexes])
                diode_channel_vg, diode_v_supply, v_d_err = self.diode.find_next_gate_voltage(diode_selected_params, export_type='gecko',
                                                                                              check_specific_curves=err_i_e_indexes)
            except MissingDataError as e:
                logger.info(e.args[0], e.em[e.args[0]] + ' .scl')

        # Gather data
        # Channel curves
        sw_channel_curves = list()
        for _, channel in enumerate(self.switch.channel):
            if channel.v_g == switch_channel_vg:
                sw_channel_curves.append(channel)

        diode_channel_curves = list()
        for _, channel in enumerate(self.diode.channel):
            if (channel.v_g is None and diode_channel_vg == 0) or channel.v_g == diode_channel_vg:
                diode_channel_curves.append(channel)

        # Loss energy curves : From the computed neighbours and recheck for provided or recommended r_g, if not compute the energy curve
        eon_curves = list()
        mapped_set = dict(zip(eon_i_e_indexes, eon_r_e_indexes))  # empty dict if no r_e and i_e combinations exists
        for index, curve in enumerate(self.switch.e_on):
            if index in eon_i_e_indexes and curve.v_supply == switch_v_supply and curve.v_g == v_g_on:
                # if no r_g is provided and also recommended is None final resort to get a r_g
                r_g_on = curve.r_g if r_g_on is None and len(mapped_set) else r_g_on
                if not curve.r_g == r_g_on and len(mapped_set):
                    mapped_r_e_object = self.switch.e_on[mapped_set[index]]
                    new_curve = curve.copy()
                    new_curve.graph_i_e = self.calc_i_e_curve_using_r_e_curve(new_curve, mapped_r_e_object, r_g_on, switch_v_supply)
                    logger.info('E_on curve estimated at {0} Ohm and supply voltage of {1}V'.format(r_g_on, switch_v_supply))
                    new_curve.r_g = r_g_on
                    eon_curves.append(new_curve)
                else:
                    logger.info('Exporting default E_on curves at the selected voltage parameters.'
                                '->Either re-estimation not possible or r_g specific curve found!')
                    eon_curves.append(self.switch.e_on[index])
                    r_g_on = self.switch.e_on[index].r_g

        eoff_curves = list()
        mapped_set = dict(zip(eoff_i_e_indexes, eoff_r_e_indexes))  # empty dict if no r_e and i_e combinations exists
        for index, curve in enumerate(self.switch.e_off):
            if index in eoff_i_e_indexes and curve.v_supply == switch_v_supply and curve.v_g == v_g_off:
                r_g_off = curve.r_g if r_g_off is None and len(mapped_set) else r_g_off
                if not curve.r_g == r_g_off and len(mapped_set):
                    mapped_r_e_object = self.switch.e_off[mapped_set[index]]
                    new_curve = curve.copy()
                    new_curve.graph_i_e = self.calc_i_e_curve_using_r_e_curve(new_curve, mapped_r_e_object, r_g_off, switch_v_supply)
                    logger.info('E_off curve estimated at {0} Ohm and supply voltage of {1}V'.format(r_g_off, switch_v_supply))
                    new_curve.r_g = r_g_on
                    eoff_curves.append(new_curve)
                else:
                    logger.info('Exporting default E_off curves at the selected voltage parameters.'
                                '->Either re-estimation not possible or r_g specific curve found!')
                    eoff_curves.append(self.switch.e_off[index])
                    r_g_off = self.switch.e_off[index].r_g

        err_curves = list()
        mapped_set = dict(zip(err_i_e_indexes, err_r_e_indexes))  # empty dict if no r_e and i_e combinations exists
        for index, curve in enumerate(self.diode.e_rr):
            if index in err_i_e_indexes and curve.v_supply == diode_v_supply and (0 if curve.v_g is None else curve.v_g) == v_d_err:
                r_g_err = curve.r_g if r_g_err is None and len(mapped_set) else r_g_err
                if not curve.r_g == r_g_err and len(mapped_set):
                    mapped_r_e_object = self.diode.e_rr[mapped_set[index]]
                    new_curve = curve.copy()
                    new_curve.graph_i_e = self.calc_i_e_curve_using_r_e_curve(new_curve, mapped_r_e_object, r_g_err, diode_v_supply)
                    logger.info('E_rr curve estimated at {0} Ohm and supply voltage of {1}V'.format(r_g_err, diode_v_supply))
                    new_curve.r_g = r_g_err
                    err_curves.append(new_curve)
                else:
                    logger.info('Exporting default E_rr curves at the selected voltage parameters.'
                                '->Either re-estimation not possible or r_g specific curve found!')
                    err_curves.append(self.diode.e_rr[index])
                    r_g_err = self.diode.e_rr[index].r_g

        # set numpy print options to inf, due to geckocircuits requests the data in one single line
        np.set_printoptions(linewidth=np.inf)

        ########################
        # export file for switch
        ########################
        if any(sw_channel_curves):

            file_switch = open(f"{self.name}_Switch(rg_on_{r_g_on})(rg_off_{r_g_off}).scl", "w")

            # switch channel data

            file_switch.write("anzMesskurvenPvCOND " + str(len(sw_channel_curves)) + "\n")
            for channel in sw_channel_curves:
                voltage = channel.graph_v_i[0]
                current = channel.graph_v_i[1]

                # gecko can not work in case of to currents are zero
                # so find the second current that is zero and replace it by a very small current
                for i in range(len(current)):
                    if i > 0 and current[i] == 0:
                        current[i] = 0.001

                if self.type.lower() == 'mosfet' or self.type.lower() == 'sic-mosfet' \
                        or self.type.lower() == 'gan-transistor':
                    # Note: Loss calculation in GeckoCIRCUITs will fail in case of reverse conducting
                    # Forward characteristic will be copied to backward-characteristic

                    voltage_reverse = voltage.copy()
                    voltage_reverse = voltage_reverse[voltage_reverse != 0]
                    voltage_reverse = np.flip(voltage_reverse)
                    voltage_reverse = [-x for x in voltage_reverse]
                    voltage = np.append(voltage_reverse, voltage)

                    current_reverse = current.copy()
                    current_reverse = current_reverse[current_reverse != 0]
                    current_reverse = np.flip(current_reverse)
                    current_reverse = [-x for x in current_reverse]
                    current = np.append(current_reverse, current)

                print_current = np.array2string(current, formatter={'float_kind': lambda x: "%.3f" % x})
                print_current = print_current[1:-1]
                print_voltage = np.array2string(voltage, formatter={'float_kind': lambda x: "%.3f" % x})
                print_voltage = print_voltage[1:-1]

                # for every loss curve, write
                file_switch.write("<LeitverlusteMesskurve>\n")
                file_switch.write(f"data[][] 2 {len(current)} {print_voltage} {print_current}")
                file_switch.write(f"\ntj {channel.t_j}\n")
                file_switch.write("<\LeitverlusteMesskurve>\n")

            # switch switching loss
            # check for availability of switching loss curves
            # count number of arrays with gate v_g == v_g_export

            file_switch.write(f"anzMesskurvenPvSWITCH {len(eon_curves) if len(eon_curves) else 1}\n")

            if not any(eon_curves) or not any(eoff_curves):
                logger.info('Switch: No loss curves found!')
                file_switch.write("<SchaltverlusteMesskurve>\n")
                file_switch.write("data[][] 3 2 0 10 0 0 0 0")
                file_switch.write("\ntj 25\n")
                file_switch.write("uBlock 400\n")
                file_switch.write("<\SchaltverlusteMesskurve>\n")
            else:
                for e_on in eon_curves:
                    on_current = e_on.graph_i_e[0]
                    on_energy = e_on.graph_i_e[1]
                    # search for off loss curves
                    for e_off in eoff_curves:
                        if e_off.v_supply == switch_v_supply and e_off.v_g == v_g_off and e_off.r_g == r_g_off and e_off.t_j == e_on.t_j:
                            # set off current and off energy
                            off_current = e_off.graph_i_e[0]
                            off_energy = e_off.graph_i_e[1]  # what the case if no matching off_energy found?

                            interp_current = np.linspace(0, on_current[-1], 10)
                            interp_on_energy = np.interp(interp_current, on_current, on_energy)
                            interp_off_energy = np.interp(interp_current, off_current, off_energy)

                            print_current = np.array2string(interp_current, formatter={'float_kind': lambda x: "%.2f" % x})
                            print_current = print_current[1:-1]
                            print_on_energy = np.array2string(interp_on_energy, formatter={'float_kind': lambda x: "%.8f" % x})
                            print_on_energy = print_on_energy[1:-1]

                            print_off_energy = np.array2string(interp_off_energy, formatter={'float_kind': lambda x: "%.8f" % x})
                            print_off_energy = print_off_energy[1:-1]

                            # for every loss curve, write
                            file_switch.write("<SchaltverlusteMesskurve>\n")
                            file_switch.write(f"data[][] 3 {len(interp_current)} {print_current} {print_on_energy} {print_off_energy}")
                            file_switch.write(f"\ntj {e_on.t_j}\n")
                            file_switch.write(f"uBlock {e_on.v_supply}\n")
                            file_switch.write("<\SchaltverlusteMesskurve>\n")

            file_switch.close()
            logger.info(f"Exported file {self.name}_Switch(rg_on_{r_g_on})(rg_off_{r_g_off}).scl  to {os.getcwd()}")
        else:
            logger.info('\nGecko exporter switch failed: No channel curve available at the selected v_g \n Try by setting recheck = True if set to False')

        ########################
        # export file for diode
        ########################
        if any(diode_channel_curves):
            file_diode = open(f"{self.name}_Diode(rg_{r_g_err}).scl", "w")

            # diode channel data
            # count number of arrays for conducting behaviour
            # in case of gan-transistor, search for v_g_off
            # in case of mosfet or igbt use all available data
            file_diode.write("anzMesskurvenPvCOND " + str(len(diode_channel_curves)) + "\n")
            # export conducting behaviour
            for n_channel in diode_channel_curves:
                # if v_g_diode is given, search for it. Else, use all data in Transistor.diode.channel
                # in case of gan-transistor, search for v_g_off
                # in case of mosfet or igbt use all available data
                voltage = np.abs(n_channel.graph_v_i[0])
                current = np.abs(n_channel.graph_v_i[1])

                # gecko can not work in case of to currents are zero
                # so find the second current that is zero and replace it by a very small current
                for i in range(len(current)):
                    if i > 0 and current[i] == 0:
                        current[i] = 0.001

                print_current = np.array2string(current, formatter={'float_kind': lambda x: "%.3f" % x})
                print_current = print_current[1:-1]
                print_voltage = np.array2string(voltage, formatter={'float_kind': lambda x: "%.3f" % x})
                print_voltage = print_voltage[1:-1]

                # for every loss curve, write
                file_diode.write("<LeitverlusteMesskurve>\n")
                file_diode.write(f"data[][] 2 {len(current)} {print_voltage} {print_current}")
                file_diode.write(f"\ntj {n_channel.t_j}\n")
                file_diode.write("<\LeitverlusteMesskurve>\n")

            # diode err loss
            # check for availability of switching loss curves
            # in case of no switching losses available, set curves to zero.
            # if switching losses will not set to zero, geckoCIRCUITS will use initial values
            if len(err_curves) == 0:
                logger.info('Diode: No loss curves found!')
                file_diode.write("anzMesskurvenPvSWITCH 1\n")
                file_diode.write("<SchaltverlusteMesskurve>\n")
                file_diode.write("data[][] 3 2 0 10 0 0 0 0")
                file_diode.write("\ntj 25\n")
                file_diode.write("uBlock 400\n")
                file_diode.write("<\SchaltverlusteMesskurve>\n")
            else:
                file_diode.write(f"anzMesskurvenPvSWITCH {len(err_curves)}\n")
                for curve_rr in err_curves:
                    if curve_rr.r_g == r_g_err:
                        rr_current = curve_rr.graph_i_e[0]
                        rr_energy = curve_rr.graph_i_e[1]

                        # forward recovery losses set to zero
                        fr_energy = np.zeros(len(rr_current))

                        print_fr_energy = np.array2string(fr_energy, formatter={'float_kind': lambda x: "%.8f" % x})
                        print_fr_energy = print_fr_energy[1:-1]

                        print_current = np.array2string(rr_current, formatter={'float_kind': lambda x: "%.2f" % x})
                        print_current = print_current[1:-1]
                        print_rr_energy = np.array2string(rr_energy, formatter={'float_kind': lambda x: "%.8f" % x})
                        print_rr_energy = print_rr_energy[1:-1]

                        # for every loss curve, write
                        file_diode.write("<SchaltverlusteMesskurve>\n")
                        file_diode.write(f"data[][] 3 {len(rr_current)} {print_current} {print_fr_energy} {print_rr_energy}")
                        file_diode.write(f"\ntj {curve_rr.t_j}\n")
                        file_diode.write(f"uBlock {curve_rr.v_supply}\n")
                        file_diode.write("<\SchaltverlusteMesskurve>\n")

            file_diode.close()
            logger.info(f"Exported file {self.name}_Diode(rg_{r_g_err}).scl to {os.getcwd()}")
        else:
            logger.info('\nGecko exporter diode failed: No channel curve available at the selected v_g \n Try by setting recheck = True if set to False')

        # set print options back to default
        np.set_printoptions(linewidth=75)

    def export_geckocircuits_coss(self, filepath: str = None, margin_factor: float = 1.2) -> None:
        """
        Export a nonlinear C_oss file for GeckoCIRCUITS.

        :param filepath: directory to save the .ncl file. CWD is used in case of None.
        :type filepath: str
        :param margin_factor: factor for margin. [1.0 = no margin], [1.2 = 20 % margin: DEFAULT]
        :type margin_factor: float
        """
        c_oss_data = self.c_oss[0].graph_v_c.T

        # Maybe check if data is monotonically
        # Check if voltage is monotonically rising
        if not np.all(c_oss_data[1:, 0] >= c_oss_data[:-1, 0], axis=0):
            warnings.warn("The voltage in csv file is not monotonically rising!", stacklevel=2)
        # Check if Coss is monotonically falling
        if not np.all(c_oss_data[1:, 1] <= c_oss_data[:-1, 1], axis=0):
            warnings.warn("The C_oss in csv file is not monotonically falling!", stacklevel=2)

        # Rescale and interpolate the csv data to have a nice 1V step size from 0V to v_max
        # A first value with zero volt will be added
        v_max = int(np.round(c_oss_data[-1, 0]))
        v_interp = np.arange(v_max + 1)
        coss_interp = margin_factor * np.interp(v_interp, c_oss_data[:, 0], c_oss_data[:, 1])
        # Since we now have an evenly spaced vector where x corresponds to the element-number of the vector
        # we don't have to store x (v_interp) with it.
        # To get Coss(V) just get the array element coss_interp[V]

        nlc_filename = f"{self.name}_c_oss.nlc"

        if filepath is None:
            file_c_oss = open(nlc_filename, "w")
        else:
            filename = os.path.join(filepath, nlc_filename)
            file_c_oss = open(filename, "w")

        # write Data to file, line by line
        for count, _ in enumerate(v_interp):
            file_c_oss.write(f"{v_interp[count]} {coss_interp[count]}\n")

        file_c_oss.close()
        logger.info(f"Exported file {nlc_filename} to {os.getcwd()}")

    def export_plecs(self, recheck: bool = True, gate_voltages: list | None = None) -> None:
        """
        Generate and export the switch and diode .xmls files to be imported into plecs simulator.

        Two output files: 'Transistor.name'_Switch.xml and 'Transistor.name'_Diode.xml created in the current working directory.

        :param recheck: enables the selection of gate voltages near to the provided values if not found
        :type recheck: bool
        :param gate_voltages: gate voltage like v_g_on, v_g_off, v_d_on, v_d_off
        :type gate_voltages: list

        :Example:

        >>> import transistordatabase as tdb
        >>> transistor = tdb.load('Fuji_2MBI200XAA065-50')
        >>> transistor.export_plecs(recheck=True, gate_voltages=[15, -15, 15, 0])
        """
        if gate_voltages is None:
            gate_voltages = []
        switch_xml_data, diode_xml_data = self.get_curve_data(recheck, gate_voltages)
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        env.globals["enumerate"] = enumerate
        for data in filter(None, [switch_xml_data, diode_xml_data]):
            if data['type'] == 'Diode':
                if len(data['TurnOffLoss']['CurrentAxis']) > 1:
                    data['TurnOffLoss']['Energy'][0] = [[0] * len(data['TurnOffLoss']['CurrentAxis'])] * len(
                        data['TurnOffLoss']['TemperatureAxis'])
                data['TurnOnLoss']['Energy'] = collections.OrderedDict(sorted(data['TurnOnLoss']['Energy'].items()))
                data['TurnOffLoss']['Energy'] = collections.OrderedDict(sorted(data['TurnOffLoss']['Energy'].items()))
                template = env.get_template('PLECS_Exporter_template_Diode.txt')
                output = template.render(diode=data)
                with open(data['partnumber'] + "_diode.xml", "w") as fh:
                    fh.write(output)
            elif data['type'] == 'IGBT' or data['type'] == 'MOSFET' or data['type'] == 'SiC-MOSFET':
                if data['type'] == 'MOSFET' or data['type'] == 'SiC-MOSFET':
                    data['TurnOnLoss']['Energy'][-10] = [[0] * len(data['TurnOnLoss']['CurrentAxis'])] * len(data['TurnOnLoss']['TemperatureAxis'])
                    data['TurnOffLoss']['Energy'][-10] = [[0] * len(data['TurnOffLoss']['CurrentAxis'])] * len(data['TurnOffLoss']['TemperatureAxis'])
                data['TurnOnLoss']['Energy'][0] = [[0] * len(data['TurnOnLoss']['CurrentAxis'])] * len(data['TurnOnLoss']['TemperatureAxis'])
                data['TurnOffLoss']['Energy'][0] = [[0] * len(data['TurnOffLoss']['CurrentAxis'])] * len(data['TurnOffLoss']['TemperatureAxis'])
                data['TurnOnLoss']['Energy'] = collections.OrderedDict(sorted(data['TurnOnLoss']['Energy'].items()))
                data['TurnOffLoss']['Energy'] = collections.OrderedDict(sorted(data['TurnOffLoss']['Energy'].items()))
                template = env.get_template('PLECS_Exporter_template_Switch.txt')
                output = template.render(transistor=data)
                str_decoded = output.encode()
                with open(data['partnumber'] + "_switch.xml", "w") as fh:
                    fh.write(str_decoded.decode())
        logger.info("Export files {0}_switch.xml and {1}_diode.xml to {2}".format(data['partnumber'], data['partnumber'], os.getcwd()))

    class WP:
        """
        WP class is intended for user calculations in Python. It is used to access transistor data in user-written programs.

        It allows the user to linearize the channel and store the result in transistor.wp. Switching loss curves can be stored
        for specific boundary conditions, so that the same variable is always accessed in the self-written program, regardless of the transistor.

        The class WP...

        - Always initialized as None.
        - Is always exported as None to .json or to the database.
        - Is a temporary workspace.
        """

        # type hints
        switch_v_channel: float | None
        switch_r_channel: float | None
        diode_v_channel: float | None
        diode_r_channel: float | None
        switch_channel: float | None
        diode_channel: float | None
        e_on: npt.NDArray[np.float64] | None  #: Units: Row 1: A; Row 2: J
        e_off: npt.NDArray[np.float64] | None  #: Units: Row 1: A; Row 2: J
        e_rr: npt.NDArray[np.float64] | None  #: Units: Row 1: A; Row 2: J
        v_switching_ref: float | None  #: Unit: V
        graph_v_coss: npt.NDArray[np.float64] | None  #: Units: Row 1: V; Row 2: F
        graph_v_eoss: npt.NDArray[np.float64] | None  #: Units: Row 1: V; Row 2: J
        graph_v_qoss: npt.NDArray[np.float64] | None  #: Units: Row 1: V; Row 2: C
        parallel_transistors: float | None  #: Unit: Number

        def __init__(self):
            self.switch_v_channel = None
            self.switch_r_channel = None
            self.diode_v_channel = None
            self.diode_r_channel = None
            self.switch_channel = None
            self.diode_channel = None
            self.e_on = None
            self.e_off = None
            self.e_rr = None
            self.v_switching_ref = None
            self.graph_v_eoss = None
            self.graph_v_qoss = None
            self.parallel_transistors = None

    def validate_transistor(self) -> dict:
        """
        Check the transistor object if it is valid for plecs exporter.

        Checks if curve characteristics and thermal network parameters of both switch and diode to be None or empty
        Appends corresponding codes for further verification in get_curve_data(..) method

        .. todo: May rename to 'plecs_validate_transistor'

        :return: Availability codes
        :rtype: dict
        """
        transistor_dict = self.convert_to_dict()
        codes = {'Switch': list(), 'Diode': list()}
        if not transistor_dict['switch']['channel']:
            codes['Switch'].append(1101)
        if not transistor_dict['switch']['e_on']:
            codes['Switch'].append(1102)
        if not transistor_dict['switch']['e_off']:
            codes['Switch'].append(1103)
        if not transistor_dict['switch']['thermal_foster']:
            codes['Switch'].append(201)
        if not transistor_dict['diode']['channel']:
            codes['Diode'].append(1201)
        if not transistor_dict['diode']['e_rr']:
            codes['Diode'].append(1202)
        if not transistor_dict['diode']['thermal_foster']:
            codes['Diode'].append(202)
        return codes

    def get_curve_data(self, channel_recheck: bool, gate_voltages: list) -> dict:
        """
        Prepare data for the PLECS exporter.

        Collect the available information of switch and diode from transistor object and passes it to plecs_exporter(..)
        for generating the diode and switch .xml files

        :param channel_recheck: if True, collect the channel and energy curve characteristics at nearest gate voltage if the given gate voltages are not found
        :type channel_recheck: bool
        :param gate_voltages: turn on and off gate voltages for selecting the curves of switch and diode
        :type gate_voltages: list

        :raises MissingDataError: If any information of switch or diode is missing completely

        :return: Switch and diode objects
        :rtype: dict
        """
        v_g_on, v_g_off, v_d_on, v_d_off = gate_voltages if len(gate_voltages) == 4 else \
            get_gatedefaults(self.type)
        v_g = v_g_on
        v_d = v_d_on
        transistor_dict = self.convert_to_dict()
        exception_codes = self.validate_transistor()
        is_body_diode = transistor_dict['type'].lower() in ['mosfet', 'sic-mosfet']
        # Gather switch data to fill in plecs template exporter
        plecs_transistor = None
        try:
            if 1101 in exception_codes['Switch']:
                raise MissingDataError(1101)
            plecs_transistor = {
                'type': transistor_dict['type'],
                'vendor': transistor_dict['manufacturer'],
                'partnumber': transistor_dict['name'],
                'ConductionLoss': {},
                'TurnOnLoss': {},
                'TurnOffLoss': {},
                'Comment': [
                    "This datasheet was created by {0} on {1} and was exported using transistordatabase.".format(
                        transistor_dict['author'], transistor_dict['datasheet_date']),
                    "Datasheet Link : {0}".format(re.sub(r'&', '&amp;', transistor_dict['datasheet_hyperlink'])),
                    "File generated : {0}".format(datetime.today()),
                    "File generated by : https://github.com/upb-lea/transistordatabase"]
            }
            if channel_recheck:
                near_to_voltages = {'v_channel_gs': v_g_on, 'v_g_on': v_g_on, 'v_g_off': v_g_off}
                v_g, v_g_on, v_g_off = self.switch.find_next_gate_voltage(req_gate_vltgs=near_to_voltages, export_type='plecs')
            plecs_transistor = get_channel_data(transistor_dict['switch']['channel'], plecs_transistor, v_g, False, is_body_diode)
            # Check if channel information exists else throw exception and don't export transistor xml data
            if 'Channel' not in plecs_transistor['ConductionLoss']:
                raise MissingDataError(1111)
            elif plecs_transistor['type'].lower() in ['mosfet', 'sic-mosfet']:
                plecs_transistor['ConductionLoss']['Channel'], plecs_transistor['ConductionLoss'][
                    'CurrentAxis'] = negate_and_append(plecs_transistor['ConductionLoss']['Channel'],
                                                       plecs_transistor['ConductionLoss']['CurrentAxis'])

            # Turn on loss information extraction
            if 1104 not in exception_codes['Switch']:
                plecs_transistor = get_loss_curves(transistor_dict['switch']['e_on'], plecs_transistor, 'TurnOnLoss', v_g_on, False)
                if 'Energy' not in plecs_transistor['TurnOnLoss']:
                    plecs_transistor['TurnOnLoss']['CurrentAxis'] = plecs_transistor['ConductionLoss']['CurrentAxis']
                    plecs_transistor['TurnOnLoss']['Energy'] = {transistor_dict['v_abs_max']: [[0] * len(
                        plecs_transistor['ConductionLoss']['CurrentAxis'])]}
                    plecs_transistor['TurnOnLoss']['TemperatureAxis'] = [25]
                else:
                    for key, _ in plecs_transistor['TurnOnLoss']['Energy'].items():
                        if not len(plecs_transistor['TurnOnLoss']['Energy'][key]) == len(
                                plecs_transistor['TurnOnLoss']['TemperatureAxis']):
                            raise MissingDataError(1102)
            else:
                plecs_transistor['TurnOnLoss']['CurrentAxis'] = plecs_transistor['ConductionLoss']['CurrentAxis']
                plecs_transistor['TurnOnLoss']['Energy'] = {transistor_dict['v_abs_max']: [[0] * len(
                    plecs_transistor['ConductionLoss']['CurrentAxis'])]}
                plecs_transistor['TurnOnLoss']['TemperatureAxis'] = [25]
            # Turn off loss information extraction
            if 1105 not in exception_codes['Switch']:
                plecs_transistor = get_loss_curves(transistor_dict['switch']['e_off'], plecs_transistor, 'TurnOffLoss', v_g_off, False)
                if 'Energy' not in plecs_transistor['TurnOffLoss']:
                    plecs_transistor['TurnOffLoss']['CurrentAxis'] = plecs_transistor['ConductionLoss']['CurrentAxis']
                    plecs_transistor['TurnOffLoss']['TemperatureAxis'] = [25]
                    plecs_transistor['TurnOffLoss']['Energy'] = {transistor_dict['v_abs_max']: [[0] * len(
                        plecs_transistor['ConductionLoss']['CurrentAxis'])]}
                else:
                    for key, _ in plecs_transistor['TurnOffLoss']['Energy'].items():
                        if not len(plecs_transistor['TurnOffLoss']['Energy'][key]) == len(
                                plecs_transistor['TurnOffLoss']['TemperatureAxis']):
                            raise MissingDataError(1103)
            else:
                plecs_transistor['TurnOffLoss']['CurrentAxis'] = plecs_transistor['ConductionLoss']['CurrentAxis']
                plecs_transistor['TurnOffLoss']['TemperatureAxis'] = [25]
                plecs_transistor['TurnOffLoss']['Energy'] = {transistor_dict['v_abs_max']: [[0] * len(
                    plecs_transistor['ConductionLoss']['CurrentAxis'])]}
            # switch forster parameter extraction either vector list of total values
            if transistor_dict['switch']['thermal_foster']['r_th_vector'] is not None:
                plecs_transistor['RElement'] = transistor_dict['switch']['thermal_foster']['r_th_vector']
                plecs_transistor['TauElement'] = transistor_dict['switch']['thermal_foster']['tau_vector']
            else:
                plecs_transistor['RElement'] = transistor_dict['switch']['thermal_foster']['r_th_total'] if \
                    transistor_dict['switch']['thermal_foster']['r_th_total'] else 1e-6,
                plecs_transistor['TauElement'] = transistor_dict['switch']['thermal_foster']['tau_total'] if \
                    transistor_dict['switch']['thermal_foster']['tau_total'] else plecs_transistor['RElement']
        except MissingDataError as e:
            logger.info(e.args[0], e.em[e.args[0]] + '.scl')
        # Gather diode data to fill in plecs template exporter
        plecs_diode = None
        try:
            if 1201 in exception_codes['Diode']:
                raise MissingDataError(1201)
            plecs_diode = {
                'type': "Diode",
                'vendor': transistor_dict['manufacturer'],
                'partnumber': transistor_dict['name'],
                'ConductionLoss': {},
                'TurnOnLoss': {},
                'TurnOffLoss': {},
                'Comment': [
                    "This datasheet was created by {0} on {1} and was exported using transistordatabase.".format(
                        transistor_dict['author'], transistor_dict['datasheet_date']),
                    "Datasheet Link : {0}".format(re.sub(r'&', '&amp;', transistor_dict['datasheet_hyperlink'])),
                    "File generated : {0}".format(datetime.today()),
                    "File generated by : https://github.com/upb-lea/transistordatabase"]
            }
            if channel_recheck:
                near_to_voltages = {'v_channel_gs': v_d_on, 'v_d_off': v_d_off}
                v_d, v_d_off = self.diode.find_next_gate_voltage(req_gate_vltgs=near_to_voltages, export_type='plecs')
            plecs_diode = get_channel_data(transistor_dict['diode']['channel'], plecs_diode, v_d, True, is_body_diode)
            if 'Channel' not in plecs_diode['ConductionLoss']:
                raise MissingDataError(1211)

            # Diode reverse recovery loss extraction
            if 1202 not in exception_codes['Diode']:
                plecs_diode = get_loss_curves(transistor_dict['diode']['e_rr'], plecs_diode, 'TurnOffLoss', v_d_off, True)
                if 'Energy' not in plecs_diode['TurnOffLoss']:
                    plecs_diode['TurnOffLoss']['CurrentAxis'] = [0]
                    plecs_diode['TurnOffLoss']['Energy'] = {0: [[0]]}
                    plecs_diode['TurnOffLoss']['TemperatureAxis'] = [25]
                else:
                    for key, _ in plecs_diode['TurnOffLoss']['Energy'].items():
                        if not len(plecs_diode['TurnOffLoss']['Energy'][key]) == len(
                                plecs_diode['TurnOffLoss']['TemperatureAxis']):
                            raise MissingDataError(
                                1203)  # Instead of throwing exception think of loading zero values as turn off losses can also be neglected
            else:
                plecs_diode['TurnOffLoss']['CurrentAxis'] = [0]
                plecs_diode['TurnOffLoss']['Energy'] = {0: [[0]]}
                plecs_diode['TurnOffLoss']['TemperatureAxis'] = [25]
            # No turn on losses for diodes are considered
            plecs_diode['TurnOnLoss']['CurrentAxis'] = [0]
            plecs_diode['TurnOnLoss']['Energy'] = {0: [[0]]}
            plecs_diode['TurnOnLoss']['TemperatureAxis'] = [25]
            # diode forster parameter extraction either vector list of total values
            if transistor_dict['diode']['thermal_foster']['r_th_vector'] is not None:
                plecs_diode['RElement'] = transistor_dict['diode']['thermal_foster']['r_th_vector']
                plecs_diode['TauElement'] = transistor_dict['diode']['thermal_foster']['tau_vector']
            else:
                plecs_diode['RElement'] = transistor_dict['diode']['thermal_foster']['r_th_total'] if \
                    transistor_dict['diode']['thermal_foster']['r_th_total'] else 1e-6,
                plecs_diode['TauElement'] = transistor_dict['diode']['thermal_foster']['tau_total'] if \
                    transistor_dict['diode']['thermal_foster']['tau_total'] else plecs_diode['RElement']
        except MissingDataError as e:
            logger.info(e.args[0], e.em[e.args[0]] + '.scl')
        return plecs_transistor if plecs_transistor is not None and 'Channel' in plecs_transistor['ConductionLoss'] \
            else None, plecs_diode if plecs_diode is not None and 'Channel' in plecs_diode['ConductionLoss'] \
            else None

    def add_dpt_measurement(self, measurement_data):
        """
        Add new measurement data to the transistor object.

        :param measurement_data: Dict of data you want to add to given attribute.
        :type measurement_data: dict
        """
        transistor_id = {'_id': self._id}

        if measurement_data['e_off_meas'] is not None:
            if isinstance(measurement_data.get('e_off_meas'), list):
                for dataset in measurement_data.get('e_off_meas'):
                    try:
                        if isvalid_dict(dataset, 'SwitchEnergyData'):
                            self.switch.e_off_meas.append(SwitchEnergyData(dataset))
                    # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                    except KeyError as error:
                        dict_list = measurement_data.get('e_off_meas')
                        if not error.args:
                            error.args = ('',)  # This syntax is necessary because error.args is a tuple
                        error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                      f"Switch-SwitchEnergyData dictionaries for e_off_meas: ",) + error.args
                        raise
            elif isvalid_dict(measurement_data.get('e_off_meas'), 'SwitchEnergyData'):
                self.switch.e_off_meas.append(SwitchEnergyData(measurement_data.get('e_off_meas')))

        if measurement_data['e_on_meas'] is not None:
            if isinstance(measurement_data.get('e_on_meas'), list):
                # Loop through list and check each dict for validity. Only create SwitchEnergyData objects from
                # valid dicts. 'None' and empty dicts are ignored.
                for dataset in measurement_data.get('e_on_meas'):
                    try:
                        if isvalid_dict(dataset, 'SwitchEnergyData'):
                            self.switch.e_on_meas.append(SwitchEnergyData(dataset))
                    # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                    except KeyError as error:
                        dict_list = measurement_data.get('e_on_meas')
                        if not error.args:
                            error.args = ('',)  # This syntax is necessary because error.args is a tuple
                        error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                      f"Switch-SwitchEnergyData dictionaries for e_on_meas: ",) + error.args
                        raise
            elif isvalid_dict(measurement_data.get('e_on_meas'), 'SwitchEnergyData'):
                # Only create SwitchEnergyData objects from valid dicts
                self.switch.e_on_meas.append(SwitchEnergyData(measurement_data.get('e_on_meas')))

        if measurement_data['raw_measurement_data'] is not None:
            if isinstance(measurement_data.get('raw_measurement_data'), list):
                # Loop through list and check each dict for validity. Only create RawMeasurementData objects from
                # valid dicts. 'None' and empty dicts are ignored.
                for dataset in measurement_data.get('raw_measurement_data'):
                    try:
                        if isvalid_dict(dataset, 'RawMeasurementData'):
                            self.raw_measurement_data.append(RawMeasurementData(dataset))
                    # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                    except KeyError as error:
                        dict_list = measurement_data.get('raw_measurement_data')
                        if not error.args:
                            error.args = ('',)  # This syntax is necessary because error.args is a tuple
                        error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] "
                                      f"in list of raw_measurement_data "f"dictionaries: ",) + error.args
                        raise
            elif isvalid_dict(measurement_data.get('raw_measurement_data'), 'RawMeasurementData'):
                # Only create RawMeasurementData objects from valid dicts
                self.raw_measurement_data.append(
                    RawMeasurementData(measurement_data.get('raw_measurement_data')))

    def add_soa_data(self, soa_data: dict | list, switch_type: str, clear: bool = False):
        """
        Add the SOA class object to the loaded transistor.switch.soa or transistor.diode.soa attribute.

        :param soa_data: argument represents the soa dictionaries objects that needs to be added to transistor switch or diode object
        :type soa_data: dict or list
        :param switch_type: either switch or diode object on which the provided soa_data needed to be appended
        :type switch_type: str
        :param clear: set to true if to clear the existing soa curves on the selected transistor switch or diode object
        :type clear: bool
        """
        soa_list = []

        if switch_type == 'switch':
            if clear:
                self.switch.soa = []
            # gathering existing data if any
            for soa_item in self.switch.soa:
                soa_list.append(soa_item.convert_to_dict())
        elif switch_type == 'diode':
            if clear:
                self.diode.soa = []
            # gathering existing data if any
            for soa_item in self.diode.soa:
                soa_list.append(soa_item.convert_to_dict())
        init_length = len(soa_list)
        # Convert 2D list ot 2D numpy array for comparison
        # TODO Does this work??
        for _, dataset in enumerate(soa_list):
            for key, _ in dataset.items():
                if isinstance(dataset[key], list):
                    dataset[key] = np.array(dataset[key])

        # validating the dict and checking for duplicates
        if isinstance(soa_data, list):
            for i, soa_data_item in enumerate(soa_data):
                try:
                    if isvalid_dict(soa_data_item, 'SOA') and check_duplicates(soa_list, soa_data_item):
                        soa_list.append(soa_data_item)
                # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                except KeyError as error:
                    if not error.args:
                        error.args = ('',)  # This syntax is necessary because error.args is a tuple
                    error.args = (f"KeyError occurred for index [{str(i)}] in list of "
                                  f"Transistor-soa dictionary: ",) + error.args
                    raise
        elif isvalid_dict(soa_data, 'SOA') and check_duplicates(soa_list, soa_data):
            soa_list.append(soa_data)

        # appending the list to the transistor object
        if len(soa_list) > init_length:
            if switch_type == 'switch':
                self.switch.soa.clear()
                for soa_item in soa_list:
                    self.switch.soa.append(SOA(soa_item))
            elif switch_type == 'diode':
                self.diode.soa.clear()
                for soa_item in soa_list:
                    self.diode.soa.append(SOA(soa_item))
            logger.info('Updated Switch.SOA successfully!')
        else:
            logger.info('No new item to add!')

    def add_gate_charge_data(self, charge_data: dict | list, clear: bool = False):
        """
        Add the GateChargeCurve class objects to the loaded transistor.switch.charge_curve attribute.

        .. note:: Transistor object must be loaded first before calling this method

        :param charge_data: argument represents the gatechargecurve dictionaries objects that needs to be added to transistor object
        :type charge_data: dict or list
        :param clear: set to true if to clear the existing gatechargecurve curves on the transistor object
        :type clear: bool
        """
        charge_list = []
        transistor_id = {'_id': self._id}
        if clear:
            self.switch.charge_curve = []
        # gathering existing data if any
        for charge_item in self.switch.charge_curve:
            charge_list.append(charge_item.convert_to_dict())

        init_length = len(charge_list)
        # Convert 2D list ot 2D numpy array for comparison
        for _, dataset in enumerate(charge_list):
            for key, _ in dataset.items():
                if isinstance(dataset[key], list):
                    dataset[key] = np.array(dataset[key])

        # validating the dict and checking for duplicates
        if isinstance(charge_data, list):
            for i, charge_data_item in enumerate(charge_data):
                try:
                    if isvalid_dict(charge_data_item, 'GateChargeCurve') and check_duplicates(charge_list, charge_data_item):
                        charge_list.append(charge_data_item)
                # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                except KeyError as error:
                    if not error.args:
                        error.args = ('',)  # This syntax is necessary because error.args is a tuple
                    error.args = (f"KeyError occurred for index [{str(i)}] in list of "
                                  f"Transistor-switch-gatecharge dictionary: ",) + error.args
                    raise
        elif isvalid_dict(charge_data, 'GateChargeCurve') and check_duplicates(charge_list, charge_data):
            charge_list.append(charge_data)

        # appending the list to the transistor object
        if len(charge_list) > init_length:
            self.switch.charge_curve.clear()
            for charge_item in charge_list:
                self.switch.charge_curve.append(GateChargeCurve(charge_item))
            logger.info('Updated Switch.Charge_Curve successfully!')
        else:
            logger.info('No new item to add!')

    def add_temp_depend_resistor_data(self, r_channel_data: dict | list, clear: bool = False):
        """
        Add the TemperatureDependResistance class objects to the loaded transistor.switch.r_channel_th attribute.

        .. note:: Transistor object must be loaded first before calling this method

        :param r_channel_data: TemperatureDependResistance dictionary object that needs to be added to transistor.switch.r_channel_th object
        :type r_channel_data: dict or list
        :param clear: set to true if to clear the existing r_channel_th curves on the transistor object
        :type clear: bool
        """
        r_channel_list = []
        transistor_id = {'_id': self._id}
        if clear:
            self.switch.r_channel_th = []
        # gathering existing data if any
        for r_channel_item in self.switch.r_channel_th:
            r_channel_list.append(r_channel_item.convert_to_dict())

        init_length = len(r_channel_list)
        # Convert 2D list ot 2D numpy array for comparison
        for _, dataset in enumerate(r_channel_list):
            for key, _ in dataset.items():
                if isinstance(dataset[key], list):
                    dataset[key] = np.array(dataset[key])

        # validating the dict and checking for duplicates
        if isinstance(r_channel_data, list):
            for index, r_channel_data_item in enumerate(r_channel_data):
                try:
                    if isvalid_dict(r_channel_data_item, 'TemperatureDependResistance') and check_duplicates(r_channel_list, r_channel_data_item):
                        r_channel_list.append(r_channel_data_item)
                # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                except KeyError as error:
                    if not error.args:
                        error.args = ('',)  # This syntax is necessary because error.args is a tuple
                    error.args = (f"KeyError occurred for index [{str(index)}] in list of "
                                  f"Transistor-switch-r_channel_th dictionary: ",) + error.args
                    raise
        elif isvalid_dict(r_channel_data, 'TemperatureDependResistance') and check_duplicates(r_channel_list, r_channel_data):
            r_channel_list.append(r_channel_data)

        # appending the list to the transistor object
        if len(r_channel_list) > init_length:
            self.switch.r_channel_th.clear()
            for r_channel_item in r_channel_list:
                self.switch.r_channel_th.append(TemperatureDependResistance(r_channel_item))
            logger.info('Updated Switch.r_channel_th successfully!')
        else:
            logger.info('No new item to add!')

    def compare_measurement_datasheet(self):
        """Compare measurements to datasheet."""
        v_g_list = []
        r_g_list = []
        t_j_list = []

        # check for measurements
        if self.switch.e_on_meas != []:
            for meas_object in self.switch.e_on_meas:
                v_g_list.append(meas_object.v_g)
                r_g_list.append(meas_object.r_g)
                t_j_list.append(meas_object.t_j)

                plt.plot(meas_object.graph_i_e[0], meas_object.graph_i_e[1],
                         label=f"Measurement: v_g = {meas_object.v_g}, r_g = {meas_object.r_g}, v_supply = {meas_object.v_supply}")

        # check for closest datasheet-data
        if self.switch.e_on != []:
            for count, v_g in enumerate(v_g_list):
                self.update_wp(t_j_list[count], v_g, self.i_cont)
                plt.plot(self.wp.e_on.graph_i_e[0], self.wp.e_on.graph_i_e[1],
                         label=f"Datasheet: v_g = {self.wp.e_on.v_g}, r_g = {self.wp.e_on.r_g}, v_supply = {self.wp.e_on.v_supply}")

        plt.xlabel('Current in A')
        plt.ylabel('Eon / J')
        plt.legend()
        plt.grid()
        plt.show()

        v_g_list = []
        r_g_list = []
        t_j_list = []

        # check for measurements
        if self.switch.e_off_meas != []:
            for meas_object in self.switch.e_off_meas:
                v_g_list.append(meas_object.v_g)
                r_g_list.append(meas_object.r_g)
                t_j_list.append(meas_object.t_j)

                plt.plot(meas_object.graph_i_e[0], meas_object.graph_i_e[1],
                         label=f"Measurement: v_g = {meas_object.v_g}, r_g = {meas_object.r_g}, v_supply = {meas_object.v_supply}")

        # check for closest datasheet-data
        if self.switch.e_off != []:
            for count, v_g in enumerate(v_g_list):
                self.update_wp(t_j_list[count], v_g, self.i_cont)
                plt.plot(self.wp.e_off.graph_i_e[0], self.wp.e_off.graph_i_e[1],
                         label=f"Datasheet: v_g = {self.wp.e_off.v_g_off}, r_g = {self.wp.e_off.r_g}, v_supply = {self.wp.e_off.v_supply}")

        plt.xlabel('Current in A')
        plt.ylabel('Eoff / J')
        plt.legend()
        plt.grid()
        plt.show()


def attach_units(trans: dict, devices: dict):
    """
    Attach units for the virtual datasheet parameters when a call is made in export_datasheet() method.

    :param trans: pdf data which contains the transistor related generic information
    :type trans: dict
    :param devices: pdf data which contains the switch type related information
    :type devices: dict

    :return: sorted data along with units to be displayed in transistor, diode, switch  section on virtual datasheet
    :rtype: dict, dict, dict
    """
    standard_list = [('Author', 'Author', None), ('Name', 'Name', None), ('Manufacturer', 'Manufacturer', None), ('Type', 'Type', None),
                     ('Datasheet_date', 'Datasheet date', None), ('Datasheet_hyperlink', 'Datasheet hyperlink', None),
                     ('Datasheet_version', 'Datasheet version', None)]
    mechthermal_list = [('Housing_area', 'Housing area', 'sq.m'), ('Housing_type', 'Housing type', 'None'), ('Cooling_area', 'Cooling area', 'sq.m'),
                        ('R_th_cs', 'R_th,cs', 'K/W'), ('R_th_total', 'R_th,total', 'K/W'), ('R_g_int', 'R_g,int', 'Ohms'), ('C_th_total', 'C_th,total', 'F'),
                        ('Tau_total', 'Tau_total', 'sec'), ('R_th_diode_cs', 'R_th,diode-cs', 'K/W'), ('R_th_switch_cs', 'R_th,switch-cs', 'K/W'),
                        ('R_g_on_recommended', 'R_g,on-recommended', 'Ohms'), ('R_g_off_recommended', 'R_g,off-recommended', 'Ohms')]
    maxratings_list = [('V_abs_max', 'V_abs,max', 'V'), ('I_abs_max', 'I_abs,max', 'A'), ('I_cont', 'I_cont', 'A'),
                       ('T_j_max', 'T_j,max', '°C'), ('T_c_max', 'T_c,max', '°C')]
    cap_list = [('C_iss_fix', 'C_iss,fix', 'F'), ('C_oss_fix', 'C_oss,fix', 'F'), ('C_rss_fix', 'C_rss,fix', 'F'),
                ('C_oss_er', 'C_oss,er', 'F'), ('C_oss_tr', 'C_oss,tr', 'F')]
    
    trans_sorted = {}
    diode_sorted = {}
    switch_sorted = {}
    if ('raw_measurement_data') in trans.keys():
        raw_measurements_test_conditions = [('T_j_°C', 'T,j', '°C'), ('V_supply_V', 'V,supply', 'V'), ('V_gate_V', 'V,gate', 'V'),
                                            ('V_gate_off_V', 'V,gate,off', 'V'), ('R_g_Ohms', 'R,g', 'Ohms'), ('R_g_off_Ohms', 'R,g,off', 'Ohms'),
                                            ('L_load_uH', 'L,load', 'uH'), ('L_commutation_uH', 'L,commutation', 'uH')]
        for list_unit in [maxratings_list, standard_list, mechthermal_list, cap_list, raw_measurements_test_conditions]:
            for tuple_unit in list_unit:
                try:
                    trans_sorted.update({tuple_unit[1]: [trans.pop(tuple_unit[0]), tuple_unit[2]]})
                except KeyError:
                    pass
    else:
        for list_unit in [maxratings_list, standard_list, mechthermal_list, cap_list]:
            for tuple_unit in list_unit:
                try:
                    trans_sorted.update({tuple_unit[1]: [trans.pop(tuple_unit[0]), tuple_unit[2]]})
                except KeyError:
                    pass

    if len(trans.keys()) > 0:
        trans_sorted.update(trans)

    for list_unit in [mechthermal_list, maxratings_list]:
        for tuple_unit in list_unit:
            try:
                switch_sorted.update({tuple_unit[1]: [devices['switch'].pop(tuple_unit[0]), tuple_unit[2]]})
            except KeyError:
                pass
            try:
                diode_sorted.update({tuple_unit[1]: [devices['diode'].pop(tuple_unit[0]), tuple_unit[2]]})
            except KeyError:
                pass
    if len(devices['diode'].keys()) > 0:
        diode_sorted.update(devices['diode'])
    if len(devices['switch'].keys()) > 0:
        switch_sorted.update(devices['switch'])

    return trans_sorted, diode_sorted, switch_sorted
