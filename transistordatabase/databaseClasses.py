from __future__ import annotations
import datetime
import xml.etree.ElementTree as et
import numpy as np
import numpy.typing as npt
import re
import os
from typing import List, Union, Optional
from matplotlib import pyplot as plt
from bson.objectid import ObjectId
from bson import json_util
from scipy import integrate
from scipy.spatial import distance
from scipy.optimize import curve_fit
from pymongo import MongoClient
from pymongo import errors
import json
import git
import shutil
import stat
import scipy.io as sio
import collections
from jinja2 import Environment, FileSystemLoader
import base64
import io
import pathlib
import warnings
from PyQt5 import QtWidgets, QtWebEngineWidgets
import sys
from .constants import *
import glob


class Transistor:
    """
    Transistor object which is the core class of transistordatabase module. Contains subclasses like Switch, Diode, FosterThermalModel etc, and other child classes
    using which all the features and functionalities of this module are based and developed.

    .. todo::
        - Groups data of all other classes for a single transistor. Methods are specified in such a way that only user-interaction with this class is necessary
        - Documentation on how to add or extract a transistor-object to/from the database can be found in
    """
    # ToDo: Add database _id as attribute
    _id: ObjectId  #: ID of the object being created. (Automatic key)
    name: str  #: Name of the transistor. Choose as specific as possible. (Mandatory key)
    type: str  #: Specifies the type of module either e.g IGBT, MOSFET, SiC MOSFET etc. (Mandatory key)
    # User-specific data
    author: str  #: The author of the module specific object. Usually added when creating and adding a new datasheet module using template.py. (Mandatory key)
    comment: Optional[str]  #: Any user specific comment created when adding a new datasheet module. (Optional key)
    # Date and template data. Should not be changed manually
    # ToDo: Add methods to automatically determine dates and template_version on construction or update.
    template_version: str  #: Specifies the template version using which a new datasheet module is created. (Mandatory/Automatic)
    template_date: "datetime.datetime"  #: Specifies the date and time at which the template in created. (Mandatory/Automatic)
    creation_date: "datetime.datetime"  #: Specifies the date and time of the new transistor module that is created using template. (Mandatory/Automatic)
    # Manufacturer- and part-specific data
    manufacturer: str  #: Provides information of the module manufacturer. (Mandatory key)
    datasheet_hyperlink: Optional[str]  #: As the name specifies, provides the hyperlink of the datasheet that is being referred to. Should be a valid link if specified(Optional)
    datasheet_date: Optional["datetime.datetime"]  #: pymongo cannot encode date => always save as datetime. (Optional key)
    datasheet_version: Optional[str]  #: Specifies the version of the module manufacturer datasheet. (Optional key)
    housing_area: float  #: Housing area extracted from datasheet. Units in m^2. (Mandatory key)
    cooling_area: float  #: Housing area extracted from datasheet. Units in m^2. (Mandatory key)
    housing_type: str  #: e.g. TO-220, etc. Must be from a list of specific strings. (Mandatory key)
    # These are documented in their respective class definitions
    switch: "Switch"  #: Member instance for class type Switch (Mandatory key)
    diode: "Diode"  #: Member instance for class type Diode (Mandatory key)
    # Recommended gate resistors
    r_g_on_recommended: Optional[float]  #: Recommended turn on gate resistance of switch (Optional key)
    r_g_off_recommended: Optional[float]  #: Recommended turn off gate resistance of switch (Optional key)
    raw_measurement_data: Optional[List["RawMeasurementData"]]  #: Member instance for class type RawMeasurementData
    # Thermal data. See git for equivalent thermal_foster circuit diagram.
    r_th_cs: Optional[float]  #: Module specific case to sink thermal resistance.  Units in K/W  (Optional key)
    r_th_switch_cs: Optional[float]  #: Switch specific case to sink thermal resistance. Units in K/W  (Optional key)
    r_th_diode_cs: Optional[float]  #: Diode specific case to sink thermal resistance. Units in K/W  (Optional key)
    # Absolute maximum ratings
    v_abs_max: float  #: Absolute maximum voltage rating. Units in V  (Mandatory key)
    i_abs_max: float  #: Absolute maximum current rating. Units in A  (Mandatory key)
    # Time and Energy related capacitance
    c_oss_er: Optional[EffectiveOutputCapacitance]  #: Energy related effective output capacitance. Units in F (Optional key)
    c_oss_tr: Optional[EffectiveOutputCapacitance]  #: Time related effective output capacitance. Units in F (Optional key)
    # Constant capacities
    c_oss_fix: Optional[float]  #: Parasitic constant capacitance. Units in F  (Optional key)
    c_iss_fix: Optional[float]  #: Parasitic constant capacitance. Units in F  (Optional key)
    c_rss_fix: Optional[float]  #: Parasitic constant capacitance. Units in F  (Optional key)
    # Voltage dependent capacities
    c_oss: Optional[List["VoltageDependentCapacitance"]]  #: List of VoltageDependentCapacitance. (Optional key)
    c_iss: Optional[List["VoltageDependentCapacitance"]]  #: List of VoltageDependentCapacitance. (Optional key)
    c_rss: Optional[List["VoltageDependentCapacitance"]]  #: List of VoltageDependentCapacitance. (Optional key)
    # Energy stored in c_oss
    graph_v_ecoss: Optional[npt.NDArray[np.float64]]  #: Member instance for storing the voltage dependant capacitance graph in the form of 2D numpy array. Units of Row 1 = V; Row 2 = J  (Optional key)
    # Rated operation region
    i_cont: Optional[float]  #: Module specific continuous current. Units in  A e.g. Fuji = I_c, Semikron = I_c,nom (Mandatory key)
    t_c_max: float  #: Module specific maximum junction temperature. Units in °C (Optional key)
    r_g_int: float  #: Internal gate resistance. Units in Ohm (Mandatory key)

    def __init__(self, transistor_args: dict, switch_args: dict, diode_args: dict) -> None:
        """
        Takes in the following dictionary arguments for creating and initializing the transistor object. isvalid_dict() method is applied on transistor_args object
        to validate the argument. Else TypeError exception is raised. Module manufacturer type and housing type data validations are performed for matching the given
        values to the pre-existed types stored in the form of 'housing.txt' and 'module_manufacturer.txt' files.

        :param transistor_args: transistor argument object
        :type transistor_args: dict
        :param switch_args: switch argument object
        :type switch_args: dict
        :param diode_args: diode argument object
        :type diode_args: dict

        :raises TypeError: Raised if isvalid_dict() return false
        :raises ValueError: Raised if index based search for module_manufacturer or housing_type values fails
        """
        try:
            if self.isvalid_dict(transistor_args, 'Transistor'):
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
                # ToDo: This is a little ugly because the file "housing_types.txt" has to be opened twice.
                # Import list of valid housing types from "housing_types.txt"
                # add housing types to the working direction
                housing_types_file = os.path.join(os.path.dirname(__file__), 'housing_types.txt')
                with open(housing_types_file, "r") as housing_types_txt:
                    housing_types = [line.replace("\n", "") for line in housing_types_txt.readlines() if not line.startswith("#")]
                # Remove all non alphanumeric characters from housing_type names and convert to lowercase for comparison
                alphanum_housing_types = [re.sub("[^A-Za-z0-9]+", "", line).lstrip().lower() for line in housing_types]
                housing_type = transistor_args.get('housing_type')
                # Get index where the housing_type was found in "housing_types.txt"
                idx = alphanum_housing_types.index(re.sub("[^A-Za-z0-9]+", "", housing_type).lstrip().lower())
                # Don't use the name in transistor_args but the matching name in "housing_types.txt"
                self.housing_type = housing_types[idx]

                # Import list of valid module manufacturers from "module_manufacturers.txt"
                # add manufacturer names to the working direction
                module_owner_file = os.path.join(os.path.dirname(__file__), 'module_manufacturers.txt')
                with open(module_owner_file, "r") as module_owner_txt:
                    module_owners = [line.replace("\n", "") for line in module_owner_txt.readlines() if
                                     not line.startswith("#")]
                # Remove all non alphanumeric characters from housing_type names and convert to lowercase for comparison
                alphanum_module_owners = [re.sub("[^A-Za-z]+", "", line).lstrip().lower() for line in module_owners]
                module_owner = transistor_args.get('manufacturer')
                # Get index where the module_manufacturer was found in "module_manufacturers.txt"
                idx = alphanum_module_owners.index(re.sub("[^A-Za-z]+", "", module_owner).lstrip().lower())
                # Don't use the name in transistor_args but the matching name in "module_manufacturers.txt"
                self.manufacturer = module_owners[idx]

                self.r_th_cs = transistor_args.get('r_th_cs')
                self.r_th_switch_cs = transistor_args.get('r_th_switch_cs')
                self.r_th_diode_cs = transistor_args.get('r_th_diode_cs')
                self.v_abs_max = transistor_args.get('v_abs_max')
                self.i_abs_max = transistor_args.get('i_abs_max')
                self.i_cont = transistor_args.get('i_cont')
                self.c_oss = []  # Default case: Empty list
                if isinstance(transistor_args.get('c_oss'), list):
                    # Loop through list and check each dict for validity. Only create VoltageDependentCapacitance objects from
                    # valid dicts. 'None' and empty dicts are ignored.
                    for dataset in transistor_args.get('c_oss'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'VoltageDependentCapacitance'):
                                self.c_oss.append(Transistor.VoltageDependentCapacitance(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = transistor_args.get('c_oss')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of c_oss "
                                          f"dictionaries: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(transistor_args.get('c_oss'), 'VoltageDependentCapacitance'):
                    # Only create VoltageDependentCapacitance objects from valid dicts
                    self.c_oss.append(Transistor.VoltageDependentCapacitance(transistor_args.get('c_oss')))

                self.c_iss = []  # Default case: Empty list
                if isinstance(transistor_args.get('c_iss'), list):
                    # Loop through list and check each dict for validity. Only create VoltageDependentCapacitance objects from
                    # valid dicts. 'None' and empty dicts are ignored.
                    for dataset in transistor_args.get('c_iss'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'VoltageDependentCapacitance'):
                                self.c_iss.append(Transistor.VoltageDependentCapacitance(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = transistor_args.get('c_iss')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of c_iss "
                                          f"dictionaries: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(transistor_args.get('c_iss'), 'VoltageDependentCapacitance'):
                    # Only create VoltageDependentCapacitance objects from valid dicts
                    self.c_iss.append(Transistor.VoltageDependentCapacitance(transistor_args.get('c_iss')))

                self.c_rss = []  # Default case: Empty list
                if isinstance(transistor_args.get('c_rss'), list):
                    # Loop through list and check each dict for validity. Only create VoltageDependentCapacitance objects from
                    # valid dicts. 'None' and empty dicts are ignored.
                    for dataset in transistor_args.get('c_rss'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'VoltageDependentCapacitance'):
                                self.c_rss.append(Transistor.VoltageDependentCapacitance(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = transistor_args.get('c_rss')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of c_rss "
                                          f"dictionaries: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(transistor_args.get('c_rss'), 'VoltageDependentCapacitance'):
                    # Only create VoltageDependentCapacitance objects from valid dicts
                    self.c_rss.append(Transistor.VoltageDependentCapacitance(transistor_args.get('c_rss')))
                self.graph_v_ecoss = transistor_args.get('graph_v_ecoss')

                self.raw_measurement_data = []
                if isinstance(transistor_args.get('raw_measurement_data'), list):
                    # Loop through list and check each dict for validity. Only create RawMeasurementData objects from
                    # valid dicts. 'None' and empty dicts are ignored.
                    for dataset in transistor_args.get('raw_measurement_data'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'RawMeasurementData'):
                                self.raw_measurement_data.append(Transistor.RawMeasurementData(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = transistor_args.get('raw_measurement_data')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] "
                                          f"in list of raw_measurement_data "f"dictionaries: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(transistor_args.get('raw_measurement_data'), 'RawMeasurementData'):
                    # Only create RawMeasurementData objects from valid dicts
                    self.raw_measurement_data.append(Transistor.RawMeasurementData(transistor_args.get('raw_measurement_data')))

                self.c_oss_er = None
                if Transistor.isvalid_dict(transistor_args.get('c_oss_er'), 'EffectiveOutputCapacitance'):
                    # Only create EffectiveOutputCapacitance objects from valid dicts
                    self.c_oss_er = Transistor.EffectiveOutputCapacitance(transistor_args.get('c_oss_er'))

                self.c_oss_tr = None
                if Transistor.isvalid_dict(transistor_args.get('c_oss_tr'), 'EffectiveOutputCapacitance'):
                    # Only create EffectiveOutputCapacitance objects from valid dicts
                    self.c_oss_tr = Transistor.EffectiveOutputCapacitance(transistor_args.get('c_oss_tr'))
            else:
                # ToDo: Is this a value or a type error?
                # ToDo: Move these raises to isvalid_dict() by checking dict_type for 'None' or empty dicts?
                # ToDo: Use info in isvalid_dict() to print the list of mandatory values automatically
                raise TypeError("Dictionary 'transistor_args' is empty or 'None'. This is not allowed since following keys"
                                "are mandatory: 'name', 'type', 'author', 'manufacturer', 'housing_area', "
                                "'cooling_area', 'housing_type', 'v_abs_max', 'i_abs_max', 'i_cont'")
            self.diode = self.Diode(diode_args)
            self.switch = self.Switch(switch_args)
            self.calc_thermal_params(input_type='switch')
            self.calc_thermal_params(input_type='diode')
            self.wp = self.WP()
        except Exception as e:
            print('Exception occurred: Selected datasheet or module could not be created or loaded\n' + str(e))
            raise

    def __eq__(self, other) -> bool:
        """
        This method checks if the passed transistor object and the transistor object in scope are both same by matching their object id's

        :param other: Expects transistor object
        :return: True or False
        :rtype: bool
        """
        if not isinstance(other, Transistor):
            # don't attempt to compare against unrelated types
            return NotImplemented
        my_dict = self.convert_to_dict()
        my_dict.pop('_id', None)
        other_dict = other.convert_to_dict()
        other_dict.pop('_id', None)
        return my_dict == other_dict

    def save(self, collection: str = "local", overwrite: bool = None) -> None:
        """
        The method save the transistor object to local mongodb database.
        Currently receives the execution instructions from update_from_fileexchange(..)

        :param collection: By default local database is selected and "local" is provided as value
        :type collection: str
        :param overwrite: Indicates whether to overwrite the existing transistor object in the local database if a match is found
        :type overwrite: bool or None

        :return: None
        :rtype: None
        """
        if collection == "local":
            collection = connect_local_TDB()
        transistor_dict = self.convert_to_dict()
        if transistor_dict.get("_id") is not None:
            _id = transistor_dict["_id"]
            if collection.find_one({"_id": _id}) is not None:
                if not isinstance(overwrite, bool):
                    raise errors.DuplicateKeyError(
                        "A transistor object with {0} is already present in the TDB. Please specify,"
                        " whether the newly saved Transistor should replace the old one or whether it should be saved as a copy. "
                        "This can be done by setting the optional argument 'overwrite' to either True or False.".format(_id))
                if not overwrite:
                    del transistor_dict["_id"]
                    collection.insert_one(transistor_dict)
                if overwrite:
                    collection.replace_one({"_id": _id}, transistor_dict)
            else:
                collection.insert_one(transistor_dict)
        else:
            collection.insert_one(transistor_dict)

    def export_json(self, path: str = None) -> None:
        """
        Exports the transistor object to .json file, e.g. to share this file on file exchange on github

        :param path: path to export
        :type path: str or None (default)

        :raises TypeError: Raised if the provided path is not a string type
        """
        transistor_dict = self.convert_to_dict()
        try:
            save_path = pathlib.Path(path)
        except:
            if path is None:
                save_path = pathlib.Path.cwd()
                with open(save_path.joinpath(transistor_dict['name'] + '.json'), 'w') as fp:
                    json.dump(transistor_dict, fp, default=json_util.default)
                print(f"Saved json-file {transistor_dict['name'] + '.json'} to {save_path.as_uri()}")
            else:
                raise TypeError("path = {0} ist not a string.".format(path))
        else:
            if path is None:
                save_path = pathlib.Path.cwd()
            with open(save_path.joinpath(transistor_dict['name'] + '.json'), 'w') as fp:
                json.dump(transistor_dict, fp, default=json_util.default)
            print(f"Saved json-file {transistor_dict['name'] + '.json'} to {save_path.as_uri()}")

    def convert_to_dict(self) -> dict:
        """
        Converts the transistor object in scope to a dictionary datatype

        :return: Transistor object in dict type
        :rtype: dict
        """
        d = dict(vars(self))
        d.pop('wp', None)  # remove wp from converting. wp will not be stored to .json files
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

    @staticmethod
    def isvalid_dict(dataset_dict: dict, dict_type: str) -> bool:
        """
        This method checks input argument dictionaries for their validity. It is checked whether all mandatory keys
        are present, have the right type and permitted values (e.g. 'MOSFET' or 'IGBT' or 'SiC-MOSFET' for 'type').
        Returns 'False' if dictionary is 'None' or Empty. These cases should be handled outside this method.
        Raises appropriate errors if dictionary invalid in other ways.

        :param dataset_dict: Dataset of type dict
        :param dict_type: Could be Transistor/SwitchEnergyData/FosterThermalModel/Diode_ChannelData etc. as specified in the internally provided list.

        :raises TypeError: Raised when the instance or dictionary values are not of expected type
        :raises ValueError: Raised when the certain dict values like housing type, module manufacturer values are not the expected values
        :raises KeyError: Raised when mandatory keys are not available in dataset_dict

        :return: True in case of valid dict, 'False' if dictionary is 'None' or Empty
        :rtype: bool

        .. todo:: Error if given key is not used?
        """

        supported_types = ['MOSFET', 'IGBT', 'SiC-MOSFET', 'GaN-Transistor']
        instructions = {
            'Transistor': {
                'mandatory_keys': {'name', 'type', 'author', 'manufacturer', 'housing_area', 'cooling_area',
                                   'housing_type', 'v_abs_max', 'i_abs_max', 'i_cont', 'r_g_int', 'r_th_cs',
                                   'r_th_switch_cs', 'r_th_diode_cs'},
                'str_keys': {'name', 'type', 'author', 'manufacturer', 'housing_type', 'comment', 'datasheet_hyperlink',
                             'datasheet_version'},
                'numeric_keys': {'housing_area', 'cooling_area', 'v_abs_max', 'i_abs_max', 'i_cont', 't_c_max',
                                 'r_g_int', 'c_oss_fix', 'c_iss_fix', 'c_rss_fix', 'r_th_cs', 'r_th_switch_cs',
                                 'r_th_diode_cs', 't_c_max', 'r_g_on_recommended', 'r_g_off_recommended'},
                'array_keys': {'graph_v_ecoss'}},
            'Switch': {
                'mandatory_keys': {'t_j_max'},
                'str_keys': {'comment', 'manufacturer', 'technology'},
                'numeric_keys': {'t_j_max'},
                'array_keys': {}},
            'Diode': {
                'mandatory_keys': {'t_j_max'},
                'str_keys': {'comment', 'manufacturer', 'technology'},
                'numeric_keys': {'t_j_max'},
                'array_keys': {}},
            'Switch_LinearizedModel': {
                'mandatory_keys': {'t_j', 'v_g', 'i_channel', 'r_channel', 'v0_channel'},
                'str_keys': {},
                'numeric_keys': {'t_j', 'v_g', 'i_channel', 'r_channel', 'v0_channel'},
                'array_keys': {}},
            'Diode_LinearizedModel': {
                'mandatory_keys': {'t_j', 'v_g', 'i_channel', 'r_channel'},
                'str_keys': {},
                'numeric_keys': {'t_j', 'v_g', 'i_channel', 'r_channel', 'v0_channel'},
                'array_keys': {}},
            'Diode_ChannelData': {
                'mandatory_keys': {'t_j', 'graph_v_i'},
                'numeric_keys': {'t_j', 'v_g'},
                'str_keys': {},
                'array_keys': {'graph_v_i'}},
            'Switch_ChannelData': {
                'mandatory_keys': {'t_j', 'graph_v_i', 'v_g'},
                'numeric_keys': {'t_j', 'v_g'},
                'str_keys': {},
                'array_keys': {'graph_v_i'}},
            'SwitchEnergyData_single': {
                'mandatory_keys': {'t_j', 'v_supply', 'v_g', 'e_x', 'r_g', 'i_x'},
                'str_keys': {},
                'numeric_keys': {'t_j', 'v_supply', 'v_g', 'e_x', 'r_g', 'i_x'},
                'array_keys': {}},
            'SwitchEnergyData_graph_r_e': {
                'mandatory_keys': {'t_j', 'v_supply', 'v_g', 'graph_r_e', 'i_x'},
                'str_keys': {},
                'numeric_keys': {'t_j', 'v_supply', 'v_g', 'i_x'},
                'array_keys': {'graph_r_e'}},
            'SwitchEnergyData_graph_i_e': {
                'mandatory_keys': {'t_j', 'v_supply', 'v_g', 'graph_i_e', 'r_g'},
                'str_keys': {},
                'numeric_keys': {'t_j', 'v_supply', 'v_g', 'r_g'},
                'array_keys': {'graph_i_e'}},
            'VoltageDependentCapacitance': {
                'mandatory_keys': {'t_j', 'graph_v_c'},
                'str_keys': {},
                'numeric_keys': {'t_j'},
                'array_keys': {'graph_v_c'}},
            'FosterThermalModel': {
                'mandatory_keys': {'r_th_total'},
                'str_keys': {},
                'numeric_keys': {'r_th_total', 'c_th_total', 'tau_total'},
                'array_keys': {'graph_t_rthjc'}},
            'RawMeasurementData': {
                'mandatory_keys': {'dataset_type'},
                'str_keys': {},
                'numeric_keys': {},
                'array_keys': {}},
            'EffectiveOutputCapacitance': {
                'mandatory_keys': {'c_o', 'v_gs', 'v_ds'},
                'str_keys': {},
                'numeric_keys': {'c_o', 'v_gs', 'v_ds'},
                'array_keys': {}},
            'TemperatureDependResistance': {
                'mandatory_keys': {'i_channel', 'v_g', 'dataset_type', 'graph_t_r'},
                'str_keys': {'dataset_type'},
                'numeric_keys': {'i_channel', 'v_g', 'r_channel_nominal'},
                'array_keys': {'graph_t_r'}},
            'GateChargeCurve': {
                'mandatory_keys': {'i_channel', 't_j', 'v_supply', 'graph_q_v'},
                'str_keys': {},
                'numeric_keys': {'i_channel', 't_j', 'v_supply', 'i_g'},
                'array_keys': {'graph_q_v'}},
            'SOA': {
                'mandatory_keys': {'graph_i_v'},
                'str_keys': {},
                'numeric_keys': {'t_c', 'time_pulse'},
                'array_keys': {'graph_i_v'}}

        }
        if dataset_dict is None or not bool(dataset_dict):  # "bool(dataset_dict) = False" represents empty dictionary
            return False  # Empty dataset. Can be valid depending on circumstances, hence no error.
        if not isinstance(dataset_dict, dict):
            raise TypeError(f"Expected dictionary with {str(dict_type)} arguments but got {str(type(dataset_dict))} "
                            f"instead.")

        if dict_type == 'Transistor':
            if dataset_dict.get("_id") is not None:
                _id = dataset_dict["_id"]
                if not isinstance(_id, ObjectId):
                    raise TypeError(f"{_id} is not a valid ObjectId.")

            if dataset_dict.get('type') not in supported_types:
                raise ValueError(f"Transistor type currently not supported. 'type' must be in "
                                 f"{supported_types}")
            text_file_dict = {'manufacturer': 'module_manufacturers.txt', 'housing_type': 'housing_types.txt'}
            for key, filename in text_file_dict.items():
                file = os.path.join(os.path.dirname(__file__), filename)
                with open(file, "r") as file_txt:
                    read_list = [line.replace("\n", "") for line in file_txt.readlines() if not line.startswith("#")]
                    # Remove all non alphanumeric characters from housing_type and manufacturer names and
                    # convert to lowercase for comparison
                    snub = "[^A-Za-z0-9]+" if key == 'housing_type' else "[^A-Za-z]+"
                    alphanum_values = [re.sub(snub, "", line).lstrip().lower() for line in read_list]
                    dataset_value = dataset_dict.get(key)
                    if re.sub(snub, "", dataset_value).lstrip().lower() not in alphanum_values:
                        name = key.capitalize().replace("_", " ")
                        if name == 'Housing type':
                            housing_file_path = pathlib.Path(os.path.join(os.path.dirname(__file__), 'housing_types.txt')).as_uri()
                            raise ValueError('{} {} is not allowed. The supported {}s are\n {} \n See file {} for a list of supported housing types.'.format(name, dataset_value, name, alphanum_values,
                                                                                                                                                             housing_file_path))
                        elif name == 'Manufacturer':
                            module_file_path = pathlib.Path(os.path.join(os.path.dirname(__file__), 'module_manufacturers.txt')).as_uri()
                            raise ValueError(
                                '{} {} is not allowed. The supported {}s are\n {} \n See file {} for a list of supported module manufacturers.'.format(name, dataset_value, name, alphanum_values,
                                                                                                                                                       module_file_path))

        if dict_type == 'SwitchEnergyData':
            if dataset_dict.get('dataset_type') not in ['single', 'graph_r_e', 'graph_i_e']:
                raise KeyError("Dictionary does not contain 'dataset_type' key necessary for SwitchEnergyData object "
                               "creation. 'dataset_type' must be 'single', 'graph_r_e' or 'graph_i_e'. "
                               "Check SwitchEnergyData class for further information.")
            if dataset_dict['dataset_type'] == 'single':
                dict_type = 'SwitchEnergyData_single'
            if dataset_dict['dataset_type'] == 'graph_r_e':
                dict_type = 'SwitchEnergyData_graph_r_e'
            if dataset_dict['dataset_type'] == 'graph_i_e':
                dict_type = 'SwitchEnergyData_graph_i_e'

        if dict_type == 'FosterThermalModel':
            given_parameters = [p for p in ['r_th_vector', 'c_th_vector', 'tau_vector']
                                if dataset_dict.get(p) is not None]
            if len(given_parameters) != 0:
                for p in given_parameters:
                    if not isinstance(dataset_dict[p], list):
                        dataset_dict[p] = [dataset_dict[p]]
                list_sizes = [len(dataset_dict[p]) for p in given_parameters]
                if not list_sizes.count(list_sizes[0]) == len(list_sizes):
                    raise TypeError("The lists 'r_th_vector', 'c_th_vector', 'tau_vector' (if given) must be the same "
                                    "length.")
                bool_list_numeric = all([all([check_realnum(single_value)
                                              for single_value in dataset_dict.get(p)])
                                         for p in given_parameters])
            if len(given_parameters) == 1:
                raise ValueError(f"Only 1 value out of {['r_th_vector', 'c_th_vector', 'tau_vector']} is given."
                                 f"Either specify 2, 3 (fitting) or none of these.")
            # ToDo: Add check, if all 3 are given whether they fit to each other?

        if dict_type == 'Diode_ChannelData' or dict_type == 'Switch_ChannelData':
            for axis in dataset_dict.get('graph_v_i'):
                if any(x < 0 for x in axis):
                    raise ValueError(" Negative values are not allowed, please include mirror_xy_data attribute")

        if dict_type == 'TemperatureDependResistance':
            if dataset_dict.get('dataset_type') == 't_factor':
                instructions[dict_type]['mandatory_keys'].add('r_channel_nominal')

        if dict_type not in instructions:
            raise KeyError(f"No instructions available for validity check of argument dictionary with dict_type "
                           f"{dict_type}.")
        mandatory_keys = instructions[dict_type]['mandatory_keys']
        str_keys = instructions[dict_type]['str_keys']
        numeric_keys = instructions[dict_type]['numeric_keys']
        array_keys = instructions[dict_type]['array_keys']

        # Check if all mandatory keys are contained in the dict and none of the mandatory values is 'None'.
        if any([dataset_dict.get(mandatory_key) is None for mandatory_key in mandatory_keys]):
            raise KeyError(f"Argument dictionary does not contain all keys necessary for {dict_type} object creation. "
                           f"Mandatory keys: {mandatory_keys}")
        # Check if all values have appropriate types.
        if all([check_realnum(dataset_dict.get(numeric_key)) for numeric_key in numeric_keys]) and \
                all([check_str(dataset_dict.get(str_key)) for str_key in str_keys]) and \
                all([check_2d_dataset(dataset_dict.get(array_key)) for array_key in array_keys]):
            return True

    def update_wp(self, t_j: float, v_g: float, i_channel: float, switch_or_diode: str = "both", normalize_t_to_v=10) -> None:
        """
        Fills the .wp-class, a temporary storage for self-written user-programs
        Searches for the input values and fills the .wp-class with data next to this points

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
        :return: None
        :rtype: None
        """
        if switch_or_diode in ["diode", "both"]:
            diode_channel, self.wp.e_rr = self.diode.find_approx_wp(t_j, v_g, normalize_t_to_v)
            if self.wp.e_rr is None:
                print("run diode.find_approx_wp: closest working point for t_j = {0} °C and {1} V:".format(t_j, v_g))
                print("There is no err, may due to MOSFET, SiC-MOSFET or GaN device: Set err to [[0, 0], [0, 0]]")
                print("Note: Values are set to t_j = 25°C, v_g = 15V, r_g = 1 Ohm")
                args = {"dataset_type": "graph_i_e",
                        "t_j": 25,
                        'v_g': 15,
                        'v_supply': 1,
                        'r_g': 1,
                        "graph_i_e": [np.array([[0, 0], [0, 0]]), np.array([[0, 0], [0, 0]])]}
                self.wp.e_rr = self.SwitchEnergyData(args)
            # ToDo: This could be handled more nicely by implementing another method for Diode and Channel class so the
            #  object can "linearize itself".
            self.wp.diode_v_channel, self.wp.diode_r_channel = \
                self.calc_lin_channel(diode_channel.t_j, diode_channel.v_g, i_channel, switch_or_diode="diode")

        if switch_or_diode in ["switch", "both"]:
            switch_channel, self.wp.e_on, self.wp.e_off = self.switch.find_approx_wp(t_j, v_g, normalize_t_to_v)
            # ToDo: This could be handled more nicely by implementing another method for Diode and Channel class so the
            #  object can "linearize itself".
            self.wp.switch_v_channel, self.wp.switch_r_channel = \
                self.calc_lin_channel(switch_channel.t_j, switch_channel.v_g, i_channel, switch_or_diode="switch")

    def quickstart_wp(self) -> None:
        """
        Function to fill out the .wp-class by just one command 'quickstart_wp()'.
        Uses typical working points

         - channel linearization next to v_g = 15V, i_cont and t_j = t_j_abs_max - 25 degree
         - switching loss curves next to t_j = t_j_abs_max - 25 degree

        :return: None
        """
        # ToDo: may separate data for IGBT, MOSFET, SiC-MOSFET and GaN-Transistor
        self.update_wp(self.switch.t_j_max - 25, 15, self.i_cont)

    def calc_v_eoss(self) -> np.array:
        """
        Calculates e_oss stored in c_oss depend on the voltage. Uses transistor.c_oss[0].graph_v_coss

        :return: e_oss numpy array
        :rtype: np.array
        """
        # energy_cumtrapz = np.zeros_like(self.c_oss[0].graph_v_c[1], dtype=np.float32)
        energy_cumtrapz = integrate.cumulative_trapezoid(self.c_oss[0].graph_v_c[0] * self.c_oss[0].graph_v_c[1],
                                                         self.c_oss[0].graph_v_c[0], initial=0)
        return np.array([self.c_oss[0].graph_v_c[0], energy_cumtrapz])

    def calc_v_qoss(self) -> np.array:
        """
        Calculates q_oss stored in c_oss depend on the voltage. Uses transistor.c_oss[0].graph_v_coss

        :return: q_oss numpy array
        :rtype: np.array
        """
        charge_cumtrapz = integrate.cumulative_trapezoid(self.c_oss[0].graph_v_c[1], self.c_oss[0].graph_v_c[0],
                                                         initial=0)

        return np.array([self.c_oss[0].graph_v_c[0], charge_cumtrapz])

    def plot_v_eoss(self, buffer_req: bool = False):
        """
        Plots v_eoss with method calc_v_eoss

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
        Plots v_qoss with method calc_v_qoss

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

    def get_object_v_i(self, switch_or_diode: str, t_j: float, v_g: float) -> list:
        """
        Used for getting a channel curve including boundary conditions

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
                print("Available operating points: (t_j, v_g)")
                print(available_datasets)
                raise ValueError("No data available for linearization at the given operating point. "
                                 "A list of available operating points is printed above.")
            elif len(candidate_datasets) > 1:
                print("Multiple datasets were found that are consistent with the chosen "
                      "operating point. The first of these sets is automatically chosen because selection of a "
                      "different dataset is not yet implemented.")
            dataset = candidate_datasets[0]

        elif switch_or_diode == 'diode':
            if self.type in ['SiC-MOSFET', 'GaN-Transistor']:
                candidate_datasets = [channel for channel in self.diode.channel if
                                      (channel.t_j == t_j and channel.v_g == v_g)]
                if len(candidate_datasets) == 0:
                    available_datasets = [(channel.t_j, channel.v_g) for channel in self.diode.channel]
                    print("Available operating points: (t_j, v_g)")
                    print(available_datasets)
                    raise ValueError("No data available for linearization at the given operating point. "
                                     "A list of available operating points is printed above.")
                elif len(candidate_datasets) > 1:
                    print("Multiple datasets were found that are consistent with the chosen "
                          "operating point. The first of these sets is automatically chosen because selection of a "
                          "different dataset is not yet implemented.")
                dataset = candidate_datasets[0]
            else:
                candidate_datasets = [channel for channel in self.diode.channel
                                      if channel.t_j == t_j]
                if len(candidate_datasets) == 0:
                    available_datasets = [channel.t_j for channel in self.diode.channel]
                    print("Available operating points: (t_j)")
                    print(available_datasets)
                    raise ValueError("No data available for linearization at the given operating point. "
                                     "A list of available operating points is printed above.")
                elif len(candidate_datasets) > 1:
                    print("Multiple datasets were found that are consistent with the chosen "
                          "operating point. The first of these sets is automatically chosen because selection of a "
                          "different dataset is not yet implemented.")
                dataset = candidate_datasets[0]

        return dataset

    def get_object_i_e(self, e_on_off_rr: str, t_j: float, v_g: float, v_supply: float, r_g: float) -> list:
        """
        Function to get the loss graphs out of the transistor class

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
                print("Available operating points: (t_j, v_g, v_supply, r_g)")
                print(available_datasets)
                raise ValueError("No data available for get_graph_i_e at the given operating point. "
                                 "A list of available operating points is printed above.")
            elif len(candidate_datasets) > 1:
                print("multiple datasets were found that are consistent with the chosen "
                      "operating point. The first of these sets is automatically chosen because selection of a "
                      "different dataset is not yet implemented.")
            dataset = candidate_datasets[0]

        if e_on_off_rr == 'e_off':
            candidate_datasets = [e_off for e_off in self.switch.e_off if (
                    e_off.t_j == t_j and e_off.v_g == v_g and e_off.v_supply == v_supply and e_off.r_g == r_g)]
            if len(candidate_datasets) == 0:
                available_datasets = [(e_off.t_j, e_off.v_g, e_off.v_supply, e_off.r_g) for e_off in self.switch.e_off]
                print("Available operating points: (t_j, v_g, v_supply, r_g)")
                print(available_datasets)
                raise ValueError("No data available for get_graph_i_e at the given operating point. "
                                 "A list of available operating points is printed above.")
            elif len(candidate_datasets) > 1:
                print("multiple datasets were found that are consistent with the chosen "
                      "operating point. The first of these sets is automatically chosen because selection of a "
                      "different dataset is not yet implemented.")
            dataset = candidate_datasets[0]

        if e_on_off_rr == 'e_rr':
            candidate_datasets = [e_rr for e_rr in self.diode.e_rr if (
                    e_rr.t_j == t_j and e_rr.v_g == v_g and e_rr.v_supply == v_supply and e_rr.r_g == r_g)]
            if len(candidate_datasets) == 0:
                available_datasets = [(e_rr.t_j, e_rr.v_g, e_rr.v_supply, e_rr.r_g) for e_rr in self.diode.e_rr]
                print("Available operating points: (t_j, v_g, v_supply, r_g)")
                print(available_datasets)
                raise ValueError("No data available for get_graph_i_e at the given operating point. "
                                 "A list of available operating points is printed above.")
            elif len(candidate_datasets) > 1:
                print("multiple datasets were found that are consistent with the chosen "
                      "operating point. The first of these sets is automatically chosen because selection of a "
                      "different dataset is not yet implemented.")
            dataset = candidate_datasets[0]
        return dataset

    @staticmethod
    def get_object_i_e_simplified(e_on_off_rr: str, t_j: float):
        """
        Function to get the loss graphs out of the transistor class, simplified version

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
            f"[{e_on_off_rr} for {e_on_off_rr} in self.{s_d}.{e_on_off_rr} if ({e_on_off_rr}.t_j == {t_j} and {e_on_off_rr}.dataset_type == 'graph_i_e')],[{e_on_off_rr} for {e_on_off_rr} in self.{s_d}.{e_on_off_rr} if {e_on_off_rr}.dataset_type == 'graph_r_e']",
            "<string>", "eval")
        ie_datasets, re_datasets = eval(code)
        i_e_dataset, r_e_dataset = None, None
        if len(ie_datasets) == 0 or re_datasets == 0:
            code = compile(
                f"[({e_on_off_rr}.t_j, {e_on_off_rr}.v_g, {e_on_off_rr}.v_supply, {e_on_off_rr}.r_g) for {e_on_off_rr} in self.{s_d}.{e_on_off_rr}]",
                "<string>", "eval")
            available_datasets = eval(code)
            print("Available operating points: (t_j, v_g, v_supply, r_g)")
            print(available_datasets)
            raise ValueError("No data available for get_graph_i_e at the given operating point. "
                             "A list of available operating points is printed above.")
        elif len(ie_datasets) > 1:
            print("multiple datasets were found that are consistent with the chosen operating point.")
            match = False
            for re_curve in re_datasets:
                for curve in ie_datasets:
                    if curve.v_supply == re_curve.v_supply and curve.t_j == re_curve.t_j and curve.v_g == re_curve.v_g:
                        i_e_dataset = curve
                        r_e_dataset = re_curve
                        match = True
            text_to_print = "A match found in r_e characteristics for the chosen operating point and therefore will be used" \
                if match else "The first of these sets is automatically chosen because selection of a different dataset is not yet implemented."
            print(text_to_print)
        elif len(ie_datasets) == 1:
            i_e_dataset = ie_datasets[0]
        return i_e_dataset, r_e_dataset

    @staticmethod
    def get_object_r_e_simplified(e_on_off_rr: str, t_j: float, v_g: float, v_supply: float, normalize_t_to_v: float) -> list:
        """
        Function to get the loss graphs out of the transistor class, simplified version
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
            f"[{e_on_off_rr} for {e_on_off_rr} in self.{s_d}.{e_on_off_rr} if {e_on_off_rr}.dataset_type == 'graph_r_e' and {e_on_off_rr}.v_supply == {v_supply}]",
            "<string>", "eval")
        candidate_datasets = eval(code)
        # Find closest loss curve
        dataset = None
        node = np.array([t_j / normalize_t_to_v, v_g])
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
            print("Available operating points: (t_j, v_g, v_supply, r_g)")
            print(available_datasets)
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
                print("Invalid v_supply provided : v_supply = {0} and choosing v_supply = {1} ".format(v_supply, v_supply_chosen))

            args = {
                'dataset_type': 'graph_i_e',
                'r_g': r_g,
                'v_supply': v_supply_chosen,
                'graph_i_e': self.calc_i_e_curve_using_r_e_curve(i_e_object, r_e_object, r_g, v_supply_chosen),
                't_j': i_e_object.t_j,
                'v_g': i_e_object.v_g,
            }
            # check dictionary
            self.isvalid_dict(args, 'SwitchEnergyData')
            # pack to object
            object_i_e_calc = self.SwitchEnergyData(args)
            return object_i_e_calc
        except Exception as e:
            print("{0} loss at chosen parameters: R_g = {1}, T_j = {2}, v_supply = {3} could not be possible due to \n {4}".format(e_on_off_rr, r_g, t_j, v_supply, e.args[0]))
            raise e

    def calc_i_e_curve_using_r_e_curve(self, i_e_object: SwitchEnergyData, r_e_object: SwitchEnergyData,
                                       r_g: float, v_supply_chosen: float) -> np.array:
        """
        Calculates the loss energy curve at the provided gate resistance value based on the r_e_graph data

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
        Get interpolated channel parameters. This function searches for ui_graphs with the chosen t_j and v_g. At
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
                print("Available operating points: (t_j, v_g)")
                print(available_datasets)
                raise ValueError("No data available for linearization at the given operating point. "
                                 "A list of available operating points is printed above.")
            elif len(candidate_datasets) > 1:
                print("During linearization, multiple datasets were found that are consistent with the chosen "
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
                    print("Available operating points: (t_j, v_g)")
                    print(available_datasets)
                    raise ValueError("No data available for linearization at the given operating point. "
                                     "A list of available operating points is printed above.")
                elif len(candidate_datasets) > 1:
                    print("During linearization, multiple datasets were found that are consistent with the chosen "
                          "operating point. The first of these sets is automatically chosen because selection of a "
                          "different dataset is not yet implemented.")
            else:
                candidate_datasets = [channel for channel in self.diode.channel
                                      if channel.t_j == t_j]
                if len(candidate_datasets) == 0:
                    available_datasets = [channel.t_j for channel in self.diode.channel]
                    print("Available operating points: (t_j)")
                    print(available_datasets)
                    raise ValueError("No data available for linearization at the given operating point. "
                                     "A list of available operating points is printed above.")
                elif len(candidate_datasets) > 1:
                    print("During linearization, multiple datasets were found that are consistent with the chosen "
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
        A method to generate thermal parameters like Rth_total, tau_total, Cth_total and vectors like Rth_vector, tau_vector, Cth_vector based
        on data availability passed by the user while creating a new transistor object.

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
            if not foster_args.r_th_vector is None and not foster_args.tau_vector is None and len(foster_args.tau_vector) == len(foster_args.r_th_vector):
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
                    print("R^2 score:", r_squared)
                    if len(rth_values) > 1:
                        foster_args.r_th_vector = [round(x, 5) for x in rth_values]
                        foster_args.tau_vector = [round(x, 5) for x in tau_values]
                        foster_args.c_th_vector = [round(x, 5) for x in cap_values]
                    if foster_args.r_th_total is None:
                        foster_args.r_th_total = round(sum(rth_values), 4)
                    foster_args.tau_total = round(sum(tau_values), 4)
                    foster_args.c_th_total = round(foster_args.tau_total / foster_args.r_th_total, 4)
                    if plotbit:
                        print("Computed Rth values: ", rth_values)
                        print("Computed tau values: ", tau_values)
                        print("Computed Cth values: ", cap_values)
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
            print("Thermal parameter computation failed: {0}".format(e))
        else:
            exec(f"self.{input_type}.thermal_foster = foster_args")
            print(input_type, ':Thermal parameters re-assigned to foster object')

    def compare_channel_linearized(self, i_channel: float, t_j: float = 150, v_g: float = 15) -> None:
        """
        Shows channel plots for switch and diode comparing the linearized graph and the original graph.
        This function searches for the closest available curves for given arguments t_j and v_g

        :param i_channel: current to linearize the channel
        :type i_channel: float
        :param t_j: junction temperature of interest, default set to 150 degree
        :type t_j: float
        :param v_g: gate voltage of interest, default set to 15V
        :type v_g: float

        :return: Plot, showing original channel data and linearized channel data
        :rtype: None
        """

        # search for closest objects
        switch_channel, eon, eoff = self.switch.find_approx_wp(t_j, v_g, normalize_t_to_v=10, switch_energy_dataset_type="graph_i_e")
        diode_channel, err = self.diode.find_approx_wp(t_j, v_g, normalize_t_to_v=10,
                                                       switch_energy_dataset_type="graph_i_e")
        # linearize channels at given points
        s_v_channel, s_r_channel = self.calc_lin_channel(switch_channel.t_j, switch_channel.v_g, i_channel, 'switch')
        d_v_channel, d_r_channel = self.calc_lin_channel(diode_channel.t_j, diode_channel.v_g, i_channel, 'diode')

        print('Linearized values. Switch at {0} °C and {1} V, diode at {2} °C and {3} V'.format(switch_channel.t_j, switch_channel.v_g, diode_channel.t_j, diode_channel.v_g))
        print(" s_v_channel = {0} V".format(s_v_channel))
        print(" s_r_channel = {0} Ohm".format(s_r_channel))
        print(" d_v_channel = {0} V".format(d_v_channel))
        print(" d_r_channel = {0} Ohm".format(d_r_channel))

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

    def export_datasheet(self, build_collection=False) -> Optional[str]:
        """
        Generates and exports the virtual datasheet in form of pdf

        :return: pdf file is created in the current working directory
        :rtype: None

        :Example:

        >>> import transistordatabase as tdb
        >>> transistor = tdb.load('Fuji_2MBI100XAA120-50')
        >>> transistor.export_datasheet()

        .. todo:: Instead of html file, generating a pdf file without third party requirements is a better option
        """
        # listV = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        pdf_data = {}
        devices = {}
        skip_ids = ['_id', 'wp', 'c_oss', 'c_iss', 'c_rss', 'graph_v_ecoss', 'c_oss_er', 'c_oss_tr']
        cap_plots = {'$c_{oss}$': self.c_oss, '$c_{rss}$': self.c_rss, '$c_{iss}$': self.c_iss}
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
        img_path = os.path.join(os.path.dirname(__file__), 'lea-upb.png')
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
        # pdfname = trans['Name'][0] + ".html"
        # datasheetpath = pathlib.Path.cwd() / pdfname
        # with open(trans['Name'][0] + ".html", "w") as fh:
        #     fh.write(html)
        # print(f"Export virtual datasheet {self.name}.html to {pathlib.Path.cwd().as_uri()}")
        # print(f"Open Datasheet here: {datasheetpath.as_uri()}")

    # export function start from here
    def buildList(self, attribute):
        """
        Gather list data (e.g. channel/e_on/e_off/e_rr) and check for 'None'

        :param attribute: attribute path to list

        :return: matlab compatible list of all attributes
        :rtype: list
        """
        # TODO: Seems to be this function is not used!

        if matlab_compatibility_test(self, attribute) is not np.nan:
            ListData = eval(attribute)
            Dataset = np.empty((len(ListData),), dtype=np.object)
            for i in range(len(ListData)):
                for attr, value in vars(ListData[i]).items():
                    if value is None:
                        setattr(ListData[i], attr, np.nan)
                Dataset[i] = ListData[i]
        else:
            Dataset = np.nan
        return Dataset

    def export_simulink_loss_model(self, r_g_on: float = None, r_g_off: float = None, v_supply: float = None,
                                   normalize_t_to_v: float = 10) -> None:
        """
        Exports a simulation model for simulink inverter loss models, see https://de.mathworks.com/help/physmod/sps/ug/loss-calculation-in-a-three-phase-3-level-inverter.html

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

        :return: .mat file for import in matlab/simulink
        :rtype: None

        :Example:

        >>> import transistordatabase as tdb
        >>> transistor = tdb.load('Infineon_FF200R12KE3')
        >>> transistor.export_simulink_loss_model()

        .. note::
         - temperature next to 25 and 150 degree at 15V gate voltage will be used for channel and switching loss
         - in case of just one temperature curve, the upper temperature will increased (+1K) to bring a small temperature change in the curves. Otherwise the model will not work
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

            print("---------------------IGBT properties----------------------")
            switch_channel_object_lower, eon_object_lower, eoff_object_lower = self.switch.find_approx_wp(t_j_lower, v_g, normalize_t_to_v, switch_energy_dataset_type="graph_i_e")
            switch_channel_object_upper, eon_object_upper, eoff_object_upper = self.switch.find_approx_wp(t_j_upper, v_g, normalize_t_to_v, switch_energy_dataset_type="graph_i_e")
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
                    print('Choosing the default curve properties for e_on')
                else:
                    print('Generated curve properties for e_on')
                    print("Lower : R_g(on) = {0}, v_g(on)= {1}, T_j = {2}, v_supply = {3}".format(eon_object_lower.r_g, eon_object_lower.v_g, eon_object_lower.t_j, eon_object_lower.v_supply))
                    print("Upper : R_g(on) = {0}, v_g(on)= {1}, T_j = {2}, v_supply = {3}".format(
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
                    print('Choosing the default curve properties for e_off')
                else:
                    print('Generated curve properties for e_off')
                    print("Lower : R_g(off) = {0}, v_g(off) = {1}, T_j = {2}, v_supply = {3}".format(eoff_object_lower.r_g,
                                                                                                     eoff_object_lower.v_g,
                                                                                                     eoff_object_lower.t_j,
                                                                                                     eoff_object_lower.v_supply))
                    print("Upper : R_g(off) = {0}, v_g(off) = {1}, T_j = {2}, v_supply = {3}".format(
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
            temp_t_j_switch_channel_upper = switch_channel_object_upper.t_j + 1 if switch_channel_object_lower.t_j == switch_channel_object_upper.t_j else switch_channel_object_upper.t_j
            temp_t_j_eon_upper = eon_object_upper.t_j + 1 if eon_object_lower.t_j == eon_object_upper.t_j else eon_object_upper.t_j
            temp_t_j_eoff_upper = eoff_object_upper.t_j + 1 if eoff_object_lower.t_j == eoff_object_upper.t_j else eoff_object_upper.t_j

            switch_dict = {'T_j_channel': np.double([switch_channel_object_lower.t_j, temp_t_j_switch_channel_upper]),
                           'T_j_ref_on': np.double([eon_object_lower.t_j, temp_t_j_eon_upper]),
                           'T_j_ref_off': np.double([eoff_object_lower.t_j, temp_t_j_eoff_upper]),
                           'R_th_total': matlab_compatibility_test(self, 'Transistor.switch.thermal_foster.r_th_total') if self.switch.thermal_foster.r_th_total != 0 else 1e-6,
                           'C_th_total': np.double(1),
                           'V_ref_on': np.double(eon_object_upper.v_supply),
                           'V_ref_off': np.double(eon_object_upper.v_supply),
                           'Eon': np.double(e_on_array * 1000),
                           'Eoff': np.double(e_off_array * 1000),
                           'v_channel': np.double(switch_channel_array),
                           'i_vec': np.double(i_interp),
                           }
            print("---------------------Diode properties----------------------")
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
                    print('Choosing the default properties for e_rr')
                else:
                    print('Generated curve properties for e_rr')
                    print("Lower : R_g = {0}, v_g = {1}, T_j = {2}, v_supply = {3}".format(err_object_lower.r_g,
                                                                                           err_object_lower.v_g,
                                                                                           err_object_lower.t_j,
                                                                                           err_object_lower.v_supply))
                    print("Upper : R_g = {0}, v_g = {1}, T_j = {2}, v_supply = {3}".format(
                        err_object_upper.r_g, err_object_upper.v_g, err_object_upper.t_j, err_object_upper.v_supply))

            diode_channel_lower_interp = np.interp(i_interp, diode_channel_object_lower.graph_v_i[1], diode_channel_object_lower.graph_v_i[0])
            diode_channel_upper_interp = np.interp(i_interp, diode_channel_object_upper.graph_v_i[1], diode_channel_object_upper.graph_v_i[0])
            diode_channel_array = np.array([diode_channel_lower_interp, diode_channel_upper_interp])

            e_rr_lower_interp = np.interp(i_interp, err_object_lower.graph_i_e[0], err_object_lower.graph_i_e[1])
            e_rr_upper_interp = np.interp(i_interp, err_object_upper.graph_i_e[0], err_object_upper.graph_i_e[1])
            err_array = np.array([e_rr_lower_interp, e_rr_upper_interp])

            # Simulink-power-electronic loss model can not handle curves in case of the temperatures are the same
            temp_t_j_switch_channel_upper = diode_channel_object_upper.t_j + 1 if diode_channel_object_lower.t_j == diode_channel_object_upper.t_j else diode_channel_object_upper.t_j
            temp_t_j_err_upper = err_object_upper.t_j + 1 if err_object_lower.t_j == err_object_upper.t_j else err_object_upper.t_j

            diode_dict = {
                'T_j_channel': np.double([diode_channel_object_lower.t_j, temp_t_j_switch_channel_upper]),
                'T_j_ref_rr': np.double([err_object_lower.t_j, temp_t_j_err_upper]),
                'R_th_total': matlab_compatibility_test(self, 'Transistor.diode.thermal_foster.r_th_total') if self.diode.thermal_foster.r_th_total != 0 else 1e-6,
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
                               'file_generated': f"{datetime.datetime.today()}",
                               'file_generated_by': "https://github.com/upb-lea/transistordatabase",
                               'datasheet_hyperlink': self.datasheet_hyperlink,
                               'r_g_on': np.double(eon_object_lower.r_g),
                               'r_g_off': np.double(eoff_object_lower.r_g),
                               }

            sio.savemat(self.name.replace('-', '_') + '_Simulink_lossmodel.mat', {self.name.replace('-', '_'): transistor_dict})
            print(f"Export files {self.name}_Simulink_lossmodel.mat to {pathlib.Path.cwd().as_uri()}")
        except Exception as e:
            print("Simulink exporter failed: {0}".format(e))

    def export_matlab(self) -> None:
        """
        Exports a transistor dictionary to a matlab dictionary

        :return: File stored in current working path
        :rtype: None

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
        transistor_clean_dict['file_generated'] = f"{datetime.datetime.today()}"
        transistor_clean_dict['file_generated_by'] = "https://github.com/upb-lea/transistordatabase",

        sio.savemat(self.name.replace('-', '_') + '_Matlab.mat', {self.name.replace('-', '_'): transistor_clean_dict})
        print(f"Export files {self.name.replace('-', '_')}_Matlab.mat to {pathlib.Path.cwd().as_uri()}")

    def collect_i_e_and_r_e_combination(self, switch_type: str, loss_type: str) -> tuple[list, list]:
        """
        A function to gather the i_e and r_e graph combinations from the available energy curves which are further used in gecko circuit exporter function

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
        for index, loss_curve in enumerate(curves_set):
            for next_index in range(index + 1, len(curves_set)):
                if not curves_set[index].dataset_type == curves_set[next_index].dataset_type and curves_set[index].t_j == curves_set[next_index].t_j and curves_set[index].v_g == curves_set[
                    next_index].v_g \
                        and curves_set[index].v_supply == curves_set[next_index].v_supply:
                    if curves_set[index].dataset_type == 'graph_i_e':
                        i_e_indexes.append(index)
                        r_e_indexes.append(next_index)
                    else:
                        i_e_indexes.append(next_index)
                        r_e_indexes.append(index)
        # If no combos available then providing indexes of only dataset_type == graph_i_e
        if not any(i_e_indexes):
            for index, loss_curve in enumerate(curves_set):
                if curves_set[index].dataset_type == 'graph_i_e':
                    i_e_indexes.append(index)
        return i_e_indexes, r_e_indexes

    def export_geckocircuits(self, recheck: bool = True, v_supply: float = None, v_g_on: float = None,
                             v_g_off: float = None, r_g_on: float = None, r_g_off: float = None) -> None:
        """
        Export transistor data to GeckoCIRCUITS

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

        :return: Two output files: 'Transistor.name'_Switch.scl and 'Transistor.name'_Diode.scl created in the current working directory
        :rtype: None

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
                                                                                                         check_specific_curves=[eon_i_e_indexes, eoff_i_e_indexes])
                diode_channel_vg, diode_v_supply, v_d_err = self.diode.find_next_gate_voltage(diode_selected_params, export_type='gecko', check_specific_curves=err_i_e_indexes)
            except MissingDataError as e:
                print(e.args[0], e.em[e.args[0]] + ' .scl')

        # Gather data
        # Channel curves
        sw_channel_curves = list()
        for index, channel in enumerate(self.switch.channel):
            if channel.v_g == switch_channel_vg:
                sw_channel_curves.append(channel)

        diode_channel_curves = list()
        for index, channel in enumerate(self.diode.channel):
            if (channel.v_g is None and diode_channel_vg == 0) or channel.v_g == diode_channel_vg:
                diode_channel_curves.append(channel)

        # Loss energy curves : From the computed neighbours and recheck for provided or recommended r_g, if not compute the energy curve
        eon_curves = list()
        mapped_set = dict(zip(eon_i_e_indexes, eon_r_e_indexes))  # empty dict if no r_e and i_e combinations exists
        for index, curve in enumerate(self.switch.e_on):
            if index in eon_i_e_indexes and curve.v_supply == switch_v_supply and curve.v_g == v_g_on:
                r_g_on = curve.r_g if r_g_on is None and len(mapped_set) else r_g_on  # if no r_g is provided and also recommended is None final resort to get a r_g
                if not curve.r_g == r_g_on and len(mapped_set):
                    mapped_r_e_object = self.switch.e_on[mapped_set[index]]
                    new_curve = curve.copy()
                    new_curve.graph_i_e = self.calc_i_e_curve_using_r_e_curve(new_curve, mapped_r_e_object, r_g_on, switch_v_supply)
                    print('E_on curve estimated at {0} Ohm and supply voltage of {1}V'.format(r_g_on, switch_v_supply))
                    new_curve.r_g = r_g_on
                    eon_curves.append(new_curve)
                else:
                    print('Exporting default E_on curves at the selected voltage parameters.->Either re-estimation not possible or r_g specific curve found!')
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
                    print('E_off curve estimated at {0} Ohm and supply voltage of {1}V'.format(r_g_off, switch_v_supply))
                    new_curve.r_g = r_g_on
                    eoff_curves.append(new_curve)
                else:
                    print('Exporting default E_off curves at the selected voltage parameters.->Either re-estimation not possible or r_g specific curve found!')
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
                    print('E_rr curve estimated at {0} Ohm and supply voltage of {1}V'.format(r_g_err, diode_v_supply))
                    new_curve.r_g = r_g_err
                    err_curves.append(new_curve)
                else:
                    print('Exporting default E_rr curves at the selected voltage parameters.->Either re-estimation not possible or r_g specific curve found!')
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

                if self.type.lower() == 'mosfet' or self.type.lower() == 'sic-mosfet':
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
                print('Switch: No loss curves found!')
                file_switch.write("<SchaltverlusteMesskurve>\n")
                file_switch.write(f"data[][] 3 2 0 10 0 0 0 0")
                file_switch.write(f"\ntj 25\n")
                file_switch.write(f"uBlock 400\n")
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
            print(f"Exported file {self.name}_Switch(rg_on_{r_g_on})(rg_off_{r_g_off}).scl  to {pathlib.Path.cwd().as_uri()}")
        else:
            print('\nGecko exporter switch failed: No channel curve available at the selected v_g \n Try by setting recheck = True if set to False')

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
                print('Diode: No loss curves found!')
                file_diode.write(f"anzMesskurvenPvSWITCH 1\n")
                file_diode.write("<SchaltverlusteMesskurve>\n")
                file_diode.write(f"data[][] 3 2 0 10 0 0 0 0")
                file_diode.write(f"\ntj 25\n")
                file_diode.write(f"uBlock 400\n")
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
            print(f"Exported file {self.name}_Diode(rg_{r_g_err}).scl to {pathlib.Path.cwd().as_uri()}")
        else:
            print('\nGecko exporter diode failed: No channel curve available at the selected v_g \n Try by setting recheck = True if set to False')

        # set print options back to default
        np.set_printoptions(linewidth=75)

    def export_plecs(self, recheck: bool = True, gate_voltages=None) -> None:
        """
        Generates and exports the switch and diode .xmls files to be imported into plecs simulator

        :param recheck: enables the selection of gate voltages near to the provided values if not found
        :type recheck: bool
        :param gate_voltages: gate voltage like v_g_on, v_g_off, v_d_on, v_d_off

        :return: Two output files: 'Transistor.name'_Switch.xml and 'Transistor.name'_Diode.xml created in the current working directory
        :rtype: None

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
        print("Export files {0}_switch.xml and {1}_diode.xml to {2}".format(data['partnumber'], data['partnumber'], pathlib.Path.cwd().as_uri()))

    class FosterThermalModel:
        """
        Contains data to specify parameters of the Foster thermal_foster model. This model describes the transient
        temperature behavior as a thermal_foster RC-network. The necessary parameters can be estimated by curve-fitting
        transient temperature data supplied in graph_t_rthjc or by manually specifying the individual 2 out of 3 of the
        parameters R, C, and tau.

        .. todo::
            - Add function to estimate parameters from transient data.
            - Add function to automatically calculate missing parameters from given ones.
            - Do these need to be numpy array or should they be lists instead?
        """

        # Thermal resistances of RC-network (array).
        r_th_vector: Optional[List[float]]  #: Thermal resistances of RC-network (array). Units in K/W (Optional key)
        # Sum of thermal_foster resistances of n-pole RC-network (scalar).
        r_th_total: Optional[float]  #: Sum of thermal_foster resistances of n-pole RC-network (scalar). Units in K/W  (Optional key)
        # Thermal capacities of n-pole RC-network (array).
        c_th_vector: Optional[List[float]]  #: Thermal capacities of n-pole RC-network (array). Units in J/K (Optional key)
        # Sum of thermal_foster capacities of n-pole low pass as (scalar).
        c_th_total: Optional[float]  #: Sum of thermal_foster capacities of n-pole low pass as (scalar). Units in J/K  (Optional key)
        # Thermal time constants of n-pole RC-network (array).
        tau_vector: Optional[List[float]]  #: Thermal time constants of n-pole RC-network (array). Units in s  (Optional key)
        # Sum of thermal_foster time constants of n-pole RC-network (scalar).
        tau_total: Optional[float]  #: Sum of thermal_foster time constants of n-pole RC-network (scalar). Units in s (Optional key)
        # Transient data for extraction of the thermal_foster parameters specified above.
        # Represented as a 2xm Matrix where row 1 is the time and row 2 the temperature.
        graph_t_rthjc: Optional[npt.NDArray[np.float64]]  #: Transient data for extraction of the thermal_foster parameters specified above. Units of Row 1 in s; Row 2 in K/W  (Optional key)

        def __init__(self, args):
            """
            Initialization method of FosterThermalModel object

            :param args: argument to be passed for initialization
            :type args: dict

            .. note:: Can be constructed from empty or 'None' argument dictionary since no attributes are mandatory.
            """
            if Transistor.isvalid_dict(args, 'FosterThermalModel'):
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
            The method converts FosterThermalModel object into dict datatype

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
            Plots tau vs rthjc

            :param buffer_req: Internally required for generating virtual datasheets
            :type buffer_req: bool

            :return: Respective plots are displayed if available else None is returned
            """
            if self.graph_t_rthjc is None:
                print('No Foster impedance information exists!')
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
            Collects foster data in form of dictionary for generating virtual datasheet

            :return: foster data in form of dictionary
            :rtype: dict
            """
            foster_data = {}
            foster_data['foster_plot'] = {'imp_plot': self.get_plots(True)}
            skipIds = ['graph_t_rthjc']
            for attr in dir(self):
                if attr not in skipIds and not callable(getattr(self, attr)) and not attr.startswith("__") and not isinstance(getattr(self, attr), (list, dict)) \
                        and (not getattr(self, attr) is None):
                    foster_data[attr.capitalize()] = getattr(self, attr)
            return foster_data

    class Switch:
        """Contains data associated with the switching-characteristics of a MOSFET/SiC-MOSFET or IGBT. Can contain multiple
        channel-, e_on- and e_off-datasets. """
        # Metadata
        comment: Optional[str]  #: Comment if any to be specified (Optional key)
        manufacturer: Optional[str]  #: Name of the manufacturer (Optional key)
        technology: Optional[str]  #: Semiconductor technology. e.g. IGBT3/IGBT4/IGBT7  (Optional key)
        # These are documented in their respective class definitions.
        thermal_foster: Transistor.FosterThermalModel  #: Transient thermal_foster model. (Optional key)
        channel: Optional[List[Transistor.ChannelData]]  #: Switch channel voltage and current data.
        e_on: Optional[List[Transistor.SwitchEnergyData]]  #: Switch on energy data.
        e_off: Optional[List[Transistor.SwitchEnergyData]]  #: Switch of energy data.
        e_on_meas: Optional[List[Transistor.SwitchEnergyData]]  #: Switch on energy data.
        e_off_meas: Optional[List[Transistor.SwitchEnergyData]]  #: Switch on energy data.
        linearized_switch: Optional[List[Transistor.LinearizedModel]]  #: Static data valid for a specific operating point.
        r_channel_th: Optional[List[Transistor.TemperatureDependResistance]]  #: Temperature dependant on resistance.
        charge_curve: Optional[List[Transistor.GateChargeCurve]]  #: Gate voltage dependant charge characteristics
        t_j_max: float   #: Maximum junction temperature. Units in °C (Mandatory key)
        soa: Optional[List[Transistor.SOA]]  #: Safe operating area of switch

        def __init__(self, switch_args):
            """
            Initialization method of Switch object

            :param switch_args: argument to be passed for initialization

            :raises KeyError: Expected during the channel/e_on/e_off instance initialization
            :raises ValueError: Expected during the channel/e_on/e_off instance initialization

            .. todo:: Is this the right behavior or should the 'thermal_foster' attribute be left empty instead?
            """
            # Current behavior on empty 'foster' dictionary: thermal_foster object is still created but with empty attributes.
            # ToDo: Is this the right behavior or should the 'thermal_foster' attribute be left empty instead?
            self.thermal_foster = Transistor.FosterThermalModel(switch_args.get('thermal_foster'))
            if Transistor.isvalid_dict(switch_args, 'Switch'):
                self.t_j_max = switch_args.get('t_j_max')
                self.comment = switch_args.get('comment')
                self.manufacturer = switch_args.get('manufacturer')
                self.technology = switch_args.get('technology')
                # This currently accepts dictionaries and lists of dictionaries. Validity is only checked by keys and
                # not their values.
                self.channel = []  # Default case: Empty list
                try:
                    if isinstance(switch_args.get('channel'), list):
                        # Loop through list and check each dict for validity. Only create ChannelData objects from valid
                        # dicts. 'None' and empty dicts are ignored.
                        for dataset in switch_args.get('channel'):
                            if Transistor.isvalid_dict(dataset, 'Switch_ChannelData'):
                                self.channel.append(Transistor.ChannelData(dataset))
                    elif Transistor.isvalid_dict(switch_args.get('channel'), 'Switch_ChannelData'):
                        # Only create ChannelData objects from valid dicts
                        self.channel.append(Transistor.ChannelData(switch_args.get('channel')))
                except KeyError as error:
                    # If KeyError occurs during for loop, raise KeyError and add index of list occurrence to the message
                    dict_list = switch_args.get('channel')
                    if not error.args:
                        error.args = ('',)  # This syntax is necessary because error.args is a tuple
                    error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                  f"Switch_ChannelData dictionaries: ",) + error.args
                    raise
                except ValueError as error:
                    dict_list = switch_args.get('channel')
                    raise Exception(f"for index [{str(dict_list.index(dataset))}] in list of Switch_ChannelData dictionaries:" + str(error))

                self.e_on = []  # Default case: Empty list
                if isinstance(switch_args.get('e_on'), list):
                    # Loop through list and check each dict for validity. Only create SwitchEnergyData objects from
                    # valid dicts. 'None' and empty dicts are ignored.
                    for dataset in switch_args.get('e_on'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'SwitchEnergyData'):
                                self.e_on.append(Transistor.SwitchEnergyData(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = switch_args.get('e_on')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                          f"Switch-SwitchEnergyData dictionaries for e_on: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(switch_args.get('e_on'), 'SwitchEnergyData'):
                    # Only create SwitchEnergyData objects from valid dicts
                    self.e_on.append(Transistor.SwitchEnergyData(switch_args.get('e_on')))

                self.e_off = []  # Default case: Empty list
                if isinstance(switch_args.get('e_off'), list):
                    for dataset in switch_args.get('e_off'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'SwitchEnergyData'):
                                self.e_off.append(Transistor.SwitchEnergyData(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = switch_args.get('e_off')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                          f"Switch-SwitchEnergyData dictionaries for e_off: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(switch_args.get('e_off'), 'SwitchEnergyData'):
                    self.e_off.append(Transistor.SwitchEnergyData(switch_args.get('e_off')))

                self.e_on_meas = []  # Default case: Empty list
                if isinstance(switch_args.get('e_on_meas'), list):
                    # Loop through list and check each dict for validity. Only create SwitchEnergyData objects from
                    # valid dicts. 'None' and empty dicts are ignored.
                    for dataset in switch_args.get('e_on_meas'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'SwitchEnergyData'):
                                self.e_on_meas.append(Transistor.SwitchEnergyData(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = switch_args.get('e_on_meas')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                          f"Switch-SwitchEnergyData dictionaries for e_on_meas: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(switch_args.get('e_on_meas'), 'SwitchEnergyData'):
                    # Only create SwitchEnergyData objects from valid dicts
                    self.e_on_meas.append(Transistor.SwitchEnergyData(switch_args.get('e_on_meas')))

                self.e_off_meas = []  # Default case: Empty list
                if isinstance(switch_args.get('e_off_meas'), list):
                    for dataset in switch_args.get('e_off_meas'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'SwitchEnergyData'):
                                self.e_off_meas.append(Transistor.SwitchEnergyData(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = switch_args.get('e_off_meas')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                          f"Switch-SwitchEnergyData dictionaries for e_off_meas: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(switch_args.get('e_off_meas'), 'SwitchEnergyData'):
                    self.e_off_meas.append(Transistor.SwitchEnergyData(switch_args.get('e_off_meas')))

                self.linearized_switch = []  # Default case: Empty list
                if isinstance(switch_args.get('linearized_switch'), list):
                    # Loop through list and check each dict for validity. Only create LinearizedModel objects from
                    # valid dicts. 'None' and empty dicts are ignored.
                    for dataset in switch_args.get('linearized_switch'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'Switch_LinearizedModel'):
                                self.linearized_switch.append(Transistor.LinearizedModel(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = switch_args.get('linearized_switch')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                          f"Switch-LinearizedModel dictionaries for e_on: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(switch_args.get('linearized_switch'), 'Switch_LinearizedModel'):
                    # Only create LinearizedModel objects from valid dicts
                    self.linearized_switch.append(Transistor.LinearizedModel(switch_args.get('linearized_switch')))

                self.r_channel_th = []  # Default case: Empty list
                if isinstance(switch_args.get('r_channel_th'), list):
                    # Loop through list and check each dict for validity. Only create TemperatureDependResistance objects from
                    # valid dicts. 'None' and empty dicts are ignored.
                    for dataset in switch_args.get('r_channel_th'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'TemperatureDependResistance'):
                                self.r_channel_th.append(Transistor.TemperatureDependResistance(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = switch_args.get('r_channel_th')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                          f"Switch-TemperatureDependResistance dictionaries for r_channel_th: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(switch_args.get('r_channel_th'), 'TemperatureDependResistance'):
                    # Only create TemperatureDependResistance objects form valid dicts
                    self.r_channel_th.append(Transistor.TemperatureDependResistance(switch_args.get('r_channel_th')))

                self.charge_curve = []  # Default case: Empty list
                if isinstance(switch_args.get('charge_curve'), list):
                    # Loop through list and check each dict for validity. Only create GateChargeCurve objects from
                    # valid dicts. 'None' and empty dicts are ignored.
                    for dataset in switch_args.get('charge_curve'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'GateChargeCurve'):
                                self.charge_curve.append(Transistor.GateChargeCurve(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = switch_args.get('charge_curve')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                          f"Switch-GateChargeCurve dictionaries for charge_curve: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(switch_args.get('charge_curve'), 'GateChargeCurve'):
                    # Only create GateChargeCurve objects form valid dicts
                    self.charge_curve.append(Transistor.GateChargeCurve(switch_args.get('charge_curve')))

                self.soa = []  # Default case: Empty list
                if isinstance(switch_args.get('soa'), list):
                    # Loop through list and check each dict for validity. Only create SOA objects from
                    # valid dicts. 'None' and empty dicts are ignored.
                    for dataset in switch_args.get('soa'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'SOA'):
                                self.soa.append(Transistor.SOA(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = switch_args.get('soa')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of soa "
                                          f"dictionaries: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(switch_args.get('soa'), 'SOA'):
                    # Only create SOA objects from valid dicts
                    self.soa.append(Transistor.SOA(switch_args.get('soa')))

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

        def convert_to_dict(self) -> dict:
            """
            The method converts Switch object into dict datatype

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

        def find_next_gate_voltage(self, req_gate_vltgs: dict, export_type: str, check_specific_curves: list = None,
                                   switch_loss_dataset_type: str = "graph_i_e") -> int:
            """
            Finds the switch gate voltage nearest to the specified values from the available gate voltages in curve datasets. Applicable to either plecs exporter or gecko exporter

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
            e_ons = [e for i, e in enumerate(self.e_on) if e.dataset_type == switch_loss_dataset_type and (not any(check_specific_curves[0]) or i in check_specific_curves[0])]
            if not e_ons:
                raise MissingDataError(1102)
            # gather e_off loss curves at required dataset_type and check for none
            e_offs = [e for i, e in enumerate(self.e_off) if e.dataset_type == switch_loss_dataset_type and (not any(check_specific_curves[1]) or i in check_specific_curves[1])]
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
                -> tuple[Transistor.ChannelData, Transistor.SwitchEnergyData, Transistor.SwitchEnergyData]:
            """
            This function looks for the smallest distance to stored object value and returns this working point

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
            node = np.array([t_j / normalize_t_to_v, v_g])
            # Find closest channeldata
            channeldata_t_js = np.array([chan.t_j for chan in self.channel])
            channeldata_v_gs = np.array([0 if chan.v_g is None else chan.v_g for chan in self.channel])
            nodes = np.array([channeldata_t_js / normalize_t_to_v, channeldata_v_gs]).transpose()
            index_channeldata = distance.cdist([node], nodes).argmin()

            # Find closest e_on
            e_ons = [e for e in self.e_on if e.dataset_type == switch_energy_dataset_type]
            if not e_ons:
                raise KeyError(f"There is no e_on data with type {switch_energy_dataset_type} for this Switch object.")
            e_on_t_js = np.array([e.t_j for e in e_ons])
            e_on_v_gs = np.array([0 if e.v_g is None else e.v_g for e in e_ons])
            nodes = np.array([e_on_t_js / normalize_t_to_v, e_on_v_gs]).transpose()
            index_e_on = distance.cdist([node], nodes).argmin()
            # Find closest e_off
            e_offs = [e for e in self.e_off if e.dataset_type == switch_energy_dataset_type]
            if not e_offs:
                raise KeyError(f"There is no e_off data with type {switch_energy_dataset_type} for this Switch object.")
            e_off_t_js = np.array([e.t_j for e in e_offs])
            e_off_v_gs = np.array([0 if e.v_g is None else e.v_g for e in e_offs])
            nodes = np.array([e_off_t_js / normalize_t_to_v, e_off_v_gs]).transpose()
            index_e_off = distance.cdist([node], nodes).argmin()
            print("run switch.find_approx_wp: closest working point for t_j = {0} °C and v_g = {1} V:".format(t_j, v_g))
            print(f"channel: t_j = {self.channel[index_channeldata].t_j} °C and v_g = {self.channel[index_channeldata].v_g} V")
            print(f"eon:     t_j = {e_ons[index_e_on].t_j} °C and v_g = {e_ons[index_e_on].v_g} V")
            print(f"eoff:    t_j = {e_offs[index_e_off].t_j} °C and v_g = {e_offs[index_e_off].v_g} V")

            return self.channel[index_channeldata], e_ons[index_e_on], e_offs[index_e_off]

        def plot_channel_data_vge(self, gatevoltage: float) -> None:
            """
            Plot channel data with a chosen gate-voltage

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
            Plot channel data with chosen temperature

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
            Plot all switch channel characteristic curves

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
                        #plt.title('Channel at $T_{{J}}$ = {0} °C'.format(key))
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
                        #plt.title('Channel at $V_{{g}}$ = {0} V'.format(key))
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
            Plots all switch energy i-e characteristic curves which are extracted from the manufacturer datasheet

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
                        labelplot = "$e_{{on}}$: $V_{{supply}}$ = {0} V, $V_{{g}}$ = {1} V, $T_{{J}}$ = {2} °C, $R_{{g}}$ = {3} Ohm".format(self.e_on[i_energy_data].v_supply,
                                                                                                                                            self.e_on[i_energy_data].v_g, self.e_on[i_energy_data].t_j,
                                                                                                                                            self.e_on[i_energy_data].r_g)
                        plt.plot(self.e_on[i_energy_data].graph_i_e[0], self.e_on[i_energy_data].graph_i_e[1],
                                 label=labelplot)
                        plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
                        plt.yticks(rotation=90)
                # look for e_off losses
                for i_energy_data in np.array(range(0, len(self.e_off))):
                    if self.e_off[i_energy_data].dataset_type == 'graph_i_e':
                        labelplot = "$e_{{off}}$: $V_{{supply}}$ = {0} V, $V_{{g}}$ = {1} V, $T_{{J}}$ = {2} °C, $R_{{g}}$ = {3} Ohm".format(self.e_off[i_energy_data].v_supply,
                                                                                                                                             self.e_off[i_energy_data].v_g,
                                                                                                                                             self.e_off[i_energy_data].t_j,
                                                                                                                                             self.e_off[i_energy_data].r_g)
                        plt.plot(self.e_off[i_energy_data].graph_i_e[0], self.e_off[i_energy_data].graph_i_e[1],
                                 label=labelplot)
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
             Plots all switch energy r-e characteristic curves

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
                        labelplot = "$e_{{on}}$: $V_{{supply}}$ = {0} V, $V_{{g}}$ = {1} V, $T_{{J}}$ = {2} °C, $i_{{ch}}$ = {3} A".format(self.e_on[i_energy_data].v_supply,
                                                                                                                                           self.e_on[i_energy_data].v_g, self.e_on[i_energy_data].t_j,
                                                                                                                                           self.e_on[i_energy_data].i_x)
                        plt.plot(self.e_on[i_energy_data].graph_r_e[0], self.e_on[i_energy_data].graph_r_e[1],
                                 label=labelplot)
                        plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
                # look for e_off losses
                for i_energy_data in np.array(range(0, len(self.e_off))):
                    if self.e_off[i_energy_data].dataset_type == 'graph_r_e':
                        labelplot = "$e_{{off}}$: $V_{{supply}}$ = {0} V, $V_{{g}}$ = {1} V, $T_{{J}}$ = {2} °C, $i_{{ch}}$ = {3} A".format(self.e_off[i_energy_data].v_supply,
                                                                                                                                            self.e_off[i_energy_data].v_g,
                                                                                                                                            self.e_off[i_energy_data].t_j,
                                                                                                                                            self.e_off[i_energy_data].i_x)
                        plt.plot(self.e_off[i_energy_data].graph_r_e[0], self.e_off[i_energy_data].graph_r_e[1],
                                 label=labelplot)
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

        def plot_all_on_resistance_curves(self, buffer_req: bool = False):
            """
            A helper function to plot and convert Temperature dependant on resistance plots in raw data format.

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
                r_on_condition = '\n'.join(["conditions: ", "$V_{g}$ = " + str(self.r_channel_th[0].v_g) + " V", "$I_{channel}$= " + str(self.r_channel_th[0].i_channel) + " A"])
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
            A helper function to plot and convert gate emitter/source voltage dependant gate charge plots in raw data format.

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
                charge_condition = '\n'.join(["conditions: ", "$I_{{channel}}$ = {0} [A]".format(self.charge_curve[0].i_channel), "$V_{{supply}}$= {0} [V]".format(self.charge_curve[0].v_supply),
                                              "$T_{{j}}$ = {0} [°C]".format(self.charge_curve[0].t_j),
                                              "$I_{{g}}$ = {0} ".format('NA' if self.charge_curve[0].i_g is None else (str(self.charge_curve[0].i_g) + ' [A]'))])
                ax.text(0.05, 0.95, charge_condition, transform=ax.transAxes, fontsize='small', bbox=props, ha='left', va='top')
            else:
                plt.legend(fontsize=8)
                charge_condition = '\n'.join(["conditions: ", "$I_{{channel}}$ = {0} [A]".format(self.charge_curve[0].i_channel), "$T_{{j}}$ = {0} [°C]".format(self.charge_curve[0].t_j),
                                              "$I_{{g}}$ = {0} ".format('NA' if self.charge_curve[0].i_g is None else (str(self.charge_curve[0].i_g) + ' [A]'))])
                ax.text(0.65, 0.1, charge_condition, transform=ax.transAxes, fontsize='small', bbox=props, ha='left', va='bottom')
            plt.grid()
            if buffer_req:
                return get_img_raw_data(plt)
            else:
                plt.show()

        def plot_soa(self, buffer_req: bool = False):
            """
             A helper function to plot and convert safe operating region characteristic plots in raw data format.

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
            Collects switch data in form of dictionary for generating virtual datasheet

            :return: Switch data in form of dictionary
            :rtype: dict
            """
            switch_data = {}
            switch_data['plots'] = {'channel_plots': self.plot_all_channel_data(True), 'energy_plots': self.plot_energy_data(True), 'energy_plots_r': self.plot_energy_data_r(True), 'r_channel_th_plot': self.plot_all_on_resistance_curves(True), 'charge_curve': self.plot_all_charge_curves(True), 'soa': self.plot_soa(True)}
            for attr in dir(self):
                if attr == 'thermal_foster':
                    switch_data.update(getattr(self, attr).collect_data())
                elif not callable(getattr(self, attr)) and not attr.startswith("__") and not \
                        isinstance(getattr(self, attr), (list, np.ndarray, dict)) and (not getattr(self, attr) is None) and not getattr(self, attr) == "":
                    switch_data[attr.capitalize()] = getattr(self, attr)
            return switch_data

    class Diode:
        """
        Contains data associated with the (reverse) diode-characteristics of a MOSFET/SiC-MOSFET or IGBT. Can contain
        multiple channel- and e_rr- datasets.
         """
        # Metadata
        comment: Optional[str]  #: Comment if any specified by the user. (Optional key)
        manufacturer: Optional[str]  #: Name of the manufacturer. (Optional key)
        technology: Optional[str]  #: Semiconductor technology. e.g. IGBT3/IGBT4/IGBT7. (Optional key)
        # These are documented in their respective class definitions.
        thermal_foster: Optional[Transistor.FosterThermalModel]  #: Transient thermal_foster model.
        channel: Optional[List[Transistor.ChannelData]]  #: Diode forward voltage and forward current data.
        e_rr: Optional[List[Transistor.SwitchEnergyData]]  #: Reverse recovery energy data.
        linearized_diode: Optional[List[Transistor.LinearizedModel]]  #: Static data. Valid for a specific operating point.
        t_j_max: float  #: Diode maximum junction temperature. Units in °C (Mandatory key)
        soa: Optional[List[Transistor.SOA]]  #: Safe operating area of Diode

        def __init__(self, diode_args):
            """
            Initialization method of Diode object

            :param diode_args: argument to be passed for initialization

            :raises KeyError: Expected during the channel/e_rr instance initialization
            :raises ValueError: Expected during the channel/e_rr instance initialization


            """
            # Current behavior on empty 'foster' dictionary: thermal_foster object is still created but with empty
            # attributes.

            # ToDo: Is this the right behavior or should the 'thermal_foster' attribute be left empty instead?
            self.thermal_foster = Transistor.FosterThermalModel(diode_args.get('thermal_foster'))
            if Transistor.isvalid_dict(diode_args, 'Diode'):
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
                            if Transistor.isvalid_dict(dataset, 'Diode_ChannelData'):
                                self.channel.append(Transistor.ChannelData(dataset))
                                # If  occurs during this, raise KeyError and add index of list occurrence to the message
                    elif Transistor.isvalid_dict(diode_args.get('channel'), 'Diode_ChannelData'):
                        # Only create ChannelData objects from valid dicts
                        self.channel.append(Transistor.ChannelData(diode_args.get('channel')))
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
                            if Transistor.isvalid_dict(dataset, 'SwitchEnergyData'):
                                self.e_rr.append(Transistor.SwitchEnergyData(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = diode_args.get('e_rr')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                          f"Diode-SwitchEnergyData dictionaries for e_rr: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(diode_args.get('e_rr'), 'SwitchEnergyData'):
                    # Only create SwitchEnergyData objects from valid dicts
                    self.e_rr.append(Transistor.SwitchEnergyData(diode_args.get('e_rr')))

                self.linearized_diode = []  # Default case: Empty list
                if isinstance(diode_args.get('linearized_diode'), list):
                    # Loop through list and check each dict for validity. Only create LinearizedModel objects from
                    # valid dicts. 'None' and empty dicts are ignored.
                    for dataset in diode_args.get('linearized_diode'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'Diode_LinearizedModel'):
                                self.linearized_diode.append(Transistor.LinearizedModel(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = diode_args.get('linearized_diode')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                          f"Diode-LinearizedModel dictionaries: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(diode_args.get('linearized_diode'), 'Diode_LinearizedModel'):
                    # Only create LinearizedModel objects from valid dicts
                    self.linearized_diode.append(Transistor.LinearizedModel(diode_args.get('linearized_diode')))

                self.soa = []  # Default case: Empty list
                if isinstance(diode_args.get('soa'), list):
                    # Loop through list and check each dict for validity. Only create SOA objects from
                    # valid dicts. 'None' and empty dicts are ignored.
                    for dataset in diode_args.get('soa'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'SOA'):
                                self.soa.append(Transistor.SOA(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = diode_args.get('soa')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of soa "
                                          f"dictionaries: ",) + error.args
                            raise
                elif Transistor.isvalid_dict(diode_args.get('soa'), 'SOA'):
                    # Only create SOA objects from valid dicts
                    self.soa.append(Transistor.SOA(diode_args.get('soa')))

            else:  # Can be constructed from empty or 'None' argument dictionary since no attributes are mandatory.
                self.comment = None
                self.manufacturer = None
                self.technology = None
                self.channel = []
                self.e_rr = []
                self.linearized_diode = []

        def convert_to_dict(self) -> dict:
            """
            The method converts Diode object into dict datatype

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
            Finds the diode gate voltage nearest to the specified values from the available gate voltages in curve datasets.
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
            e_rrs = [e for i, e in enumerate(self.e_rr) if e.dataset_type == diode_loss_dataset_type and (not any(check_specific_curves) or i in check_specific_curves)]
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

            print("--Diode Recheck--")
            for key, value in req_gate_vltgs.items():
                print(key + ': ', value)
            return req_gate_vltgs.values()

        def find_approx_wp(self, t_j: float, v_g: float, normalize_t_to_v: float = 10,
                           switch_energy_dataset_type: str = "graph_i_e") \
                -> tuple[Transistor.ChannelData, Transistor.SwitchEnergyData]:
            """
            This function looks for the smallest distance to stored object value and returns this working point

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
            node = np.array([t_j / normalize_t_to_v, v_g])
            # Find closest channeldata
            channeldata_t_js = np.array([chan.t_j for chan in self.channel])
            channeldata_v_gs = np.array([0 if chan.v_g is None else chan.v_g for chan in self.channel])
            nodes = np.array([channeldata_t_js / normalize_t_to_v, channeldata_v_gs]).transpose()
            index_channeldata = distance.cdist([node], nodes).argmin()
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

                print("run diode.find_approx_wp: closest working point for t_j = {0} °C and v_g = {1} V:".format(t_j, v_g))
                print("channel: t_j = {0} °C and v_g = {1} V".format(self.channel[index_channeldata].t_j, self.channel[index_channeldata].v_g))
                print("err:     t_j = {0} °C and v_g = {1} V".format(e_rrs[index_e_rr].t_j, e_rrs[index_e_rr].v_g))

            return self.channel[index_channeldata], e_rrs[index_e_rr]

        def plot_all_channel_data(self, buffer_req: bool = False):
            """
            Plot all diode channel characteristic curves

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
            Plots all diode reverse recovery energy i-e characteristic curves which are extracted from the manufacturer datasheet

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
                        labelplot = "$e_{{rr}}$: $v_{{supply}}$ = {0} V, $T_{{J}}$ = {1} °C, $R_{{g}}$ = {2} Ohm".format(self.e_rr[i_energy_data].v_supply, self.e_rr[i_energy_data].t_j,
                                                                                                                         self.e_rr[i_energy_data].r_g)
                        # check if gate voltage is given (GaN Transistor, SiC-MOSFET)
                        # if ture, add gate-voltage to label
                        if isinstance(self.e_rr[i_energy_data].v_g, (int, float)):
                            labelplot = labelplot + ", $v_{{g}}$ = {0} V".format(self.e_rr[i_energy_data].v_g)
                        # plot
                        plt.plot(self.e_rr[i_energy_data].graph_i_e[0], self.e_rr[i_energy_data].graph_i_e[1],
                                 label=labelplot)
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
                print("Diode reverse recovery energy i_e curves are not available for the chosen transistor")
                return None

        def plot_energy_data_r(self, buffer_req: bool = False):
            """
             Plots all diode energy r-e characteristic curves

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
                        labelplot = "$e_{{rr}}$: $v_{{supply}}$ = {0} V, $T_{{J}}$ = {1} °C, $I_{{ch}}$ = {2} A".format(self.e_rr[i_energy_data].v_supply, self.e_rr[i_energy_data].t_j,
                                                                                                                        self.e_rr[i_energy_data].i_x)
                        # check if gate voltage is given (GaN Transistor, SiC-MOSFET)
                        # if ture, add gate-voltage to label
                        if isinstance(self.e_rr[i_energy_data].v_g, (int, float)):
                            labelplot = labelplot + ", $v_{{g}}$ = {0} V".format(self.e_rr[i_energy_data].v_g)

                        # plot
                        plt.plot(self.e_rr[i_energy_data].graph_r_e[0], self.e_rr[i_energy_data].graph_r_e[1],
                                 label=labelplot)
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
                print("Diode reverse recovery energy r_e curves are not available for the chosen transistor")
                return None

        def plot_soa(self, buffer_req: bool = False):
            """
             A helper function to plot and convert safe operating region characteristic plots in raw data format.

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
            Collects diode data in form of dictionary for generating virtual datasheet

            :return: Diode data in form of dictionary
            :rtype: dict
            """
            diode_data = {}
            diode_data['plots'] = {'channel_plots': self.plot_all_channel_data(True), 'energy_plots': self.plot_energy_data(True), 'energy_plots_r': self.plot_energy_data_r(True), 'soa': self.plot_soa(True)}
            for attr in dir(self):
                if attr == 'thermal_foster':
                    diode_data.update(getattr(self, attr).collect_data())
                elif not callable(getattr(self, attr)) and not attr.startswith("__") and not \
                        isinstance(getattr(self, attr), (list, np.ndarray, dict)) and (not getattr(self, attr) is None) and not getattr(self, attr) == "":
                    diode_data[attr.capitalize()] = getattr(self, attr)
            return diode_data

    class LinearizedModel:
        """Contains data for a linearized Switch/Diode depending on given operating point. Operating point specified by
        t_j, i_channel and (not for all diode types) v_g."""
        t_j: float  #: Junction temperature of diode\switch. Units in K  (Mandatory key)
        v_g: Optional[float]  #: Gate voltage of switch or diode. Units in V (Mandatory for Switch, Optional for some Diode types)
        i_channel: float  #: Channel current of diode\switch. Units in A (Mandatory key)
        r_channel: float  #: Channel resistance of diode\switch. Units in Ohm (Mandatory key)
        v0_channel: float  #: Channel voltage of diode\switch. Unis in V (Mandatory key)

        def __init__(self, args):
            """
            Initialization method for linearizedmodel object

            :param args: arguments to passed for initialization
            """
            self.t_j = args.get('t_j')
            self.v_g = args.get('v_g')
            self.i_channel = args.get('i_channel')
            self.r_channel = args.get('r_channel')
            self.v0_channel = args.get('v0_channel')

        def convert_to_dict(self) -> dict:
            """
            The method converts LinearizedModel object into dict datatype

            :return: LinearizedModel object of dict type
            :rtype: dict
            """
            d = dict(vars(self))
            return d

    class ChannelData:
        """Contains channel V-I data for either switch or diode. Data is given for only one junction temperature t_j.
        For different temperatures: Create additional ChannelData-objects and store them as a list in the respective
        Diode- or Switch-object.
        This data can be used to linearize the transistor at a specific operating point """

        # # Test condition: Must be given as scalar. Create additional objects for different temperatures.
        t_j: float  #: Junction temperature of switch\diode. (Mandatory key)
        v_g: float  #: Switch: Mandatory key, Diode: optional (standard diode useless, for GaN 'diode' necessary
        # Dataset: Represented as a 2xm Matrix where row 1 is the voltage and row 2 the current.
        graph_v_i: npt.NDArray[np.float64]  #: Represented as a numpy 2D array where row 1 is the voltage and row 2 the current. Units of Row 1 = V; Row 2 = A (Mandatory key)

        def __init__(self, args):
            """
            Initialization method for ChannelData object

            :param args: arguments to be passed for initialization
            """
            # Validity of args is checked in the constructor of Diode/Switch class and thus does not need to be
            # checked again here.
            self.t_j = args.get('t_j')
            self.graph_v_i = args.get('graph_v_i')
            self.v_g = args.get('v_g')

        def convert_to_dict(self) -> dict:
            """
            The method converts ChannelData object into dict datatype

            :return: ChannelData object of dict type
            :rtype: dict
            """
            d = dict(vars(self))
            for att_key in d:
                if isinstance(d[att_key], np.ndarray):
                    d[att_key] = d[att_key].tolist()
            return d

        def plot_graph(self) -> None:
            """
            Plots the channel curve v_i characteristics called by using any ChannelData object

            :return: Respective plots are displayed
            :rtype: None
            """
            plt.figure()
            label = f"v_g = {self.v_g} V, t_j = {self.t_j} °C"
            plt.plot(self.graph_v_i[0], self.graph_v_i[1], label=label)
            plt.legend()
            plt.grid()
            plt.xlabel('Voltage in V')
            plt.ylabel('Current in A')
            plt.show()

    class VoltageDependentCapacitance:
        """Contains graph_v_c data for transistor class. Data is given for only one junction temperature t_j.
        For different temperatures: Create additional VoltageDependentCapacitance-objects and store them as a list in the transistor-object.
        """
        # # Test condition: Must be given as scalar. Create additional objects for different temperatures.
        t_j: float  #: Junction temperature (Mandatory key)
        # Dataset: Represented as a 2xm Matrix where row 1 is the voltage and row 2 the capacitance.
        graph_v_c: npt.NDArray[np.float64]  #: Represented as a 2D numpy array where row 1 is the voltage and row 2 the capacitance. Units of Row 1 = V; Row 2 = A  (Mandatory key)

        def __init__(self, args):
            """
            Initialization method for VoltageDependentCapacitance object

            :param args: arguments to be passed for initialization
            """
            # Validity of args is checked in the constructor of Diode/Switch class and thus does not need to be
            # checked again here.
            self.t_j = args.get('t_j')
            self.graph_v_c = args.get('graph_v_c')

        def convert_to_dict(self) -> dict:
            """
            The method converts VoltageDependentCapacitance object into dict datatype

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
            Plots the voltage dependant capacitance graph_v_c of the VoltageDependentCapacitance object. Also attaches the plot to figure axes for the purpose virtual datasheet if ax argument is specified

            :param ax: figure axes for making the graph_v_c plot in virtual datasheet
            :param label: label of the plot for virtual datasheet plot

            :return: Respective plots are displayed
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

    class SwitchEnergyData:
        """
        - Contains switching energy data for either switch or diode. The type of Energy (E_on, E_off or E_rr) is already implicitly specified by how the respective objects of this class are used in a Diode- or Switch-object.
        - For each set (e.g. every curve in the datasheet) of switching energy data a separate object should be created.
        - This also includes the reference values in a datasheet given without a graph. (Those are considered as data sets with just a single data point.)
        - Data sets with more than one point are given as graph_i_e with an r_g parameter or as graph_r_e with an i_x parameter.
        - Unused parameters or datasets should be left empty.
        - Which of these cases (single point, E vs I dataset, E vs R dataset) is valid for the current object also needs to be specified by the dataset_type-property.
        """

        # Type of the dataset:
        # single: e_x, r_g, i_x are scalars. Given e.g. by a table in the datasheet.
        # graph_r_e: r_e is a 2-dim numpy array with two rows. i_x is a scalar. Given e.g. by an E vs R graph.
        # graph_i_e: i_e is a 2-dim numpy array with two rows. r_g is a scalar. Given e.g. by an E vs I graph.
        dataset_type: str  #: Single, graph_r_e, graph_i_e (Mandatory key)
        # Additional measurement information.
        comment: Optional[str]  #: Comment for additional information e.g. on who made these measurements
        measurement_date: Optional["datetime.datetime"]  #: Specifies the date and time at which the measurement was done.
        measurement_testbench: Optional[str]  #: Specifies the testbench used for the measurement.
        commutation_device: Optional[str]  #: Second device used in half-bridge test condition
        # Test conditions. These must be given as scalars. Create additional objects for e.g. different temperatures.
        t_j: float  #: Junction temperature. Units in °C (Mandatory key)
        v_supply: float  #: Supply voltage. Units in V (Mandatory key)
        v_g: float  #: Gate voltage. Units in V (Mandatory key)
        v_g_off: Optional[float]  #: Gate voltage for turn off. Units in V
        load_inductance: Optional[float]  #: Load inductance. Units in µH
        commutation_inductance: Optional[float]  #: Commutation inductance. Units in µH
        # Scalar dataset-parameters. Some of these can be 'None' depending on the dataset_type.
        e_x: Optional[float]  #: Scalar dataset-parameter - switching energy. Units in J
        r_g: Optional[float]  #: Scalar dataset-parameter - gate resistance. Units in Ohm
        i_x: Optional[float]  #: Scalar dataset-parameter - current rating. Units in A
        # Dataset. Only one of these is allowed. The other should be 'None'.
        graph_i_e: Optional[npt.NDArray[np.float64]]  #: Units for Row 1 = A; Row 2 = J
        graph_r_e: Optional[npt.NDArray[np.float64]]  #: Units for Row 1 = Ohm; Row 2 = J

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
            Initialization method for VoltageDependentCapacitance object

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
                self.graph_i_e = None
                self.graph_r_e = None
            elif self.dataset_type == 'graph_i_e':
                self.e_x = None
                self.r_g = args.get('r_g')
                self.i_x = None
                self.graph_i_e = args.get('graph_i_e')
                self.graph_r_e = None
            elif self.dataset_type == 'graph_r_e':
                self.e_x = None
                self.r_g = None
                self.i_x = args.get('i_x')
                self.graph_i_e = None
                self.graph_r_e = args.get('graph_r_e')

        def convert_to_dict(self) -> dict:
            """
              The method converts SwitchEnergyData object into dict datatype

              :return: SwitchEnergyData object of dict type
              :rtype: dict
              """
            d = dict(vars(self))
            for att_key in d:
                if isinstance(d[att_key], np.ndarray):
                    d[att_key] = d[att_key].tolist()
            return d

        def plot_graph(self) -> None:
            """
            Plots switch / diode energy curve characteristics (either from graph_i_e or graph_r_e dataset)

            :return: Respective plots are displayed
            :rtype: None
            """
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
            A method to copy the existing SwitchEnergyData object and create a new object of same type. Created to allow deep copy of object when using gecko exporter

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
            Transistor.isvalid_dict(args, 'SwitchEnergyData')
            return Transistor.SwitchEnergyData(args)

    class WP:
        """
         The WP class is intended for user calculations in Python. It is used to access transistor data in user-written programs.
         It allows the user to linearize the channel and store the result in transistor.wp. Switching loss curves can be stored
         for specific boundary conditions, so that the same variable is always accessed in the self-written program, regardless of the transistor.

        The class WP...

        - Always initialized as None.
        - Is always exported as None to .json or to the database.
        - Is a temporary workspace.
        """
        # type hints
        v_channel: Optional[float]
        r_channel: Optional[float]
        e_on: Optional[npt.NDArray[np.float64]]  #: Units: Row 1: A; Row 2: J
        e_off: Optional[npt.NDArray[np.float64]]  #: Units: Row 1: A; Row 2: J
        e_rr: Optional[npt.NDArray[np.float64]]  #: Units: Row 1: A; Row 2: J
        v_switching_ref: Optional[float]  #: Unit: V
        e_oss: Optional[npt.NDArray[np.float64]]  #: Units: Row 1: V; Row 2: J
        q_oss: Optional[npt.NDArray[np.float64]]  #: Units: Row 1: V; Row 2: C
        parallel_transistors: Optional[float]  #: Unit: Number

        def __init__(self):
            self.switch_v_channel = None
            self.switch_r_channel = None
            self.diode_v_channel = None
            self.diode_r_channel = None
            self.e_on = None
            self.e_off = None
            self.e_rr = None
            self.v_switching_ref = None
            self.e_oss = None
            self.q_oss = None
            self.parallel_transistors = None

    class EffectiveOutputCapacitance:
        """
        The class EffectiveOutputCapacitance is used to record energy related or time related output capacitance of the switch.
        """
        c_o: float  #: Value of the fixed output capacitance. Units in F
        v_gs: float  #: Gate to source voltage of the switch. Units in V
        v_ds: float  #: Drain to source voltage of the switch ex: V_DS = (0-400V) i.e v_ds=400 (max value, min assumed a 0). Units in V

        def __init__(self, args):
            """
            Initialization method for EffectiveOutputCapacitance object

            :param args: arguments to be passed for initialization
            """
            # Validity of args is checked in the constructor of Diode/Switch class and thus does not need to be
            # checked again here.
            self.c_o = args.get('c_o')
            self.v_gs = args.get('v_gs')
            self.v_ds = args.get('v_ds')

        def convert_to_dict(self) -> dict:
            """
            The method converts EffectiveOutputCapacitance object into dict datatype

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
            c_oss_related = {}
            skipIds = []
            for attr in dir(self):
                if attr not in skipIds and not callable(getattr(self, attr)) and not attr.startswith("__") and not isinstance(getattr(self, attr), (list, dict)) \
                        and (not getattr(self, attr) is None):
                    c_oss_related[attr.capitalize()] = getattr(self, attr)
            return c_oss_related

    class TemperatureDependResistance:
        """
        class to store temperature dependant resistance curve
        """
        i_channel: float  #: channel current at which the graph is recorded
        v_g: float  #: gate voltage
        dataset_type: str  #: curve datatype, can be either 't_r' or 't_factor'. 't_factor' is used to denote normalized gate curves
        graph_t_r: npt.NDArray[np.float64]  #: a 2D numpy array to store the temperature related channel on resistance
        r_channel_nominal: Optional[float]  #: a mandatory field if the dataset_type is 't_factor'

        def __init__(self, args):
            """
            Initialization method for TemperatureDependResistance object

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
            The method converts TemperatureDependResistance object into dict datatype

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
            Plots On resistance vs Junction temperature

            :param ax: figure axes to append the curves

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

    class GateChargeCurve:

        """ A class to hold gate charge characteristics of switch which is added as a optional attribute inside switch class"""

        v_supply: float  #: same as drain-to-source (v_ds)/ collector-emitter (v_ce) voltages
        t_j: float  #: junction temperature
        i_channel: float  #: channel current at which the graph is recorded
        i_g: Optional[float]  #: gate to source/emitter current
        graph_q_v: npt.NDArray[np.float64]  #: a 2D numpy array to store gate charge dependant on gate to source voltage

        def __init__(self, args):
            """
            Initialization method for GateChargeCurve object

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
            The method converts GateChargeCurve object into dict datatype

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
            Plots gate charge vs gate source/ gate emitter voltage of switch type mosfet and igbt respectively

            :param ax: figure axes to append the curves

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
        """ A class to hold safe operating area characteristics of transistor type which is added as a optional attribute inside transistor class"""

        t_c: Optional[float]  #: case temperature
        time_pulse: Optional[float]  #: applied pulse duration
        graph_i_v: npt.NDArray[np.float64]  #: a 2D numpy array to store SOA characteristics curves

        def __init__(self, args: dict):
            """
            Initialization method for SOA object

            :param args: arguments to be passed for initialization
            """
            # Validity of args is checked in the constructor of Transistor class and thus does not need to be
            # checked again here.
            self.time_pulse = args.get('time_pulse')
            self.t_c = args.get('t_c')
            self.graph_i_v = args.get('graph_i_v')

        def convert_to_dict(self) -> dict:
            """
            The method converts SOA object into dict datatype

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
            Plots drain current/reverse diode current vs drain-to-source voltage/diode applied reverse voltage of switch type mosfet/igbt

            :param ax: figure axes to append the curves

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

    def parallel_transistors(self, count_parallels: int = 2) -> Transistor:
        """

        Connect [count_parallels] transistors in parallel
        The returned transistor object behaves like a single transistor.

        - name will be modified by adding _[count_parallels]_parallel
        - channel characteristics will be modified
        - e_on/e_off/e_rr characteristics will be modified
        - thermal behaviour will be modified

        :param count_parallels: count of parallel transistors of same type, default = 2
        :type count_parallels: int

        :return: transistor object with parallel transistors
        :rtype: Transistor

        :Example:

        >>> import transistordatabase as tdb
        >>> transistor = tdb.load('Infineon_FF200R12KE3')
        >>> parallel_transistorobject = transistor.parallel_transistors(3)

        """
        transistor_dict = self.convert_to_dict()

        # modify transistor elements
        transistor_dict['name'] = f"{transistor_dict['name']}_{count_parallels}_parallel"
        transistor_dict['r_th_switch_cs'] = transistor_dict['r_th_switch_cs'] / count_parallels
        transistor_dict['r_th_diode_cs'] /= count_parallels
        transistor_dict['r_th_cs'] /= count_parallels
        transistor_dict['i_abs_max'] = transistor_dict['i_abs_max'] * count_parallels
        transistor_dict['i_cont'] = transistor_dict['i_cont'] * count_parallels
        transistor_dict['c_iss'] = transistor_dict['c_iss'] * count_parallels
        transistor_dict['c_oss'] *= count_parallels
        transistor_dict['c_rss'] *= count_parallels

        # modify switch dict
        for channel_dict in transistor_dict['switch']['channel']:
            if 'graph_v_i' in channel_dict:
                channel_dict['graph_v_i'][1] = [y * count_parallels for y in channel_dict['graph_v_i'][1]]
        for e_on_dict in transistor_dict['switch']['e_on']:
            if e_on_dict['dataset_type'] == 'graph_i_e':
                e_on_dict['graph_i_e'][0] = [y * count_parallels for y in e_on_dict['graph_i_e'][0]]
                e_on_dict['graph_i_e'][1] = [y * count_parallels for y in e_on_dict['graph_i_e'][1]]
            if e_on_dict['dataset_type'] == 'graph_r_e':
                e_on_dict['graph_r_e'][1] = [y * count_parallels for y in e_on_dict['graph_r_e'][1]]
        for e_off_dict in transistor_dict['switch']['e_off']:
            if e_off_dict['dataset_type'] == 'graph_i_e':
                e_off_dict['graph_i_e'][0] = [y * count_parallels for y in e_off_dict['graph_i_e'][0]]
                e_off_dict['graph_i_e'][1] = [y * count_parallels for y in e_off_dict['graph_i_e'][1]]
            if e_off_dict['dataset_type'] == 'graph_r_e':
                e_off_dict['graph_r_e'][1] = [y * count_parallels for y in e_off_dict['graph_r_e'][1]]
        # modify diode dict
        for x in transistor_dict['diode']['channel']:
            x['graph_v_i'][1] = [y * count_parallels for y in x['graph_v_i'][1]]
        for e_rr_dict in transistor_dict['diode']['e_rr']:
            if e_rr_dict['dataset_type'] == 'graph_i_e':
                e_rr_dict['graph_i_e'][0] = [y * count_parallels for y in e_rr_dict['graph_i_e'][0]]
                e_rr_dict['graph_i_e'][1] = [y * count_parallels for y in e_rr_dict['graph_i_e'][1]]
            if e_rr_dict['dataset_type'] == 'graph_r_e':
                e_rr_dict['graph_r_e'][1] = [y * count_parallels for y in e_rr_dict['graph_r_e'][1]]

        # modify switch thermal dict
        transistor_dict['switch']['thermal_foster']['r_th_total'] /= count_parallels
        transistor_dict['switch']['thermal_foster']['r_th_vector'] = None if \
            transistor_dict['switch']['thermal_foster']['r_th_vector'] is None else [x / count_parallels for x in
                                                                                     transistor_dict['switch'][
                                                                                         'thermal_foster']['r_th_vector']]
        transistor_dict['switch']['thermal_foster']['c_th_total'] = None if transistor_dict['switch']['thermal_foster'][
                                                                                'c_th_total'] is None else \
            transistor_dict['switch']['thermal_foster']['c_th_total'] / count_parallels
        transistor_dict['switch']['thermal_foster']['c_th_vector'] = None if \
            transistor_dict['switch']['thermal_foster']['c_th_vector'] is None else [x / count_parallels for x in
                                                                                     transistor_dict['switch'][
                                                                                         'thermal_foster']['c_th_vector']]

        if transistor_dict['switch']['thermal_foster']['graph_t_rthjc'] is not None:
            transistor_dict['switch']['thermal_foster']['graph_t_rthjc'][1] = [x / count_parallels for x in
                                                                               transistor_dict['switch'][
                                                                                   'thermal_foster'][
                                                                                   'graph_t_rthjc'][1]]
        # modify diode thermal dict
        transistor_dict['diode']['thermal_foster']['r_th_total'] /= count_parallels
        transistor_dict['diode']['thermal_foster']['r_th_vector'] = None if transistor_dict['diode']['thermal_foster'][
                                                                                'r_th_vector'] is None else [
            x / count_parallels for x in transistor_dict['diode']['thermal_foster']['r_th_vector']]
        transistor_dict['diode']['thermal_foster']['c_th_total'] = None if transistor_dict['diode']['thermal_foster'][
                                                                               'c_th_total'] is None else \
            transistor_dict['diode']['thermal_foster']['c_th_total'] / count_parallels
        transistor_dict['diode']['thermal_foster']['c_th_vector'] = None if transistor_dict['diode']['thermal_foster'][
                                                                                'c_th_vector'] is None else [
            x / count_parallels for x in transistor_dict['diode']['thermal_foster']['c_th_vector']]

        if transistor_dict['diode']['thermal_foster']['graph_t_rthjc'] is not None:
            transistor_dict['diode']['thermal_foster']['graph_t_rthjc'][1] = [x / count_parallels for x in
                                                                              transistor_dict['diode'][
                                                                                  'thermal_foster'][
                                                                                  'graph_t_rthjc'][1]]

        return convert_dict_to_transistor_object(transistor_dict)

    def validate_transistor(self) -> dict:
        """
        A helper function for plecs exporter. Checks if curve characteristics and thermal network parameters of both switch and diode to be None or empty
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
         Collects the available information of switch and diode from transistor object and passes it to plecs_exporter(..) for generating the diode and switch .xml files

        :param channel_recheck: if set to True, collects the channel and energy curve characteristics at nearest gate voltage if the given gate voltages are not found
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
                        transistor_dict['author'], transistor_dict['datasheet_date'])
                    , "Datasheet Link : {0}".format(re.sub(r'&', '&amp;', transistor_dict['datasheet_hyperlink'])),
                    "File generated : {0}".format(datetime.datetime.today()),
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
                    for key, value in plecs_transistor['TurnOnLoss']['Energy'].items():
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
                    for key, value in plecs_transistor['TurnOffLoss']['Energy'].items():
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
            print(e.args[0], e.em[e.args[0]] + '.scl')
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
                        transistor_dict['author'], transistor_dict['datasheet_date'])
                    , "Datasheet Link : {0}".format(re.sub(r'&', '&amp;', transistor_dict['datasheet_hyperlink'])),
                    "File generated : {0}".format(datetime.datetime.today()),
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
                    for key, value in plecs_diode['TurnOffLoss']['Energy'].items():
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
            print(e.args[0], e.em[e.args[0]] + '.scl')
        return plecs_transistor if plecs_transistor is not None and 'Channel' in plecs_transistor['ConductionLoss'] \
                   else None, plecs_diode if plecs_diode is not None and 'Channel' in plecs_diode['ConductionLoss'] \
                   else None

    class RawMeasurementData:
        """
                - Contains RAW measurement data. e.g. for voltage and current graphs from a double pulse test.
                """

        # Type of the dataset:
        # dpt_u_i: U/t I/t graph from double pulse measurements
        dataset_type: str  #: e.g. dpt_u_i (Mandatory key)
        dpt_on_vds: Optional[List[npt.NDArray[np.float64]]]  #: measured Vds data at turn on event. Units in V and s
        dpt_on_id: Optional[List[npt.NDArray[np.float64]]]  #: measured Id data at turn on event. Units in A and s
        dpt_off_vds: Optional[List[npt.NDArray[np.float64]]]  #: measured Vds data at turn off event. Units in V and s
        dpt_off_id: Optional[List[npt.NDArray[np.float64]]]  #: measured Vds data at turn off event. Units in A and s
        measurement_date: Optional["datetime.datetime"]  #: Specifies the measurements date and time
        measurement_testbench: Optional[str]  #: Specifies the testbench used for the measurement.
        commutation_device: Optional[str]  #: Second device used in half-bridge test condition
        comment: Optional[str]  #: Comment for additional information e.g. on who made these measurements
        # Test conditions. These must be given as scalars. Create additional objects for e.g. different temperatures.
        t_j: Optional[float]  #: Junction temperature. Units in °C
        v_supply: Optional[float]  #: Supply voltage. Units in V
        v_g: Optional[float]  #: Gate voltage. Units in V
        v_g_off: Optional[float]  #: Gate voltage for turn off. Units in V
        r_g: Optional[List[npt.NDArray[np.float64]], float]  #: gate resistance. Units in Ohm
        r_g_off: Optional[List[npt.NDArray[np.float64]], float]  #: gate resistance. Units in Ohm
        load_inductance: Optional[float]  #: Load inductance. Units in µH
        commutation_inductance: Optional[float]  #: Commutation inductance. Units in µH

        def __init__(self, args):
            """
            Initialization method for RawMeasurementData object

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
            The method converts RawMeasurementData object into dict datatype

            :return: Switch object of dict type
            :rtype: dict
            """
            d = dict(vars(self))
            d['dpt_on_vds'] = [c.tolist() for c in self.dpt_on_vds]
            d['dpt_on_id'] = [c.tolist() for c in self.dpt_on_id]
            d['dpt_off_vds'] = [c.tolist() for c in self.dpt_off_vds]
            d['dpt_off_id'] = [c.tolist() for c in self.dpt_off_id]
            return d

        def dpt_calculate_energies(self, integration_interval: str, dataset_type: str, energies: str):
            """
                Imports double pulse measurements and calculates switching losses to each given working point.

                [1] options for the integration interval are based on following paper:
                Link: https://ieeexplore.ieee.org/document/8515553

                :param integration_interval: calculation standards for switching losses
                :type integration_interval: str
                :param dataset_type: defines what measurement set should should be calculated
                :type dataset_type: str
                :param energies: defines which switching energies should be calculated
                :type energies: str


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

            e_off_meas = Union[dict, None]
            e_on_meas = Union[dict, None]
            label_x_plot = 'Id / A'

            if dataset_type == 'graph_r_e':
                label_x_plot = 'Ron / Ohm'

            if energies == 'E_off' or energies == 'both':

                sample_point = 0
                measurement_points = len(self.dpt_off_id)
                e_off = []

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

                    time_correction = 0

                    ##############################
                    # Integrate the power with predefined integration limits
                    ##############################
                    while id_temp[i - time_correction, 1] >= (id_avg_max * off_is_limit):
                        e_off_temp = e_off_temp + (vds_temp[i, 1] * id_temp[i - time_correction, 1] * sample_interval)
                        i += 1

                    if dataset_type == 'graph_r_e':
                        e_off.append([self.r_g[sample_point], e_off_temp])
                    else:
                        e_off.append([id_avg_max, e_off_temp])

                    sample_point += 1

                e_off_0 = [item[0] for item in e_off]
                e_off_1 = [item[1] for item in e_off]

                e_off_meas = {'dataset_type': dataset_type,
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
                              'i_x': id_avg_max}

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

            if energies == 'E_on' or energies == 'both':

                sample_point = 0
                measurement_points = len(self.dpt_on_id)
                e_on = []

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

                    time_correction = 0
                    ##############################
                    # Integrate the power with predefined integration limits
                    ##############################
                    while vds_temp[i + time_correction, 1] >= (vds_avg_max * on_vds_limit):
                        e_on_temp = e_on_temp + (vds_temp[i + time_correction, 1] * id_temp[i, 1] * sample_interval)
                        i += 1

                    if dataset_type == 'graph_r_e':
                        e_on.append([self.r_g[sample_point], e_on_temp])
                    else:
                        e_on.append([id_avg_max, e_on_temp])

                    sample_point += 1

                e_on_0 = [item[0] for item in e_on]
                e_on_1 = [item[1] for item in e_on]

                e_on_meas = {'dataset_type': dataset_type,
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
                             'i_x': id_avg_max}

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

    def add_dpt_measurement(self, measurement_data):
        """
        This method adds new measurement data to the transistor object and saves changes to the database.

        :param measurement_data: Dict of data you want to add to given attribute.
        :type measurement_data: dict
        """

        collection = connect_local_TDB()
        transistor_id = {'_id': self._id}

        if measurement_data['e_off_meas'] is not None:
            if isinstance(measurement_data.get('e_off_meas'), list):
                for dataset in measurement_data.get('e_off_meas'):
                    try:
                        if Transistor.isvalid_dict(dataset, 'SwitchEnergyData'):
                            self.switch.e_off_meas.append(Transistor.SwitchEnergyData(dataset))
                    # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                    except KeyError as error:
                        dict_list = measurement_data.get('e_off_meas')
                        if not error.args:
                            error.args = ('',)  # This syntax is necessary because error.args is a tuple
                        error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                      f"Switch-SwitchEnergyData dictionaries for e_off_meas: ",) + error.args
                        raise
            elif Transistor.isvalid_dict(measurement_data.get('e_off_meas'), 'SwitchEnergyData'):
                self.switch.e_off_meas.append(Transistor.SwitchEnergyData(measurement_data.get('e_off_meas')))

            transistor_dict = self.switch.convert_to_dict()
            new_value = {'$set': {'switch.e_off_meas': transistor_dict['e_off_meas']}}
            collection.update_one(transistor_id, new_value)

        if measurement_data['e_on_meas'] is not None:
            if isinstance(measurement_data.get('e_on_meas'), list):
                # Loop through list and check each dict for validity. Only create SwitchEnergyData objects from
                # valid dicts. 'None' and empty dicts are ignored.
                for dataset in measurement_data.get('e_on_meas'):
                    try:
                        if Transistor.isvalid_dict(dataset, 'SwitchEnergyData'):
                            self.switch.e_on_meas.append(Transistor.SwitchEnergyData(dataset))
                    # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                    except KeyError as error:
                        dict_list = measurement_data.get('e_on_meas')
                        if not error.args:
                            error.args = ('',)  # This syntax is necessary because error.args is a tuple
                        error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] in list of "
                                      f"Switch-SwitchEnergyData dictionaries for e_on_meas: ",) + error.args
                        raise
            elif Transistor.isvalid_dict(measurement_data.get('e_on_meas'), 'SwitchEnergyData'):
                # Only create SwitchEnergyData objects from valid dicts
                self.switch.e_on_meas.append(Transistor.SwitchEnergyData(measurement_data.get('e_on_meas')))

            transistor_dict = self.switch.convert_to_dict()
            new_value = {'$set': {'switch.e_on_meas': transistor_dict['e_on_meas']}}
            collection.update_one(transistor_id, new_value)

        if measurement_data['raw_measurement_data'] is not None:
            if isinstance(measurement_data.get('raw_measurement_data'), list):
                # Loop through list and check each dict for validity. Only create RawMeasurementData objects from
                # valid dicts. 'None' and empty dicts are ignored.
                for dataset in measurement_data.get('raw_measurement_data'):
                    try:
                        if Transistor.isvalid_dict(dataset, 'RawMeasurementData'):
                            self.raw_measurement_data.append(Transistor.RawMeasurementData(dataset))
                    # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                    except KeyError as error:
                        dict_list = measurement_data.get('raw_measurement_data')
                        if not error.args:
                            error.args = ('',)  # This syntax is necessary because error.args is a tuple
                        error.args = (f"KeyError occurred for index [{str(dict_list.index(dataset))}] "
                                      f"in list of raw_measurement_data "f"dictionaries: ",) + error.args
                        raise
            elif Transistor.isvalid_dict(measurement_data.get('raw_measurement_data'), 'RawMeasurementData'):
                # Only create RawMeasurementData objects from valid dicts
                self.raw_measurement_data.append(
                    Transistor.RawMeasurementData(measurement_data.get('raw_measurement_data')))

            transistor_dict = self.convert_to_dict()
            new_value = {'$set': {'raw_measurement_data': transistor_dict['raw_measurement_data']}}
            collection.update_one(transistor_id, new_value)

    def add_soa_data(self, soa_data: [dict, list], switch_type: str, clear: bool = False):
        """
        A transistor method to add the SOA class object to the loaded transistor.switch.soa or transistor.diode.soa attribute.
        .. note:: Transistor object must be loaded first before calling this method

        :param soa_data: argument represents the soa dictionaries objects that needs to be added to transistor switch or diode object
        :type soa_data: dict or list
        :param switch_type: either switch or diode object on which the provided soa_data needed to be appended
        :type switch_type: str
        :param clear: set to true if to clear the existing soa curves on the selected transistor switch or diode object
        :type clear: bool

        :return: updated transistor switch or diode object with added soa characteristics
        """
        soa_list = []
        transistor_id = {'_id': self._id}

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
        for index, dataset in enumerate(soa_list):
            for key, item in dataset.items():
                if isinstance(dataset[key], list):
                    dataset[key] = np.array(dataset[key])

        # validating the dict and checking for duplicates
        if isinstance(soa_data, list):
            for i, soa_data_item in enumerate(soa_data):
                try:
                    if Transistor.isvalid_dict(soa_data_item, 'SOA') and check_duplicates(soa_list, soa_data_item):
                        soa_list.append(soa_data_item)
                # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                except KeyError as error:
                    if not error.args:
                        error.args = ('',)  # This syntax is necessary because error.args is a tuple
                    error.args = (f"KeyError occurred for index [{str(i)}] in list of "
                                  f"Transistor-soa dictionary: ",) + error.args
                    raise
        elif Transistor.isvalid_dict(soa_data, 'SOA') and check_duplicates(soa_list, soa_data):
            soa_list.append(soa_data)

        # appending the list to the transistor object
        if len(soa_list) > init_length:
            collection = connect_local_TDB()
            if switch_type == 'switch':
                self.switch.soa.clear()
                for soa_item in soa_list:
                    self.switch.soa.append(Transistor.SOA(soa_item))
                    soa_item['graph_i_v'] = soa_item['graph_i_v'].tolist()
                soa_object = {'$set': {'switch.soa': soa_list}}
                collection.update_one(transistor_id, soa_object)
            elif switch_type == 'diode':
                self.diode.soa.clear()
                for soa_item in soa_list:
                    self.diode.soa.append(Transistor.SOA(soa_item))
                    soa_item['graph_i_v'] = soa_item['graph_i_v'].tolist()
                soa_object = {'$set': {'diode.soa': soa_list}}
                collection.update_one(transistor_id, soa_object)
            print('Updated successfully!')
        else:
            print('No new item to add!')

    def add_gate_charge_data(self, charge_data: [dict, list], clear: bool = False):
        """
        A transistor method to add the GateChargeCurve class objects to the loaded transistor.switch.charge_curve attribute.
        .. note:: Transistor object must be loaded first before calling this method

        :param charge_data: argument represents the gatechargecurve dictionaries objects that needs to be added to transistor object
        :type charge_data: dict or list
        :param clear: set to true if to clear the existing gatechargecurve curves on the transistor object
        :type clear: bool

        :return: updated transistor object with added gate charge characteristics
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
        for index, dataset in enumerate(charge_list):
            for key, item in dataset.items():
                if isinstance(dataset[key], list):
                    dataset[key] = np.array(dataset[key])

        # validating the dict and checking for duplicates
        if isinstance(charge_data, list):
            for i, charge_data_item in enumerate(charge_data):
                try:
                    if Transistor.isvalid_dict(charge_data_item, 'GateChargeCurve') and check_duplicates(charge_list, charge_data_item):
                        charge_list.append(charge_data_item)
                # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                except KeyError as error:
                    if not error.args:
                        error.args = ('',)  # This syntax is necessary because error.args is a tuple
                    error.args = (f"KeyError occurred for index [{str(i)}] in list of "
                                  f"Transistor-switch-gatecharge dictionary: ",) + error.args
                    raise
        elif Transistor.isvalid_dict(charge_data, 'GateChargeCurve') and check_duplicates(charge_list, charge_data):
            charge_list.append(charge_data)

        # appending the list to the transistor object
        if len(charge_list) > init_length:
            self.switch.charge_curve.clear()
            for charge_item in charge_list:
                self.switch.charge_curve.append(Transistor.GateChargeCurve(charge_item))
                charge_item['graph_q_v'] = charge_item['graph_q_v'].tolist()
            charge_object = {'$set': {'switch.charge_curve': charge_list}}
            collection = connect_local_TDB()
            collection.update_one(transistor_id, charge_object)
            print('Updated successfully!')
        else:
            print('No new item to add!')

    def add_temp_depend_resis_data(self, r_channel_data: [dict, list], clear: bool = False):
        """
        A transistor method to add the TemperatureDependResistance class objects to the loaded transistor.switch.r_channel_th attribute.
        .. note:: Transistor object must be loaded first before calling this method

        :param r_channel_data: argument represents the TemperatureDependResistance dictionaries objects that needs to be added to transistor.switch.r_channel_th object
        :type r_channel_data: dict or list
        :param clear: set to true if to clear the existing r_channel_th curves on the transistor object
        :type clear: bool

        :return: updated transistor object with added gate charge characteristics
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
        for index, dataset in enumerate(r_channel_list):
            for key, item in dataset.items():
                if isinstance(dataset[key], list):
                    dataset[key] = np.array(dataset[key])

        # validating the dict and checking for duplicates
        if isinstance(r_channel_data, list):
            for index, r_channel_data_item in enumerate(r_channel_data):
                try:
                    if Transistor.isvalid_dict(r_channel_data_item, 'TemperatureDependResistance') and check_duplicates(r_channel_list, r_channel_data_item):
                        r_channel_list.append(r_channel_data_item)
                # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                except KeyError as error:
                    if not error.args:
                        error.args = ('',)  # This syntax is necessary because error.args is a tuple
                    error.args = (f"KeyError occurred for index [{str(index)}] in list of "
                                  f"Transistor-switch-r_channel_th dictionary: ",) + error.args
                    raise
        elif Transistor.isvalid_dict(r_channel_data, 'TemperatureDependResistance') and check_duplicates(r_channel_list, r_channel_data):
            r_channel_list.append(r_channel_data)

        # appending the list to the transistor object
        if len(r_channel_list) > init_length:
            self.switch.r_channel_th.clear()
            for r_channel_item in r_channel_list:
                self.switch.r_channel_th.append(Transistor.TemperatureDependResistance(r_channel_item))
                r_channel_item['graph_t_r'] = r_channel_item['graph_t_r'].tolist()
            r_channel_object = {'$set': {'switch.r_channel_th': r_channel_list}}
            collection = connect_local_TDB()
            collection.update_one(transistor_id, r_channel_object)
            print('Updated successfully!')
        else:
            print('No new item to add!')


def check_duplicates(current_items: list[dict], item_to_append: dict) -> bool:
    """
    A helper method to check if the item being added already exists in the list

    :param current_items: list of particular class object converted to dictionaries using which the checks are conducted
    :type current_items: list(dict)
    :param item_to_append: the object dict that needs to be appended
    :type item_to_append: dict

    :return: True if the added item is not duplicate
    :rtype: bool
    """
    if len(current_items) == 0:
        return True
    else:
        for index, c_item in enumerate(current_items):
            count = 0
            for key, value in c_item.items():
                if isinstance(item_to_append[key], np.ndarray):
                    count = count + 1 if c_item[key].tolist() == item_to_append[key].tolist() else count
                elif c_item[key] == item_to_append[key]:
                    count += 1
            if count == len(c_item):
                msg = "Duplicate object detected: already present at index {0} of {1} object" .format(index, type(current_items).__name__)
                print(msg)
                return False
        return True


def export_all_datasheets(filter_list: list = None):
    """
    A method to export all the available transistor data present in the local mongoDB database

    :param filter_list: a list of transistor names that needs to be exported in specific
    :type filter_list: list

    :return: None
    """
    transistor_list = print_TDB()
    filtered_list = list()
    html_list = list()
    pdf_name_list = list()
    paths_list = list()
    if filter_list is not None:
        for item in filter_list:
            if item not in transistor_list:
                print("{0} transistor is not present in database".format(item))
            else:
                filtered_list.append(item)
    else:
        filtered_list = transistor_list
    if len(filtered_list) > 0:
        for transistor_str in filtered_list:
            transistor = load(transistor_str)
            html_list.append(transistor.export_datasheet(build_collection=True))
            pdf_name_list.append(transistor.name + ".pdf")
            paths_list.append(os.path.join(os.getcwd(), transistor.name + ".pdf"))
        html_to_pdf(html_list, pdf_name_list, paths_list)
    else:
        print("Nothing to export, please recheck inputs")


def html_to_pdf(html: Union[list, str], name: Union[list, str], path: Union[list, str]):
    """
    A helper method to convert the generated html document to pdf file using qt WebEngineWidgets tool

    :param html: html string that needs to be converted to pdf file
    :type html: str or list
    :param name: name of the file that will be saved as (basically the transistor name)
    :type name: str or list
    :param path: corresponding path where the file needs to be stored
    :type path: str or list

    :return: saves the html string to pdf file format
    """
    app = QtWidgets.QApplication(sys.argv)
    page = QtWebEngineWidgets.QWebEnginePage()
    path_item = str()
    name_item = str()
    html_item = str()

    def fetch_next():
        try:
            nonlocal html_item, name_item, path_item
            html_item, name_item, path_item = next(html_and_paths)
        except StopIteration:
            return False
        else:
            page.setHtml(html_item)
        return True

    def handle_print_finished(filepath, status):
        print(f"Export virtual datasheet {name_item} to {pathlib.Path.cwd().as_uri()}")
        print(f"Open Datasheet here: {pathlib.Path(filepath).as_uri()}")
        if not fetch_next():
            app.quit()

    def handle_load_finished(status):
        if status:
            nonlocal path_item
            page.printToPdf(path_item)
        else:
            print("Failed")
            app.quit()

    page.pdfPrintingFinished.connect(handle_print_finished)
    page.loadFinished.connect(handle_load_finished)
    if isinstance(html, list):
        html_and_paths = iter(zip(html, name, path))
    else:
        html_and_paths = iter(zip([html], [name], [path]))
    fetch_next()
    app.exec_()


def gen_exp_func(order: int):
    """
    A helper function to calc_thermal_params method. Generates the required ordered function for curve fitting

    :param order: order of the function for approximation  with n ranging from 1 to 5
    :type order: int

    :return: A n ordered polynomial
    """
    if order == 1:
        return lambda t, rn, tau: rn * (1 - np.exp(-t / tau))
    elif order == 2:
        return lambda t, rn, tau, rn2, tau2: rn * (1 - np.exp(-t / tau)) + rn2 * (1 - np.exp(-t / tau2))
    elif order == 3:
        return lambda t, rn, tau, rn2, tau2, rn3, tau3: rn * (1 - np.exp(-t / tau)) + rn2 * (1 - np.exp(-t / tau2)) + rn3 * (1 - np.exp(-t / tau3))
    elif order == 4:
        return lambda t, rn, tau, rn2, tau2, rn3, tau3, rn4, tau4: rn * (1 - np.exp(-t / tau)) + rn2 * (1 - np.exp(-t / tau2)) + rn3 * (1 - np.exp(-t / tau3)) + rn4 * (1 - np.exp(-t / tau4))
    elif order == 5:
        return lambda t, rn, tau, rn2, tau2, rn3, tau3, rn4, tau4, rn5, tau5: rn * (1 - np.exp(-t / tau)) + rn2 * (1 - np.exp(-t / tau2)) + rn3 * (1 - np.exp(-t / tau3)) + rn4 * (1 - np.exp(-t / tau4)) + rn5 * (1 - np.exp(-t / tau5))


def get_xml_data(file: str) -> dict:
    """
    A helper function to import_xml_data method to extract the xml file data i.e turn on/off energies, channel data, foster thermal data.

    :param file: name of the xml file to be read
    :type file: str

    :raises ImportError: If the provide files doesn't relate to XML file format

    :return: dictionaries holding turn on/off energies, channel data, foster thermal data
    :rtype: dict

    """
    namespaces = {'plecs': 'http://www.plexim.com/xml/semiconductors/'}
    etree = et.parse(file)
    root = etree.getroot()
    package = root.find('plecs:Package', namespaces)
    info = package.attrib
    v_on, v_off = (0, 12) if info['class'] == 'Diode' else (12, 0)
    are_variables_defined = package.find('plecs:Variables', namespaces).text
    if not are_variables_defined:
        semiconductor_data = package.find('plecs:SemiconductorData', namespaces)
        energy_on_list = []
        energy_off_list = []
        channel_list = []
        foster_args = {}
        for character_node in semiconductor_data:
            if character_node.tag == '{' + namespaces['plecs'] + '}' + 'TurnOnLoss' and character_node.find('plecs:ComputationMethod', namespaces).text.lower() == 'table only':
                axis_string = character_node.find('plecs:CurrentAxis', namespaces).text
                current_axis = [float(x) for x in axis_string.split()]
                axis_string = character_node.find('plecs:VoltageAxis', namespaces).text
                voltage_axis = [float(x) for x in axis_string.split()]
                axis_string = character_node.find('plecs:TemperatureAxis', namespaces).text
                temperature_axis = [float(x) for x in axis_string.split()]
                energy_node = character_node.find('plecs:Energy', namespaces)
                scale = float(energy_node.attrib['scale'])
                for tdx, temp_node in enumerate(energy_node.findall('plecs:Temperature', namespaces)):
                    for vdx, vltg_node in enumerate(temp_node.findall('plecs:Voltage', namespaces)):
                        if not voltage_axis[vdx]:
                            continue
                        energy_dict = {}
                        energy_data = [float(x) * scale for x in vltg_node.text.split()]
                        energy_dict["dataset_type"] = "graph_i_e"
                        energy_dict["t_j"] = temperature_axis[tdx]
                        energy_dict["v_supply"] = voltage_axis[vdx]
                        energy_dict["r_g"] = 0
                        energy_dict["v_g"] = v_on
                        energy_dict["graph_i_e"] = np.transpose(np.column_stack((current_axis, energy_data)))
                        energy_on_list.append(energy_dict)

            if character_node.tag == '{' + namespaces['plecs'] + '}' + 'TurnOffLoss' and character_node.find('plecs:ComputationMethod', namespaces).text.lower() == 'table only':
                axis_string = character_node.find('plecs:CurrentAxis', namespaces).text
                current_axis = [float(x) for x in axis_string.split()]
                axis_string = character_node.find('plecs:VoltageAxis', namespaces).text
                voltage_axis = [float(x) for x in axis_string.split()]
                axis_string = character_node.find('plecs:TemperatureAxis', namespaces).text
                temperature_axis = [float(x) for x in axis_string.split()]
                energy_node = character_node.find('plecs:Energy', namespaces)
                scale = float(energy_node.attrib['scale'])
                for tdx, temp_node in enumerate(energy_node.findall('plecs:Temperature', namespaces)):
                    for vdx, vltg_node in enumerate(temp_node.findall('plecs:Voltage', namespaces)):
                        if not voltage_axis[vdx]:
                            continue
                        energy_dict = {}
                        energy_data = [float(x) * scale for x in vltg_node.text.split()]
                        energy_dict["dataset_type"] = "graph_i_e"
                        energy_dict["t_j"] = temperature_axis[tdx]
                        energy_dict["v_supply"] = voltage_axis[vdx]
                        energy_dict["r_g"] = 0
                        energy_dict["v_g"] = v_off
                        energy_dict["graph_i_e"] = np.transpose(np.column_stack((current_axis, energy_data)))
                        energy_off_list.append(energy_dict)

            if character_node.tag == '{' + namespaces['plecs'] + '}' + 'ConductionLoss' and character_node.find('plecs:ComputationMethod', namespaces).text.lower() == 'table only':
                axis_string = character_node.find('plecs:CurrentAxis', namespaces).text
                current_axis = [float(x) for x in axis_string.split()]
                axis_string = character_node.find('plecs:TemperatureAxis', namespaces).text
                temperature_axis = [float(x) for x in axis_string.split()]
                voltage_drop_node = character_node.find('plecs:VoltageDrop', namespaces)
                scale = float(voltage_drop_node.attrib['scale'])
                for tdx, temp_node in enumerate(voltage_drop_node.findall('plecs:Temperature', namespaces)):
                    channel_dict = {}
                    channel_data = [float(x) * scale for x in temp_node.text.split()]
                    channel_dict["t_j"] = temperature_axis[tdx]
                    channel_dict["v_g"] = v_on
                    channel_dict["graph_v_i"] = np.transpose(np.column_stack((channel_data, current_axis)))
                    channel_list.append(channel_dict)
        thermal_data = package.find('plecs:ThermalModel', namespaces)
        if thermal_data[0].attrib['type'] == 'Foster':
            r_par, tau_par = list(), list()
            for attr in thermal_data[0].findall('plecs:RTauElement', namespaces):
                r_par.append(float(attr.attrib['R']))
                tau_par.append(float(attr.attrib['Tau']) if attr.attrib['Tau'] else None)
            foster_args['r_th_vector'], foster_args['tau_vector'] = (r_par, tau_par) if len(r_par) > 1 else (None, None)
            foster_args['r_th_total'], foster_args['tau_total'] = (r_par[0], tau_par[0]) if len(r_par) == 1 else (sum(foster_args['r_th_vector']), sum(foster_args['tau_vector']))
        return info, energy_on_list, energy_off_list, channel_list, foster_args
    else:
        raise ImportError('Import of ' + file + ' Not possible: Only table type xml data are accepted')


def import_xml_data(files: dict) -> Transistor:
    """
    A function feature of transistordatabase module to import switch and diode characteristics in plecs xml file format.

    :param files: dictionary holding switch and diode xml file names
    :rtype files: dict

    :raises ImportError: raised when file format is not valid or not found

    :return: Transistor object creating using information extracted from the provided files
    :rtype: Transistor
    """
    try:
        s_info, s_energy_on_list, s_energy_off_list, s_channel_list, s_foster_args = get_xml_data(files['switch'])
        switch_args = {
            'comment': 'Gate voltages are set to 12V/0V',
            'manufacturer': s_info['vendor'],
            'technology': None,
            't_j_max': 175,
            'channel': s_channel_list,
            'e_on': s_energy_on_list,
            'e_off': s_energy_off_list,
            'thermal_foster': s_foster_args}
        d_info, d_energy_on_list, d_energy_off_list, d_channel_list, d_foster_args = get_xml_data(files['diode'])
        if s_info['class'] == 'IGBT' and d_info['class'] == 'Diode':
            if s_info['vendor'] != d_info['vendor'] or s_info['partnumber'] != d_info['partnumber']:
                raise ImportError('Vendor or part number differs')
        else:
            raise ImportError('Invalid files: One of type ' + s_info['class'] + ' and other ' + d_info['class'])
        diode_args = {'comment': 'Turn On and Off voltages are set to 12V/0V',
                      'manufacturer': d_info['vendor'],
                      'technology': None,
                      't_j_max': 175,
                      'channel': d_channel_list,
                      'e_rr': d_energy_off_list,
                      'thermal_foster': d_foster_args}
        transistor_args = {'name': s_info['partnumber'],
                           'type': s_info['class'],
                           'author': 'XML importer',
                           'comment': 'Generated using xml importer (inaccurate)',
                           'manufacturer': s_info['vendor'],
                           'datasheet_hyperlink': 'http://www.plexim.com/xml/semiconductors/' + s_info['partnumber'],
                           'datasheet_date': datetime.date.today(),
                           'datasheet_version': "unknown",
                           'housing_area': 0,
                           'cooling_area': 0,
                           'housing_type': 'PLECS Import',
                           'v_abs_max': 999999999,
                           'i_abs_max': max(s_channel_list[0]["graph_v_i"][1]),
                           'i_cont': max(s_channel_list[0]["graph_v_i"][1]) / 2,
                           'c_iss': None,  # insert csv here
                           'c_oss': None,  # insert csv here
                           'c_rss': None,  # insert csv here
                           'graph_v_ecoss': None,
                           'r_g_int': 0,
                           'r_th_cs': 0,
                           'r_th_diode_cs': 0,
                           'r_th_switch_cs': 0,
                           }
        return Transistor(transistor_args, switch_args, diode_args)
    except ImportError as e:
        print(e.args[0])


def attach_units(trans: dict, devices: dict):
    """
    The function will attach units for the virtual datasheet parameters when a call is made in export_datasheet() method.

    :param trans: pdf data which contains the transistor related generic information
    :type trans: dict
    :param devices: pdf data which contains the switch type related information
    :type devices: dict

    :return: sorted data along with units to be displayed in transistor, diode, switch  section on virtual datasheet
    :rtype: dict, dict, dict
    """
    standard_list = [('Author', 'Author', None), ('Name', 'Name', None), ('Manufacturer', 'Manufacturer', None), ('Type', 'Type', None), ('Datasheet_date', 'Datasheet date', None),
                     ('Datasheet_hyperlink', 'Datasheet hyperlink', None), ('Datasheet_version', 'Datasheet version', None)]
    mechthermal_list = [('Housing_area', 'Housing area', 'sq.m'), ('Housing_type', 'Housing type', 'None'), ('Cooling_area', 'Cooling area', 'sq.m'), ('R_th_cs', 'R_th,cs', 'K/W'),
                        ('R_th_total', 'R_th,total', 'K/W'), ('R_g_int', 'R_g,int', 'Ohms'), ('C_th_total', 'C_th,total', 'F'), ('Tau_total', 'Tau_total', 'sec'),
                        ('R_th_diode_cs', 'R_th,diode-cs', 'K/W'), ('R_th_switch_cs', 'R_th,switch-cs', 'K/W'), ('R_g_on_recommended', 'R_g,on-recommended', 'Ohms'),
                        ('R_g_off_recommended', 'R_g,off-recommended', 'Ohms')]
    maxratings_list = [('V_abs_max', 'V_abs,max', 'V'), ('I_abs_max', 'I_abs,max', 'A'), ('I_cont', 'I_cont', 'A'), ('T_j_max', 'T_j,max', '°C'), ('T_c_max', 'T_c,max', '°C')]
    cap_list = [('C_iss_fix', 'C_iss,fix', 'F'), ('C_oss_fix', 'C_oss,fix', 'F'), ('C_rss_fix', 'C_rss,fix', 'F'), ('C_oss_er', 'C_oss,er', 'F'), ('C_oss_tr', 'C_oss,tr', 'F')]
    trans_sorted = {}
    diode_sorted = {}
    switch_sorted = {}
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


def get_img_raw_data(plot):
    """
    A helper method to convert the plot images to raw data which is further used to display plots in virtual datasheet

    :param plot: pyplot object

    :return: decoded raw image data to utf-8
    """
    buf = io.BytesIO()
    plot.gcf().set_size_inches(3.5, 2.2)
    plot.savefig(buf, format='png', bbox_inches='tight')
    encoded_img_data = base64.b64encode(buf.getvalue())
    plot.close()
    return encoded_img_data.decode('UTF-8')


def get_vc_plots(cap_data: dict):
    """
    A helper function to plot and convert voltage dependant capacitance plots in raw data format. Invoked internally by export_datasheet() method.

    :param cap_data: dictionary holding capacitance information of type list (self.c_oss, self.c_iss, self.c_rss)
    :type cap_data: dict

    :return: decoded raw image data to utf-8
    """
    if not all(cap_data.values()):
        return None
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for key, item in cap_data.items():
        if isinstance(item, list) and item:
            for cap_curve in item:
                line1, = cap_curve.get_plots(ax, key)
    plt.legend(fontsize=8)
    plt.xlabel('Voltage in V')
    plt.ylabel('Capacitance in F')
    plt.grid()
    return get_img_raw_data(plt)


def get_channel_data(channel_data: list, plecs_holder: dict, v_on: int, is_diode: bool, has_body_diode: bool) -> dict:
    """
    A helper method to extract channel data of switch/diode for plecs exporter. Called internally by get_curve_data() for using plecs exporter feature.

    :param channel_data: channel data taken from transistor class switch/diode object
    :type channel_data: list
    :param plecs_holder: dictionary to collect the channel data
    :type plecs_holder: dict
    :param v_on: channel voltage of IGBT/MOSFET
    :type v_on: int
    :param is_diode: a boolean to notify that argument channel_data relates to diode
    :type is_diode: bool
    :param has_body_diode: a boolean to check if the switch relates to either mosfet or sic-mosfet type
    :type has_body_diode: bool

    :return: plecs_holder filled with the extracted switch's or diode's channel information
    :rtype: dict
    """
    for channel in channel_data:
        if channel['v_g'] == v_on or (not has_body_diode and is_diode):
            try:
                if limit_current and limit_current > max(np.abs(channel['graph_v_i'][1])):
                    limit_current = max(np.abs(channel['graph_v_i'][1]))
            except NameError:
                limit_current = max(np.abs(channel['graph_v_i'][1]))
    for channel in channel_data:
        if channel['v_g'] == v_on or (not has_body_diode and is_diode):
            interp_current = np.linspace(0, limit_current, 20)
            channel_data = np.interp(interp_current, np.abs(channel['graph_v_i'][1]), np.abs(channel['graph_v_i'][0]))
            if 'Channel' not in plecs_holder['ConductionLoss']:
                plecs_holder['ConductionLoss']['CurrentAxis'] = interp_current.tolist()
                plecs_holder['ConductionLoss']['Channel'] = list()
                plecs_holder['ConductionLoss']['TemperatureAxis'] = list()
            plecs_holder['ConductionLoss']['TemperatureAxis'].append(channel['t_j'])  # forward characteristics are defined only at one gate voltage and does not depend on v_supply
            plecs_holder['ConductionLoss']['Channel'].append(channel_data.tolist())
    return plecs_holder


def get_loss_curves(loss_data: list, plecs_holder: dict, loss_type: str, v_g: int, is_recovery_loss: bool) -> dict:
    """
    A helper method to extract loss information of switch/diode for plecs exporter. Called internally by get_curve_data() for using plecs exporter feature.

    :param loss_data: turn on/off energy data taken from transistor class switch or diode object
    :type loss_data: list
    :param plecs_holder: dictionary to collect the energy loss data
    :type plecs_holder: dict
    :param loss_type: either of type TurnOnLoss or TurnOffLoss
    :type loss_type: str
    :param v_g: gate turn on or turn off voltage at which the curves selected are being made
    :type v_g: int
    :param is_recovery_loss: a boolean to specify the provided loss information relates to diode's reverse recovery losses
    :type is_recovery_loss: bool

    :return: plecs_holder filled with the extracted switch's or diode's energy loss information
    :rtype: dict
    """
    for energy_dict in loss_data:
        if energy_dict['v_g'] == v_g and energy_dict['dataset_type'] == 'graph_i_e' and energy_dict['graph_i_e'] is not None:
            try:
                if limit_current and limit_current > max(energy_dict['graph_i_e'][0]):
                    limit_current = max(energy_dict['graph_i_e'][0])
            except NameError:
                limit_current = max(energy_dict['graph_i_e'][0])
    for energy_dict in loss_data:
        if energy_dict['v_g'] == v_g and energy_dict['dataset_type'] == 'graph_i_e' and energy_dict['graph_i_e'] is not None:
            interp_current = np.linspace(0, limit_current, 20)
            loss_energy = np.interp(interp_current, energy_dict['graph_i_e'][0], energy_dict['graph_i_e'][1])
            if 'Energy' not in plecs_holder[loss_type]:
                plecs_holder[loss_type]['CurrentAxis'] = interp_current.tolist()
                plecs_holder[loss_type]['Energy'] = {}
                plecs_holder[loss_type]['TemperatureAxis'] = list()
            rev_voltage = energy_dict['v_supply'] if not is_recovery_loss else -abs(energy_dict['v_supply'])
            if rev_voltage not in plecs_holder[loss_type]['Energy']:
                plecs_holder[loss_type]['Energy'][rev_voltage] = []
            plecs_holder[loss_type]['Energy'][rev_voltage].append(loss_energy.tolist())
            # Loss curves are defined at one v_g in many v_supply voltages, therefore to avoid redundancy in Tj and v_supply appends
            plecs_holder[loss_type]['TemperatureAxis'].append(energy_dict['t_j']) if energy_dict['t_j'] not in plecs_holder[loss_type]['TemperatureAxis'] else None
    return plecs_holder


def negate_and_append(voltage: list, current: list) -> tuple[list, np.array]:
    """
    A helper function to negate the channel current x-axis data for the transistors of type mosfet.
    Generates third quadrant curve characteristics for mosfet.

    :param voltage: channel voltage y-axis information
    :type voltage: list
    :param current: channel current x-axis information
    :type current: list

    :return: the negated channel axis information is appended to the exists axis and returned
    :rtype: tuple[list, np.array]
    """
    current_reverse = np.array(current)
    current_reverse = current_reverse[current_reverse != 0]
    current_reverse = np.flip(current_reverse)
    current_reverse = [-x for x in current_reverse]
    current = np.append(current_reverse, current).tolist()
    for index, vData in enumerate(voltage):
        voltage_reverse = np.array(vData)
        voltage_reverse = voltage_reverse[voltage_reverse != 0]
        voltage_reverse = np.flip(voltage_reverse)
        voltage_reverse = [-x for x in voltage_reverse]
        voltage[index] = np.append(voltage_reverse, vData).tolist()
    return voltage, current


def get_gatedefaults(transistor_type: str) -> list:
    """
    Defines gate voltage defaults depending on the transistor type

    :param transistor_type: transistor type, e.g. IGBT, MOSFET, SiC-MOSFET or GaN-Transistor
    :type transistor_type: str

    :return: default gate voltages [v_g_turn_on, v_g_turn_off, v_g_channel_blocks, v_g_channel_conducting]
    :rtype: list
    """
    gate_voltages = {'sic-mosfet': [SIC_MOS_VGS_ON, SIC_MOS_VGS_OFF, SIC_MOS_BD_VGS, SIC_MOS_BD_VG_ERR],
                     'mosfet': [MOS_VGS_ON, MOS_VGS_OFF, MOS_BD_VGS, MOS_BD_VG_ERR],
                     'igbt': [IGBT_VG_ON, IGBT_VG_OFF, DIODE_VGS, DIODE_VG_ERR],
                     'gan-transistor': [GAN_VGS_ON, GAN_VGS_OFF, GAN_BD_VGS, GAN_BD_VG_ERR]
                     }.get(transistor_type.lower(), [15, -15, 0, 15])
    return gate_voltages


def check_realnum(float_to_check: float) -> bool:
    """
    Check if argument is real numeric scalar. Raise TypeError if not. None is also accepted because it is valid for
    optional keys. Mandatory keys that must not contain None are checked somewhere else beforehand.

    :param float_to_check: input argument
    :type float_to_check: float

    :raises TypeError: if float_to_check is not numeric

    :return: True in case of numeric scalar.
    :rtype: bool
    """
    if isinstance(float_to_check, (int, float, np.integer, np.floating)) or float_to_check is None:
        return True
    raise TypeError(f"{float_to_check} is not numeric.")


def check_2d_dataset(dataset_to_check: np.array) -> bool:
    """
    Check if argument is real 2D-dataset of right shape. None is also accepted because it is
    valid for optional keys. Mandatory keys that must not contain None are checked somewhere else beforehand.

    :param dataset_to_check: 2d-dataset
    :type dataset_to_check: np.array

    :raises TypeError: if the passed argument is a 2D-numpy array with real numeric values

    :return: True in case of valid 2d-dataset
    :rtype: bool
    """
    if dataset_to_check is None:
        return True
    if isinstance(dataset_to_check, np.ndarray):
        if np.all(np.isreal(dataset_to_check)):
            if dataset_to_check.ndim == 2:
                if dataset_to_check.shape[0] == 2:
                    return True
    raise TypeError("Invalid dataset. Must be 2D-numpy array with shape (2,x) and real numeric values.")


def check_str(string_to_check: str) -> bool:
    """
    Check if argument is string. Function not necessary but helpful to keep raising of errors
    consistent with other type checks. None is also accepted because it is valid for optional keys. Mandatory keys that
    must not contain None are checked somewhere else beforehand.

    :param string_to_check: input string
    :type string_to_check: str

    :raises TypeError: if the argument is not of type string

    :return: True in case of valid string
    :rtype: bool
    """
    if isinstance(string_to_check, str) or string_to_check is None:
        return True
    raise TypeError(f"{string_to_check} is not a string.")


def csv2array(csv_filename: str, first_xy_to_00: bool = False, second_y_to_0: bool = False,
              first_x_to_0: bool = False, mirror_xy_data: bool = False) -> np.array:
    """
    Imports a .csv file and extracts its input to a numpy array. Delimiter in .csv file must be ';'. Both ',' or '.'
    are supported as decimal separators. .csv file can generated from a 2D-graph for example via
    https://apps.automeris.io/wpd/

    .. todo: Check if array needs to be transposed? (Always the case for webplotdigitizer)

    :param csv_filename: Insert .csv filename, e.g. "switch_channel_25_15v"
    :type csv_filename: str
    :param first_xy_to_00: Set 'True' to change the first value pair to zero. This is necessary in
        case of webplotdigitizer returns the first value pair e.g. as -0,13; 0,00349.
    :type first_xy_to_00: bool
    :param second_y_to_0: Set 'True' to set the second y-value to zero. This is interesting in
        case of diode / igbt forward channel characteristic, if you want to make sure to set the point where the ui-graph
        leaves the u axis on the u-point to zero. Otherwise there might be a very small (and negative) value of u.
    :type second_y_to_0: bool
    :param first_x_to_0: Set 'True' to set the first x-value to zero. This is interesting in
        case of nonlinear input/output capacities, e.g. c_oss, c_iss, c_rss
    :type first_x_to_0: bool
    :param mirror_xy_data: Takes the absolute() of both axis. Used for given mirrored data, e.g. some datasheet show diode data in the 3rd quadrant instead of the 1st quadrant
    :type mirror_xy_data: bool

    :return: 1d array, ready to use in the transistor database
    :rtype: np.array
    """
    # See issue #5: German csv-files use ; as separator, english systems use , as separator
    # if ; is available in the file, csv-file generation was made by a german-language operating system
    file1 = open(csv_filename, "r")
    readfile = file1.read()
    if ';' in readfile:
        # csv-file was generated by a german language system
        array = np.genfromtxt(csv_filename, delimiter=";",
                              converters={0: lambda s: float(s.decode("UTF-8").replace(",", ".")),
                                          1: lambda s: float(s.decode("UTF-8").replace(",", "."))})
    else:
        # csv-file was generated by a english language system
        array = np.genfromtxt(csv_filename, delimiter=",")
    file1.close()

    if first_xy_to_00:
        array[0][0] = 0  # x value
        array[0][1] = 0  # y value

    if second_y_to_0:
        array[1][1] = 0  # y value

    if first_x_to_0:
        array[0][0] = 0  # x value

    if mirror_xy_data:
        array = np.abs(array)

    return np.transpose(array)


def merge_curve(curve: np.array, curve_detail: np.array) -> np.array:
    """
    Merges two equal curves, one of which contains an enlarged section of the first curve.
    Use case is the merging of capacity curves, here often two curves (normal and zoom) are given in the data sheets.

    :param curve: full curve
    :type curve: np.array
    :param curve_detail: curve with zoom on x-axis
    :type curve_detail: np.array

    :return: merged curve
    :rtype: np.array

    :Example (e.g. merges c_oss curve from 0-200V and from 0-1000V):

    >>> import transistordatabase as tdb
    >>> c_oss_normal = tdb.csv2array('transistor_c_oss.csv', first_x_to_0=True)
    >>> c_oss_detail = tdb.csv2array('transistor_c_oss_detail.csv', first_x_to_0=True)
    >>> c_oss_merged = tdb.merge_curve(c_oss_normal, c_oss_detail)

    """

    # find out max(x) from detailed curve
    curve_detail_max_x = max(curve_detail[0])

    merged_curve = curve_detail.copy()

    # cut all values that are smaller than max(x) from
    for x in range(len(curve[0])):
        if curve[0][x] > curve_detail_max_x:
            merged_curve = np.append(merged_curve, [[curve[0][x]], [curve[1][x]]], axis=1)
            type(merged_curve)
    return merged_curve


def print_TDB(filters: Optional[List[str]] = None, collection_name: str = "local") -> List[str]:
    """
    Print all transistorelements stored in the local database

    :param filters: filters for searching the database, e.g. 'name' or 'type'
    :type filters: List[str]
    :param collection_name: Choose database name in local mongodb client. Default name is "collection"
    :type collection_name: str

    :return: Return a list with all transistor objects fitting to the search-filter
    :rtype: list

    :Example:

    >>> import transistordatabase as tdb
    >>> tdb.print_TDB()
    >>> # or
    >>> tdb.print_TDB(collection = 'type')
    """
    # Note: Never use mutable default arguments
    # see https://florimond.dev/en/posts/2018/08/python-mutable-defaults-are-the-source-of-all-evil/
    # This is the better solution
    filters = filters or []

    if collection_name == "local":
        mongodb_collection = connect_local_TDB()
    else:
        # TODO: support other collections. As of now, other database connections also connects to local-tdb
        warnings.warn("Connection of other databases than the local on not implemented yet. Connect so local database")
        mongodb_collection = connect_local_TDB()
    if not isinstance(filters, list):
        if isinstance(filters, str):
            filters = [filters]
        else:
            raise TypeError(
                "The 'filters' argument must be specified as a list of strings or a single string but is"
                f" {type(filters)} instead.")
    if "name" not in filters:
        filters.append("name")
    """Filters must be specified according to the respective objects they're associated with. 
    e.g. 'type' for type of Transistor or 'diode.technology' for technology of Diode."""
    returned_cursor = mongodb_collection.find({}, filters)
    name_list = []
    for tran in returned_cursor:
        print(tran)
        name_list.append(tran['name'])
    return name_list


def connect_TDB(host: str):
    """
    A method for establishing connection with transistordatabase_exchange.

    :param host: "local" is specified by default, other cases need to be investigated
    :type host: str

    :return: transistor_database collection
    """
    if host == "local":
        host = "mongodb://localhost:27017/"
    my_transistor_database = MongoClient(host)
    return my_transistor_database.transistor_database.collection


def connect_local_TDB():
    """
    A method for establishing connection with transistordatabase_exchange.
    Internally used by

      - update_from_fileexchange() method to sync the local with transistordatabase_File_Exchange
      - load() methods for saving and loading the transistor object to local mongodb-database.

    :return: transistor_database collection

    """
    host = "mongodb://localhost:27017/"
    myclient = MongoClient(host)
    return myclient.transistor_database.collection


def load(transistor: [str, dict], collection_name: str = "local"):
    """
    load a transistor from your local mongodb-database

    :param transistor: transistor name that needs to be loaded, see example
    :type transistor: str
    :param collection_name: mongodb connection, predefined value
    :type collection_name: str

    :return: transistor object
    :rtype: Transistor

    :Example:

    >>> import transistordatabase as tdb
    >>> transistor_loaded = tdb.load('Infineon_FF200R12KE3')
    """
    try:
        find_filter = {'name': transistor} if type(transistor) == str else transistor
        if collection_name == "local":
            mongodb_collection = connect_local_TDB()
        else:
            # TODO: support other collections. As of now, other database connections also connects to local-tdb
            warnings.warn("Connection of other databases than the local on not implemented yet. Connect so local database")
            mongodb_collection = connect_local_TDB()
        # ToDo: Implement case where different transistors fit the filter criteria.
        selected_trans_dict = mongodb_collection.find_one(find_filter)
        if selected_trans_dict is None:
            raise MissingDataError('Selected Transistor {0} does not exists in local database'.format(find_filter['name']))
        return convert_dict_to_transistor_object(selected_trans_dict)
    except MissingDataError as e:
        print(e.args[0])


def convert_dict_to_transistor_object(db_dict: dict) -> Transistor:
    """
    Converts a dictionary to a transistor object.
    This is a helper function of the following functions:

    - parallel_transistors()
    - load()
    - import_json()

    :param db_dict: transistor dictionary
    :type db_dict: dict

    :return: Transistor object
    :rtype: Transistor object
    """
    # Convert transistor_args
    transistor_args = db_dict
    if 'c_oss' in transistor_args and transistor_args['c_oss'] is not None:
        for i in range(len(transistor_args['c_oss'])):
            transistor_args['c_oss'][i]['graph_v_c'] = np.array(transistor_args['c_oss'][i]['graph_v_c'])
    if 'c_iss' in transistor_args and transistor_args['c_iss'] is not None:
        for i in range(len(transistor_args['c_iss'])):
            transistor_args['c_iss'][i]['graph_v_c'] = np.array(transistor_args['c_iss'][i]['graph_v_c'])
    if 'c_rss' in transistor_args and transistor_args['c_rss'] is not None:
        for i in range(len(transistor_args['c_rss'])):
            transistor_args['c_rss'][i]['graph_v_c'] = np.array(transistor_args['c_rss'][i]['graph_v_c'])
    if 'graph_v_ecoss' in transistor_args and transistor_args['graph_v_ecoss'] is not None:
        transistor_args['graph_v_ecoss'] = np.array(transistor_args['graph_v_ecoss'])
    if 'raw_measurement_data' in transistor_args:
        for i in range(len(transistor_args['raw_measurement_data'])):
            for u in range(len(transistor_args['raw_measurement_data'][i]['dpt_on_vds'])):
                transistor_args['raw_measurement_data'][i]['dpt_on_vds'][u] = np.array(transistor_args['raw_measurement_data'][i]['dpt_on_vds'][u])
            for u in range(len(transistor_args['raw_measurement_data'][i]['dpt_on_id'])):
                transistor_args['raw_measurement_data'][i]['dpt_on_id'][u] = np.array(transistor_args['raw_measurement_data'][i]['dpt_on_id'][u])
            for u in range(len(transistor_args['raw_measurement_data'][i]['dpt_off_vds'])):
                transistor_args['raw_measurement_data'][i]['dpt_off_vds'][u] = np.array(transistor_args['raw_measurement_data'][i]['dpt_off_vds'][u])
            for u in range(len(transistor_args['raw_measurement_data'][i]['dpt_off_id'])):
                transistor_args['raw_measurement_data'][i]['dpt_off_id'][u] = np.array(transistor_args['raw_measurement_data'][i]['dpt_off_id'][u])

    # Convert switch_args
    switch_args = db_dict['switch']
    if switch_args['thermal_foster']['graph_t_rthjc'] is not None:
        switch_args['thermal_foster']['graph_t_rthjc'] = np.array(switch_args['thermal_foster']['graph_t_rthjc'])
    for i in range(len(switch_args['channel'])):
        switch_args['channel'][i]['graph_v_i'] = np.array(switch_args['channel'][i]['graph_v_i'])
    for i in range(len(switch_args['e_on'])):
        if switch_args['e_on'][i]['dataset_type'] == 'graph_r_e':
            switch_args['e_on'][i]['graph_r_e'] = np.array(switch_args['e_on'][i]['graph_r_e'])
        elif switch_args['e_on'][i]['dataset_type'] == 'graph_i_e':
            switch_args['e_on'][i]['graph_i_e'] = np.array(switch_args['e_on'][i]['graph_i_e'])
    if 'e_on_meas' in switch_args:
        for i in range(len(switch_args['e_on_meas'])):
            if switch_args['e_on_meas'][i]['dataset_type'] == 'graph_r_e':
                switch_args['e_on_meas'][i]['graph_r_e'] = np.array(switch_args['e_on_meas'][i]['graph_r_e'])
            elif switch_args['e_on_meas'][i]['dataset_type'] == 'graph_i_e':
                switch_args['e_on_meas'][i]['graph_i_e'] = np.array(switch_args['e_on_meas'][i]['graph_i_e'])
    for i in range(len(switch_args['e_off'])):
        if switch_args['e_off'][i]['dataset_type'] == 'graph_r_e':
            switch_args['e_off'][i]['graph_r_e'] = np.array(switch_args['e_off'][i]['graph_r_e'])
        elif switch_args['e_off'][i]['dataset_type'] == 'graph_i_e':
            switch_args['e_off'][i]['graph_i_e'] = np.array(switch_args['e_off'][i]['graph_i_e'])
    if 'e_off_meas' in switch_args:
        for i in range(len(switch_args['e_off_meas'])):
            if switch_args['e_off_meas'][i]['dataset_type'] == 'graph_r_e':
                switch_args['e_off_meas'][i]['graph_r_e'] = np.array(switch_args['e_off_meas'][i]['graph_r_e'])
            elif switch_args['e_off_meas'][i]['dataset_type'] == 'graph_i_e':
                switch_args['e_off_meas'][i]['graph_i_e'] = np.array(switch_args['e_off_meas'][i]['graph_i_e'])
    if 'charge_curve' in switch_args:
        for i in range(len(switch_args['charge_curve'])):
            switch_args['charge_curve'][i]['graph_q_v'] = np.array(switch_args['charge_curve'][i]['graph_q_v'])
    if 'r_channel_th' in switch_args:
        for i in range(len(switch_args['r_channel_th'])):
            switch_args['r_channel_th'][i]['graph_t_r'] = np.array(switch_args['r_channel_th'][i]['graph_t_r'])
    if 'soa' in switch_args:
        for i in range(len(switch_args['soa'])):
            switch_args['soa'][i]['graph_i_v'] = np.array(switch_args['soa'][i]['graph_i_v'])

    # Convert diode_args
    diode_args = db_dict['diode']
    if diode_args['thermal_foster']['graph_t_rthjc'] is not None:
        diode_args['thermal_foster']['graph_t_rthjc'] = np.array(diode_args['thermal_foster']['graph_t_rthjc'])
    for i in range(len(diode_args['channel'])):
        diode_args['channel'][i]['graph_v_i'] = np.array(diode_args['channel'][i]['graph_v_i'])
    for i in range(len(diode_args['e_rr'])):
        if diode_args['e_rr'][i]['dataset_type'] == 'graph_r_e':
            diode_args['e_rr'][i]['graph_r_e'] = np.array(diode_args['e_rr'][i]['graph_r_e'])
        elif diode_args['e_rr'][i]['dataset_type'] == 'graph_i_e':
            diode_args['e_rr'][i]['graph_i_e'] = np.array(diode_args['e_rr'][i]['graph_i_e'])
    if 'soa' in diode_args:
        for i in range(len(diode_args['soa'])):
            diode_args['soa'][i]['graph_i_v'] = np.array(diode_args['soa'][i]['graph_i_v'])

    return Transistor(transistor_args, switch_args, diode_args)


def update_from_fileexchange(collection: str = "local", overwrite: bool = True) -> None:
    """
    Update your local transistor database from transistordatabase-fileexchange from github

    :param collection: name of mongodb collection
    :type collection: str
    :param overwrite: True to overwrite existing transistor objects in local database, False to not overwrite existing transistor objects in local database.
    :type overwrite: bool

    :return: None
    :rtype: None
    """
    print("Note: Please make sure that you have installed the latest version of the transistor database, "
          "especially if the update_from_fileexchange()-method ends in an error. "
          "Find the latest version here: https://pypi.org/project/transistordatabase/")
    # Check if the local repository exists, if yes load the repo information
    repo_url = f"https://github.com/upb-lea/transistordatabase_File_Exchange"
    module_file_path = pathlib.Path(__file__).parent.absolute()
    local_dir = os.path.join(module_file_path, "cloned_repo_TDB_File_Exchange")

    try:
        # Raises InvalidGitRepositoryError when not in a repo
        repo = git.Repo(local_dir, search_parent_directories=False)
        # check that the repository loaded correctly
        if not repo.bare:
            print('Repo at {} successfully loaded.'.format(repo.working_tree_dir))
            print("Remote: " + repo.remote("origin").url)
            # If the loaded repo is dirty discard the local changes
            if repo.is_dirty():
                repo.git.reset('--hard')
            repo.remotes.origin.pull()
        else:
            print('Could not load repository at {} :('.format(repo.working_tree_dir))
            raise git.exc.InvalidGitRepositoryError
    except git.exc.InvalidGitRepositoryError:
        # Occurs if repo couldn't be located, initially check if cloned_repo folder exists and deletes it before cloning from remote
        if os.path.isdir(local_dir):
            for root, dirs, files in os.walk(local_dir):
                for dir in dirs:
                    os.chmod(os.path.join(root, dir), stat.S_IRWXU)
                for file in files:
                    os.chmod(os.path.join(root, file), stat.S_IRWXU)
            shutil.rmtree(local_dir)
        git.Repo.clone_from(repo_url, local_dir)
    except git.exc.NoSuchPathError:
        # if local repository doesn't exits, clone from remote branch
        git.Repo.clone_from(repo_url, local_dir)

    if collection == "local":
        collection = connect_local_TDB()

    for subdir, dirs, files in os.walk(local_dir):
        for file in files:
            # print(f"{os.path.join(subdir, file)}")
            filepath = subdir + os.sep + file
            if filepath.endswith(".json"):
                try:
                    transistor = import_json(filepath)
                except Exception as e:
                    warnings.warn("Failed Transistor : " + filepath)
                else:
                    transistor.save(collection, overwrite)
                    print(f"Update Transistor: {transistor.name}")


def import_json(path: str) -> Transistor:
    """
    Import a json-file and return a transistor class object.
    Note: The transistor is NOT stored in your local database!

    :param path: path to the .json-file
    :type path: str

    :return: transistor dictionary, loaded from the .json-file
    :rtype: Transistor

    :Example:

    >>> import transistordatabase as tdb
    >>> transistor_imported = tdb.import_json('CREE_C3M0016120K.json')
    """
    if isinstance(path, str):
        with open(path, 'r') as transistor_json_file:
            transistor_dict = transistor_json_file.read()
        return convert_dict_to_transistor_object(json_util.loads(transistor_dict))
    else:
        TypeError("path = {0} ist not a string.".format(path))


def r_g_max_rapid_channel_turn_off(v_gsth: float, c_ds: float, c_gd: float, i_off: Union[float, List[float]],
                                   v_driver_off: float) -> float:
    """
    Calculates the maximum gate resistor to achieve no turn-off losses when working with MOSFETs
    'rapid channel turn-off' (rcto)

    Note: Input (e.g. i_off can also be a vector)
    Source: D. Kubrick, T. Dürbaum, A. Bucher:
    'Investigation of Turn-Off Behaviour under the Assumption of Linear Capacitances'
    International Conference of Power Electronics Intelligent Motion Power Quality 2006, PCIM 2006, p. 239 –244

    :param v_gsth: gate threshold voltage
    :type v_gsth: float
    :param c_ds: equivalent drain-source capacitance
    :type c_ds: float
    :param c_gd: equivalent gate-drain capacitance
    :type c_gd: float
    :param i_off: turn-off current
    :type i_off: float or List[float]
    :param v_driver_off: Driver voltage during turn-off
    :type v_driver_off: float

    :return: r_g_max_rcto maximum gate resistor to achieve rapid channel turn-off
    :rtype: float
    """
    return (v_gsth - v_driver_off) / i_off * (1 + c_ds / c_gd)


# Export helper functions


def dict2matlab(input_dict: dict) -> dict:
    """
    Cleans a python dict and makes it compatible with matlab

    Dict must be cleaned from 'None's to np.nan (= NaN in Matlab)
    see https://stackoverflow.com/questions/35985923/replace-none-in-a-python-dictionary

    :param input_dict: dictionary to be cleaned
    :type input_dict: dict

    :return: 'clean' matlab-compatible transistor dictionary
    :rtype: dict
    """
    result = {}
    for key, value in input_dict:
        if value is None:
            value = np.nan
        result[key] = value
    return result


def matlab_compatibility_test(Transistor, attribute):
    """
    checks attribute for occurrences of None an replace it with np.nan

    .. todo: This function might can be replaced by dict_clean()

    :param Transistor: transistor object
    :type Transistor: Transistor
    :param attribute: path to given attribute
    :type attribute: str

    :raises AttributeError: if the provided path evaluates to invalid attribute

    :return: attribute value or np.nan
    """
    try:
        att = eval(attribute)
        if att is None:
            return np.nan
        else:
            return att

    except AttributeError:
        return np.nan


def check_keys(keys_to_check: dict, req_type: str, switch_type: str):
    """
    A helper function for find_next_gate_voltage method of class type - switch and diode. Verifies if the required keys are available and their value types are valid for carrying out the export
    Used for export_gecko() and export_plecs()

    :param keys_to_check: the dictionary which contains the essential keys for the corresponding exporter function
    :type keys_to_check: dict
    :param req_type: 'plecs' or 'gecko' type for passed during respective exporter function calls
    :type req_type: str
    :param switch_type: 'diode' or 'switch'
    :type switch_type: str

    :raises KeyError: when not all the required keys are available for the chosen exporter functions
    :raises ValueError: if the key values are None

    """
    default_key_dict = {'plecs': ('v_channel_gs', 'v_d_off'),
                        'gecko': ('v_channel_gs', 'v_supply', 'v_d_off')}.get(req_type) if switch_type == 'diode' else \
        {'plecs': ('v_channel_gs', 'v_g_on', 'v_g_off'),
         'gecko': ('v_channel_gs', 'v_supply', 'v_g_on', 'v_g_off')}.get(req_type)
    if all(key in list(keys_to_check.keys()) for key in default_key_dict):
        for value in keys_to_check.values():
            if value is None:
                raise ValueError
            else:
                check_realnum(value)
    else:
        raise KeyError("Not all keys exists for re-estimating gate voltages")


class MissingDataError(Exception):
    """Custom exception class for plecs_exporter"""

    # define the error codes & messages here
    em = {1101: "Switch conduction channel information is missing, cannot export to",
          1111: "Switch conduction channel information is missing at provided v_g, cannot export to",
          1102: "Switch turn on loss curves do not exists at every junction temperature, cannot export to",
          1103: "Switch turn off loss curves do not exists at every junction temperature, cannot export to",
          1104: "Switch turn on loss information is missing",
          1105: "Switch turn off loss information is missing",
          1201: "Diode conduction channel information is missing, cannot export to",
          1211: "Diode conduction channel information is missing at provided v_g, cannot export to",
          1202: "Diode reverse recovery loss information is missing",
          1203: "Diode reverse recovery loss curves do not exists at every junction temperature, cannot export to"}


def dpt_save_data(measurement_dict: dict):
    """
        Imports double pulse measurements and calculates switching losses to each given working point.

        [1] options for the integration interval are based on following paper:
        Link: https://ieeexplore.ieee.org/document/8515553

        :param measurement_dict: dictionary with above mentioned parameters
        :type measurement_dict: dict

        """

    if measurement_dict.get('integration_interval') == 'IEC 60747-9':
        off_vds_limit = 0.1
        off_is_limit = 0.02
        on_vds_limit = 0.02
        on_is_limit = 0.1
    elif measurement_dict.get('integration_interval') == 'Mitsubishi':
        off_vds_limit = 0.1
        off_is_limit = 0.1
        on_vds_limit = 0.1
        on_is_limit = 0.1
    elif measurement_dict.get('integration_interval') == 'Infineon':
        off_vds_limit = 0.1
        off_is_limit = 0.02
        on_vds_limit = 0.02
        on_is_limit = 0.1
    elif measurement_dict.get('integration_interval') == 'Wolfspeed':
        off_vds_limit = 0
        off_is_limit = -0.1
        on_vds_limit = -0.1
        on_is_limit = 0
    else:
        off_vds_limit = 0.1
        off_is_limit = 0.1
        on_vds_limit = 0.1
        on_is_limit = 0.1

    # Get a list of all the csv files
    csv_files = glob.glob(measurement_dict.get('path'))

    position_t_j = csv_files[1].rfind("C_")
    position_t_j_start = csv_files[1].rfind("_", 0, position_t_j)
    t_j = int(csv_files[1][position_t_j_start + 1:position_t_j])

    position_r_g = csv_files[1].rfind("R_")
    position_r_g_start = csv_files[1].rfind("_", 0, position_r_g)
    r_g = int(csv_files[1][position_r_g_start + 1:position_r_g])

    position_v_supply = csv_files[1].rfind("V_")
    position_v_supply_start = csv_files[1].rfind("_", 0, position_v_supply)
    v_supply = int(csv_files[1][position_v_supply_start + 1:position_v_supply])

    dpt_raw_data = {}
    e_off_meas = Union[dict, None]
    e_on_meas = Union[dict, None]

    position_attribute_start = 'V_'
    position_attribute_end = 'A_'
    label_x_plot = 'Id / A'

    if measurement_dict['dataset_type'] == 'graph_r_e':
        position_attribute_start = 'C_'
        position_attribute_end = 'R_'
        label_x_plot = 'Ron / Ohm'
        r_g_on_list = []

    if measurement_dict['energies'] == 'e_off' or measurement_dict['energies'] == 'both':
        off_i_locations = []
        off_v_locations = []
        csv_length = len(csv_files)

        ##############################
        # Read all Turn-off current measurements and sort them by Id or Rgon
        ##############################
        i = 0
        while csv_length > i:
            if csv_files[i].rfind("_OFF_I") != -1:
                position_a = csv_files[i].rfind(position_attribute_end)
                position_b = csv_files[i].rfind(position_attribute_start)
                off_i_locations.append([i, int(csv_files[i][position_b + 2:position_a])])
            i += 1
        off_i_locations.sort(key=lambda x: x[1])

        ##############################
        # Read all Turn-off voltage measurements and sort them by Id or Rgon
        ##############################
        i = 0
        while csv_length > i:
            if csv_files[i].rfind("_OFF_U") != -1:
                position_a = csv_files[i].rfind(position_attribute_end)
                position_b = csv_files[i].rfind(position_attribute_start)
                off_v_locations.append([i, int(csv_files[i][position_b + 2:position_a])])
            i += 1
        off_v_locations.sort(key=lambda x: x[1])

        sample_point = 0
        measurement_points = len(off_i_locations)
        e_off = []
        vds_raw_off = []
        id_raw_off = []
        time_correction = 0

        while measurement_points > sample_point:
            # Load vds and Id pairs in increasing order
            vds = np.genfromtxt(csv_files[off_v_locations[sample_point][0]], delimiter=',', skip_header=24)
            Id = np.genfromtxt(csv_files[off_i_locations[sample_point][0]], delimiter=',', skip_header=24)

            vds_raw_off.append(np.array(vds))
            id_raw_off.append(np.array(Id))

            sample_length = len(vds)
            sample_interval = abs(vds[1, 0] - vds[2, 0])
            avg_interval = int(sample_length * 0.05)

            vds_avg_max = 0
            id_avg_max = 0

            ##############################
            # Find the max. Id in steady state
            ##############################
            i = 0
            while i <= avg_interval:
                id_avg_max = id_avg_max + Id[i, 1] / avg_interval
                i += 1

            ##############################
            # Find the max. vds in steady state
            ##############################
            i = 0
            while i <= avg_interval:
                vds_avg_max = vds_avg_max + vds[(sample_length - 1 - i), 1] / avg_interval
                i += 1

            ##############################
            # Find the starting point of the Eoff integration
            # i equals the lower integration limit
            ##############################
            i = 0
            e_off_temp = 0
            while vds[i, 1] < (vds_avg_max * off_vds_limit):
                i += 1

            lower_integration_limit = i

            ##############################
            # Integrate the power with predefined integration limits
            ##############################
            while Id[i - time_correction, 1] >= (id_avg_max * off_is_limit):
                e_off_temp = e_off_temp + (vds[i, 1] * Id[i - time_correction, 1] * sample_interval)
                i += 1

            upper_integration_limit = i

            if measurement_dict['dataset_type'] == 'graph_r_e':
                e_off.append([off_i_locations[sample_point][1], e_off_temp])
                r_g_on_list.append(off_i_locations[sample_point][1])
            else:
                e_off.append([id_avg_max, e_off_temp])

            sample_point += 1

        e_off_0 = [item[0] for item in e_off]
        e_off_1 = [item[1] for item in e_off]

        e_off_meas = {'dataset_type': measurement_dict.get('dataset_type'),
                      't_j': t_j,
                      'load_inductance': measurement_dict.get('load_inductance'),
                      'commutation_inductance': measurement_dict.get('commutation_inductance'),
                      'commutation_device': measurement_dict.get('commutation_device'),
                      'comment': measurement_dict.get('comment'),
                      'measurement_date': measurement_dict.get('measurement_date'),
                      'measurement_testbench': measurement_dict.get('measurement_testbench'),
                      'v_supply': v_supply,
                      'v_g': measurement_dict.get('v_g'),
                      'v_g_off': measurement_dict.get('v_g_off'),
                      'r_g': r_g,
                      'r_g_off': measurement_dict.get('r_g_off'),
                      'graph_i_e': np.array([e_off_0, e_off_1]),
                      'graph_r_e': np.array([e_off_0, e_off_1]),
                      'e_x': float(e_off_1[0]),
                      'i_x': id_avg_max}

        dpt_raw_data |= {'dpt_off_vds': vds_raw_off, 'dpt_off_id': id_raw_off}

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

    if measurement_dict['energies'] == 'e_on' or measurement_dict['energies'] == 'both':
        i = 0
        on_i_locations = []
        on_v_locations = []
        csv_length = len(csv_files)
        ##############################
        # Read all Turn-on current measurements and sort them by Id or Rgon
        ##############################
        while csv_length > i:
            if csv_files[i].rfind("_ON_I") != -1:
                position_a = csv_files[i].rfind(position_attribute_end)
                position_b = csv_files[i].rfind(position_attribute_start)
                on_i_locations.append([i, int(csv_files[i][position_b + 2:position_a])])
            i += 1
        on_i_locations.sort(key=lambda x: x[1])

        ##############################
        # Read all Turn-on voltage measurements and sort them by Id or Rgon
        ##############################
        i = 0
        while csv_length > i:
            if csv_files[i].rfind("_ON_U") != -1:
                position_a = csv_files[i].rfind(position_attribute_end)
                position_b = csv_files[i].rfind(position_attribute_start)
                on_v_locations.append([i, int(csv_files[i][position_b + 2:position_a])])
            i += 1
        on_v_locations.sort(key=lambda x: x[1])

        sample_point = 0
        measurement_points = len(on_i_locations)
        e_on = []
        vds_raw_on = []
        id_raw_on = []

        while measurement_points > sample_point:
            # Load vds and Id pairs in increasing order
            vds = np.genfromtxt(csv_files[on_v_locations[sample_point][0]], delimiter=',', skip_header=24)
            Id = np.genfromtxt(csv_files[on_i_locations[sample_point][0]], delimiter=',', skip_header=24)

            vds_raw_on.append(np.array(vds))
            id_raw_on.append(np.array(Id))

            sample_length = len(vds)
            sample_interval = abs(vds[1, 0] - vds[2, 0])
            avg_interval = int(sample_length * 0.05)
            vds_avg_max = 0
            id_avg_max = 0

            ##############################
            # Find the max. Id in steady state
            ##############################
            i = 0
            while i <= avg_interval:
                id_avg_max = id_avg_max + (Id[(sample_length - 3 - i), 1] / avg_interval)
                i += 1

            ##############################
            # Find the max. vds in steady state
            ##############################
            i = 0
            while i <= avg_interval:
                vds_avg_max = vds_avg_max + (vds[i, 1] / avg_interval)
                i += 1

            ##############################
            # Find the starting point of the Eon integration
            # i equals the lower integration limit
            ##############################
            i = 0
            e_on_temp = 0
            while Id[i, 1] < (id_avg_max * on_is_limit):
                i += 1

            time_correction = 0
            ##############################
            # Integrate the power with predefined integration limits
            ##############################
            while vds[i + time_correction, 1] >= (vds_avg_max * on_vds_limit):
                e_on_temp = e_on_temp + (vds[i + time_correction, 1] * Id[i, 1] * sample_interval)
                i += 1

            if measurement_dict['dataset_type'] == 'graph_r_e':
                e_on.append([on_i_locations[sample_point][1], e_on_temp])
            else:
                e_on.append([id_avg_max, e_on_temp])

            if measurement_dict['dataset_type'] == 'graph_r_e' and measurement_dict['energies'] != 'both':
                r_g_on_list.append(on_i_locations[sample_point][1])

            sample_point += 1

        e_on_0 = [item[0] for item in e_on]
        e_on_1 = [item[1] for item in e_on]

        e_on_meas = {'dataset_type': measurement_dict.get('dataset_type'),
                     't_j': t_j,
                     'load_inductance': measurement_dict.get('load_inductance'),
                     'commutation_inductance': measurement_dict.get('commutation_inductance'),
                     'commutation_device': measurement_dict.get('commutation_device'),
                     'comment': measurement_dict.get('comment'),
                     'measurement_date': measurement_dict.get('measurement_date'),
                     'measurement_testbench': measurement_dict.get('measurement_testbench'),
                     'v_supply': v_supply,
                     'v_g': measurement_dict.get('v_g'),
                     'v_g_off': measurement_dict.get('v_g_off'),
                     'r_g': r_g,
                     'r_g_off': measurement_dict.get('r_g_off'),
                     'graph_i_e': np.array([e_on_0, e_on_1]),
                     'graph_r_e': np.array([e_on_0, e_on_1]),
                     'e_x': float(e_on_1[0]),
                     'i_x': id_avg_max}

        dpt_raw_data |= {'dpt_on_vds': vds_raw_on, 'dpt_on_id': id_raw_on}

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

    dpt_raw_data |= {'t_j': t_j,
                     'load_inductance': measurement_dict.get('load_inductance'),
                     'measurement_date': measurement_dict.get('measurement_date'),
                     'measurement_testbench': measurement_dict.get('measurement_testbench'),
                     'v_supply': v_supply,
                     'v_g': measurement_dict.get('v_g'),
                     'v_g_off': measurement_dict.get('v_g_off')}

    if measurement_dict.get('dataset_type') == 'graph_r_e':
        dpt_raw_data |= {'dataset_type': 'dpt_u_i_r',
                         'r_g': r_g_on_list}
    else:
        dpt_raw_data |= {'dataset_type': 'dpt_u_i',
                         'r_g': r_g}
    dpt_dict = {'e_off_meas': e_off_meas, 'e_on_meas': e_on_meas, 'raw_measurement_data': dpt_raw_data}
    return dpt_dict


def build_dummy(attribute_name, attribute_value):
    """
            This function creates an dummy transistor which is usually used by update_dpt_measurement to append
            new values to a existing transistor.

            :param attribute_name: Name of the attribute you want to change.
            :type attribute_name: str
            :param attribute_value: Dict of data you want to add to given attribute.
            :type attribute_value: dict
            """

    name = 'Dummy-Transistor'
    type = 'IGBT'
    author = 'Dummy-Author'
    manufacturer = 'Fuji Electric'
    housing_area = 367e-6
    cooling_area = 160e-6
    housing_type = 'TO247'
    v_abs_max = 200
    i_abs_max = 200
    i_cont = 200
    r_g_int = 10
    t_j_max = 175
    r_th_switch_cs = 0
    r_th_diode_cs = 0
    r_th_cs = 0.05

    switch_args = {'t_j_max': t_j_max,
                   attribute_name: attribute_value}
    diode_args = {'t_j_max': t_j_max,
                  attribute_name: attribute_value}
    transistor_args = {'name': name,
                       'type': type,
                       'author': author,
                       'manufacturer': manufacturer,
                       'housing_area': housing_area,
                       'cooling_area': cooling_area,
                       'housing_type': housing_type,
                       'v_abs_max': v_abs_max,
                       'i_abs_max': i_abs_max,
                       'i_cont': i_cont,
                       'r_g_int': r_g_int,
                       'r_th_cs': r_th_cs,
                       'r_th_switch_cs': r_th_switch_cs,
                       'r_th_diode_cs': r_th_diode_cs,
                       attribute_name: attribute_value}

    dummy_transistor = Transistor(transistor_args, switch_args, diode_args)
    return dummy_transistor


def update_dpt_measurement(transistor_name, measurement_data):
    """
        This function loads a transistor from the database and adds new measurement data.

        :param transistor_name: Name of the transistor to be loaded.
        :type transistor_name: str
        :param measurement_data: Dict of data you want to add to given attribute.
        :type measurement_data: dict

        """

    transistor_loaded = load(transistor_name)
    collection = connect_local_TDB()
    transistor_id = {'_id': transistor_loaded._id}

    if measurement_data['e_off_meas'] is not None:
        dummy_off = build_dummy('e_off_meas', measurement_data['e_off_meas'])
        transistor_loaded.switch.e_off_meas.append(dummy_off.switch.e_off_meas[0])
        transistor_dict = transistor_loaded.convert_to_dict()
        new_value = {'$set': {'switch.e_off_meas': transistor_dict['switch']['e_off_meas']}}
        collection.update_one(transistor_id, new_value)

    if measurement_data['e_on_meas'] is not None:
        dummy_on = build_dummy('e_on_meas', measurement_data['e_on_meas'])
        transistor_loaded.switch.e_on_meas.append(dummy_on.switch.e_on_meas[0])
        transistor_dict = transistor_loaded.convert_to_dict()
        new_value = {'$set': {'switch.e_on_meas': transistor_dict['switch']['e_on_meas']}}
        collection.update_one(transistor_id, new_value)

    if measurement_data['dpt_raw_data'] is not None:
        dummy_raw = build_dummy('raw_measurement_data', measurement_data['dpt_raw_data'])
        transistor_loaded.raw_measurement_data.append(dummy_raw.raw_measurement_data[0])
        transistor_dict = transistor_loaded.convert_to_dict()
        new_value = {'$set': {'raw_measurement_data': transistor_dict['raw_measurement_data']}}
        collection.update_one(transistor_id, new_value)
