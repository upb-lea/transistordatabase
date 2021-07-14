import datetime
import numpy as np
import re
import os
from typing import List
from matplotlib import pyplot as plt
from bson.objectid import ObjectId
from bson import json_util
from scipy import integrate
from scipy.spatial import distance
from pymongo import MongoClient
from pymongo import errors
import json
import pathlib
import inspect
from fpdf import FPDF
from git import Repo
import shutil
import stat
import scipy.io as sio
import collections
from jinja2 import Environment, FileSystemLoader


class Transistor:
    """Groups data of all other classes for a single transistor. Methods are specified in such a way that only
    user-interaction with this class is necessary (ToDo!)
    Documentation on how to add or extract a transistor-object to/from the database can be found in (ToDo!)
    """
    # ToDo: Add database _id as attribute
    _id: "bson.objectid.ObjectId"
    name: str  # Name of the transistor. Choose as specific as possible. # Mandatory
    type: str  # Mandatory
    # User-specific data
    author: str  # Mandatory
    comment: [str, None]  # Optional
    # Date and template data. Should not be changed manually.
    # ToDo: Add methods to automatically determine dates and template_version on construction or update.
    template_version: str  # Mandatory/Automatic
    template_date: "datetime.datetime"  # Mandatory/Automatic
    creation_date: "datetime.datetime"  # Mandatory/Automatic
    last_modified: "datetime.datetime"  # Mandatory/Automatic
    # Manufacturer- and part-specific data
    manufacturer: str  # Mandatory
    datasheet_hyperlink: [str, None]  # Make sure this link is valid.  # Optional
    datasheet_date: ["datetime.datetime", None]  # Optional, pymongo cannot encode date => always save as datetime
    datasheet_version: [str, None]  # Optional
    housing_area: float  # Unit: m^2  # Mandatory
    cooling_area: float  # Unit: m^2  # Mandatory
    housing_type: str  # e.g. TO-220, etc. # Mandatory. Must be from a list of specific strings.
    # These are documented in their respective class definitions
    switch: "Switch"
    diode: "Diode"
    # Thermal data. See git for equivalent thermal_foster circuit diagram.
    r_th_cs: [float, int, None]  # Unit: K/W  # Optional
    r_th_switch_cs: [float, int, None]  # Unit: K/W  # Optional
    r_th_diode_cs: [float, int, None]  # Unit: K/W  # Optional
    # Absolute maximum ratings
    v_abs_max: [float, int]  # Unit: V  # Mandatory
    i_abs_max: [float, int]  # Unit: A  # Mandatory
    # Constant Capacitances
    c_oss_fix: [float, int, None]  # Unit: F  # Optional
    c_iss_fix: [float, int, None]  # Unit: F  # Optional
    c_rss_fix: [float, int, None]  # Unit: F  # Optional
    # Voltage dependent capacitances
    c_oss: List["VoltageDependentCapacitance"]  # VoltageDependentCapacitance. # Optional
    c_iss: List["VoltageDependentCapacitance"]  # VoltageDependentCapacitance. # Optional
    c_rss: List["VoltageDependentCapacitance"]  # VoltageDependentCapacitance. # Optional
    # Energy stored in c_oss
    graph_v_ecoss: ["np.ndarray[np.float64]", None]  # Units: Row 1: V; Row 2: J  # Optional
    # Rated operation region
    i_cont: [float, int, None]  # Unit: A  # e.g. Fuji: I_c, Semikron: I_c,nom # Mandatory
    t_c_max: [float, int]  # Unit °C # Optional
    r_g_int: [float, int]  # Unit: Ohm # Mandatory

    def __init__(self, transistor_args, switch_args, diode_args):
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
            else:
                # ToDo: Is this a value or a type error?
                # ToDo: Move these raises to isvalid_dict() by checking dict_type for 'None' or empty dicts?
                # ToDo: Use info in isvalid_dict() to print the list of mandatory values automatically
                raise TypeError("Dictionary 'transistor_args' is empty or 'None'. This is not allowed since following keys"
                                "are mandatory: 'name', 'type', 'author', 'manufacturer', 'housing_area', "
                                "'cooling_area', 'housing_type', 'v_abs_max', 'i_abs_max', 'i_cont'")

            self.diode = self.Diode(diode_args)
            self.switch = self.Switch(switch_args)
            self.wp = self.WP()
        except Exception as e:
            print('Exception occured: Selected datasheet or module could not be created or loaded\n'+str(e))
            raise

    def __eq__(self, other):
        if not isinstance(other, Transistor):
            # don't attempt to compare against unrelated types
            return NotImplemented
        my_dict = self.convert_to_dict()
        my_dict.pop('_id', None)
        other_dict = other.convert_to_dict()
        other_dict.pop('_id', None)
        return my_dict == other_dict

    def save(self, collection="local", overwrite=None):
        if collection == "local":
            collection = connect_local_TDB()
        transistor_dict = self.convert_to_dict()
        if transistor_dict.get("_id") is not None:
            _id = transistor_dict["_id"]
            if collection.find_one({"_id": _id}) is not None:
                if not isinstance(overwrite, bool):
                    raise errors.DuplicateKeyError(
                        f"A transistor object with {_id = } is already present in the TDB. Please specify, "
                        f"whether the newly saved Transistor should replace the old one or whether it should "
                        f"be saved as a copy. This can be done by setting the optional argument 'overwrite' "
                        f" to either True or False.")
                if not overwrite:
                    del transistor_dict["_id"]
                    collection.insert_one(transistor_dict)
                if overwrite:
                    collection.replace_one({"_id": _id}, transistor_dict)
            else:
                collection.insert_one(transistor_dict)
        else:
            collection.insert_one(transistor_dict)

    def export_json(self, path=None):
        """
        export a transistor to .json file, e.g. to share this file on fileexchange on github
        :param path: path to export
        :return: -
        """
        transistor_dict = self.convert_to_dict()
        if path is None:
            with open(transistor_dict['name'] + '.json', 'w') as fp:
                json.dump(transistor_dict, fp, default=json_util.default)
            print(f"Saved json-file {transistor_dict['name'] + '.json'} to {os.getcwd()}")
        elif isinstance(path, str):
            with open(os.path.join(path, transistor_dict['name'] + '.json'), 'w') as fp:
                json.dump(transistor_dict, fp, default=json_util.default)
            print(f"Saved json-file {transistor_dict['name'] + '.json'} to {path}")
        else:
            TypeError(f"{path = } ist not a string.")

    def convert_to_dict(self):
        d = dict(vars(self))
        d.pop('wp', None)  # remove wp from convertig. wp will not be stored to .json files
        d['diode'] = self.diode.convert_to_dict()
        d['switch'] = self.switch.convert_to_dict()
        d['c_oss'] = [c.convert_to_dict() for c in self.c_oss]
        d['c_iss'] = [c.convert_to_dict() for c in self.c_iss]
        d['c_rss'] = [c.convert_to_dict() for c in self.c_rss]
        if isinstance(self.graph_v_ecoss, np.ndarray):
            d['graph_v_ecoss'] = self.graph_v_ecoss.tolist()
        return d

    @staticmethod
    def isvalid_dict(dataset_dict, dict_type):
        """
        This method checks input argument dictionaries for their validity. It is checked whether all mandatory keys
        are present, have the right type and permitted values (e.g. 'MOSFET' or 'IGBT' or 'SiC-MOSFET' for 'type').
        Returns 'False' if dictionary is 'None' or Empty. These cases should be handled outside this method.
        Raises appropriate errors if dictionary invalid in other ways.
        :param dataset_dict: dataset dict
        :param dict_type:
        :return: True in case of valid dict, 'False' if dictionary is 'None' or Empty
        """
        # ToDo: Error if given key is not used?
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
                                 'r_th_diode_cs', 't_c_max'},
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
                'array_keys': {'graph_t_rthjc'}}
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
            text_file_dict = {'housing_type': 'housing_types.txt', 'manufacturer': 'module_manufacturers.txt'}
            for key, filename in text_file_dict.items():
                file = os.path.join(os.path.dirname(__file__), filename)
                with open(file, "r") as file_txt:
                    read_list = [line.replace("\n", "") for line in file_txt.readlines()]
                    # Remove all non alphanumeric characters from housing_type and manufacturer names and
                    # convert to lowercase for comparison
                    snub = "[^A-Za-z0-9]+" if key == 'housing_type' else "[^A-Za-z]+"
                    alphanum_values = [re.sub(snub, "", line).lstrip().lower() for line in read_list]
                    dataset_value = dataset_dict.get(key)
                    if re.sub(snub, "", dataset_value).lstrip().lower() not in alphanum_values:
                        name = key.capitalize().replace("_"," ")
                        raise ValueError(f"{name} {dataset_value} is not allowed. See file {filename} for a "
                                 f"list of supported types.")

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
                if any(x<0 for x in axis) == True:
                    raise ValueError(" Negative values are not allowed, please include mirror_xy_data attribute")

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

    def update_wp(self, t_j, v_g, i_channel, switch_or_diode="both", normalize_t_to_v=10):
        if switch_or_diode in ["diode", "both"]:
            diode_channel, self.wp.e_rr = self.diode.find_approx_wp(t_j, v_g, normalize_t_to_v)
            if self.wp.e_rr is None:
                print(f"run diode.find_approx_wp: closest working point for {t_j = } °C and {v_g = } V:")
                print(f"There is no err, may due to MOSFET, SiC-MOSFET or GaN device: Set err to [[0, 0], [0, 0]]")
                print(f"Note: Values are set to t_j = 25°C, v_g = 15V, r_g = 1 Ohm")
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

    def quickstart_wp(self):
        self.update_wp(self.switch.t_j_max - 25, 15, self.i_abs_max/2)

    def calc_v_eoss(self):
        """
        Calculates e_oss stored in c_oss depend on the voltage. Uses transistor.c_oss[0].graph_v_coss
        :return: e_oss numpy array
        """
        # energy_cumtrapz = np.zeros_like(self.c_oss[0].graph_v_c[1], dtype=np.float32)
        energy_cumtrapz = integrate.cumulative_trapezoid(self.c_oss[0].graph_v_c[0] * self.c_oss[0].graph_v_c[1],
                                                         self.c_oss[0].graph_v_c[0], initial=0)
        return np.array([self.c_oss[0].graph_v_c[0], energy_cumtrapz])

    def calc_v_qoss(self):
        """
        Calculates q_oss stored in c_oss depend on the voltage. Uses transistor.c_oss[0].graph_v_coss
        :return: q_oss numpy array
        """
        charge_cumtrapz = integrate.cumulative_trapezoid(self.c_oss[0].graph_v_c[1], self.c_oss[0].graph_v_c[0],
                                                         initial=0)

        return np.array([self.c_oss[0].graph_v_c[0], charge_cumtrapz])

    def plot_v_eoss(self):
        """
        Plots v_eoss with method calc_v_eoss
        :return:
        """
        v_eoss = self.calc_v_eoss()
        plt.figure()
        plt.plot(v_eoss[0], v_eoss[1])
        plt.xlabel('Voltage in V')
        plt.ylabel('Energy in J')
        plt.grid()
        plt.show()

    def plot_v_qoss(self):
        v_qoss = self.calc_v_qoss()
        plt.figure()
        plt.plot(v_qoss[0], v_qoss[1])
        plt.xlabel('Voltage in V')
        plt.ylabel('Charge in C')
        plt.grid()
        plt.show()

    def get_object_v_i(self, switch_or_diode, t_j, v_g):
        """
        get a channel curve including boundary conditions
        :param switch_or_diode: 'switch' or 'diode'
        :param t_j: junction temperature
        :param v_g: gate voltage
        :return: v_i-object (channel curve including boundary conditions)
        """
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

    def get_object_i_e(self, e_on_off_rr, t_j, v_g, v_supply, r_g):
        """
        Function to get the loss graphs out of the transistor class
        :param e_on_off_rr: can be the following: 'e_on', 'e_off' or 'e_rr'
        :param t_j: junction temperature
        :param v_g: gate voltage at turn-on / turn-off
        :param v_supply: dc link voltage
        :param r_g: gate resistor
        :return: e_on.graph_i_e or e_off.graph_i_e or e_rr.graph_i_e
        """
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

    def get_object_i_e_simplified(self, e_on_off_rr, t_j):
        """
        Function to get the loss graphs out of the transistor class, simplified version
        :param e_on_off_rr: can be the following: 'e_on', 'e_off' or 'e_rr'
        :param t_j: junction temperature
        :return: e_on.graph_i_e or e_off.graph_i_e or e_rr.graph_i_e
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
            for re_curve in re_datasets:
                for curve in ie_datasets:
                    if curve.v_supply == re_curve.v_supply and curve.t_j == re_curve.t_j and curve.v_g == re_curve.v_g:
                        i_e_dataset = curve
                        r_e_dataset = re_curve
            text_to_print = "A match found in r_e characteristics for the chosen operating point and therefore will be used" if match else "The first of these sets is automatically chosen because selection of a different dataset is not yet implemented."
            print(text_to_print)
        elif len(ie_datasets) == 1:
            i_e_dataset = ie_datasets[0]
        return i_e_dataset, r_e_dataset

    def get_object_r_e_simplified(self, e_on_off_rr, t_j, v_g, v_supply, normalize_t_to_v):
        """
        Function to get the loss graphs out of the transistor class, simplified version
        :param e_on_off_rr: can be the following: 'e_on', 'e_off' or 'e_rr'
        :param t_j: junction temperature
        :return: e_on.graph_i_e or e_off.graph_i_e or e_rr.graph_i_e
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
        index_lossdata = distance.cdist([node], nodes).argmin()
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

    def calc_object_i_e(self, e_on_off_rr, r_g, t_j, v_supply, normalize_t_to_v):
        """
        Calculate loss curves for other gate resistor than the standard one.
        This function uses i_e loss curve in combination with r_e loss curve, to calculate a new i_e loss curve for
        a choosen gate restistor. Also voltage correction is implemented (e.g. half voltage compared to datasheet means half losses)
        Note: r_e_object may has not same voltage as i_e_object. #ToDo:  r_e_object may has not same voltage as i_e_object.
        :param e_on_off_rr: 'e_on', 'e_off', 'e_rr'
        :param r_g: gate resistor of interest
        :param t_j: juncntion temperature of interest
        :param v_supply: supply voltage of interest
        :return: object with corrected i_e curves due to r_g and v_supply at given t_j
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
            args = {
                'dataset_type': 'graph_i_e',
                'r_g': r_g,
                'v_supply': v_supply_chosen,
                'graph_i_e': object_i_e_calc,
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

    def virtual_datasheet(self):
        pdf = PDF()
        pdf.set_title(f"Virtual datasheet {self.name}")
        pdf.set_author('LEA - Transistor Database File generator')
        pdf.add_page()
        pdf.chapter_title(1, 'Transistor data')
        pdf.print_value(self.name)
        pdf.print_value(self.type)
        pdf.print_value(self.author)
        pdf.print_value(self.technology)
        pdf.print_value(self.template_version)
        pdf.print_value(self.template_date)
        pdf.print_value(self.creation_date)
        pdf.print_value(self.last_modified)
        pdf.print_value(self.comment)
        pdf.print_value(self.manufacturer)
        pdf.print_value(self.datasheet_hyperlink)
        pdf.print_value(self.datasheet_date)
        pdf.print_value(self.datasheet_version)
        pdf.print_value(self.housing_area)
        pdf.print_value(self.cooling_area)
        pdf.print_value(self.t_c_max)
        pdf.print_value(self.r_g_int)
        pdf.print_value(self.c_oss_fix)
        pdf.print_value(self.c_iss_fix)
        pdf.print_value(self.c_rss_fix)
        pdf.print_value(self.housing_type)
        pdf.print_value(self.r_th_cs)
        pdf.print_value(self.r_th_switch_cs)
        pdf.print_value(self.r_th_diode_cs)
        pdf.print_value(self.v_abs_max)
        pdf.print_value(self.i_abs_max)
        pdf.print_value(self.i_cont)
        pdf.add_page()
        pdf.chapter_title(2, 'Switch data')
        pdf.print_value(self.switch.comment)
        pdf.print_value(self.switch.manufacturer)
        pdf.print_value(self.switch.technology)
        pdf.print_value(self.switch.t_j_max)
        pdf.add_page()
        pdf.chapter_title(3, 'Diode data')
        pdf.print_value(self.diode.comment)
        pdf.print_value(self.diode.manufacturer)
        pdf.print_value(self.diode.technology)
        pdf.print_value(self.diode.t_j_max)
        # pdf.figure_left(memfile)
        # pdf.figure_right(memfile)
        # memfile.close()
        pdf.output(self.name + '.pdf')

    def calc_lin_channel(self, t_j, v_g, i_channel, switch_or_diode):
        """
        Get interpolated channel parameters. This function searches for ui_graphs with the chosen t_j and v_g. At
        the desired current, the equivalent parameters for u_channel and r_channel are returned
        :param t_j: junction temperature
        :param v_g: gate voltage
        :param i_channel: current to linearize the channel
        :param switch_or_diode: 'switch' or 'diode'
        :return: linearized parameters for v_channel, r_channel
        """
        # ToDo: rethink method name. May include switch or diode as a parameter and use one global function
        # ToDo: check if this function works for all types of transistors
        # ToDo: Error handling
        # ToDo: Unittest for this method
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

    """
    Initial author: Henning Steinhagen
    Date of creation: 04.01.2021
    Last modified by: Mohan Nagella
    Date of modification: 14.07.2021
    Version: 0.2.7
    Compatibility: Python
    Other files required: Numpy and SciPy package
    Link to file:
    ToDo: Check transistor name for forbidden symbols
    ToDo: implement linearization and update attributes (each attribute has its own TODO)
    ToDo: Add input parameters (e.g. for a given temperature set)

    Description:
    Exports transistor objects for multiple use cases.

    Known Bugs:
    Changelog:
    VERSION / DATE / NAME: Comment
    1.0.0 / 04.01.2021 / Henning Steinhagen: Initial Version
    1.0.1 / 08.01.2021 / Henning Steinhagen: Reformatted Code + exportTransistor implementation
    1.0.2 / 18.01.2021 / Manuel Klaedtke: Updated names and implemented changes accordingly to the restructuring of
    Metadata class and some other attributes
    1.1.0 / 24.01.2021 / Henning Steinhagen: Implemented compatibilityCheck
    1.2.0 / 25.01.2021 / Henning Steinhagen: Implemented exportTransistorV1 (Legacy format to old .mat Database)
    1.2.1 / 01.02.2021 / Henning Steinhagen: Added functionality to exportTransistorV1 and build functions to extract Data
    1.3.0 / 02.02.2021 / Henning Steinhagen: Added functionality to export_matlab_v1 + commented code + renamed functions
    1.4.0 / 17.02.2021 / Manuel Klädtke: Removed Metadata class and added all its attributes to Transistor class. Updated
    export functions accordingly.
    1.4.1 / 1.6.2021 / Nikolas Förster: remove export_simulink_v1 and replace by export_simulink_loss_model
    """

    # export function start from here
    def buildList(self, attribute):
        """
        Gather list data (e.g. channel/e_on/e_off/e_rr) and check for 'None'
        :param Transistor: transistor object
        :param attribute: attribute path to list
        :return: matlab compatible list of all attributes
        """

        if compatibilityTest(self, attribute) is not np.nan:
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

    def export_simulink_loss_model(self, r_g_on=None, r_g_off=None, v_supply=None, normalize_t_to_v=10):
        """
        Exports a simulation model for simulink inverter loss models, see https://de.mathworks.com/help/physmod/sps/ug/loss-calculation-in-a-three-phase-3-level-inverter.html
        #ToDo: C_th is fixed at the moment to 1e-6 for switch an diode. Needs to be calculated from ohter data
        Notes:
         - temperature next to 25 and 150 degree at 15V gate voltage will be used for channel and switching loss
         - in case of just one temperature curve, the upper temperature will increased (+1K) to bring a small temperature change in the curves. Otherwise the model will not work
         - only necessary data from tdb will be exported to simulink
         - Simulink model need switching energy loss in 'mJ'
         - in case of no complete curve (e.g. not starting from zero), this tool will interpolate the curve
        :param transistor: transistor object
        :return: .mat file for import in matlab/simulink
        """
        try:
            # Notes on exporting the file:
            # values need to be exported as np.double(), otherwise the Simulink-model can not interpolate the data (but displaying the curves is working...)

            if self.type.lower() != 'igbt':
                raise ValueError("In export_simulink_loss_model: Function is working for IGBTs only")

            t_j_lower = 25
            t_j_upper = 150
            v_g = 15

            ### switch
            print("---------------------IGBT properties----------------------")
            switch_channel_object_lower, eon_object_lower, eoff_object_lower = self.switch.find_approx_wp(t_j_lower, v_g, normalize_t_to_v, SwitchEnergyData_dataset_type="graph_i_e")
            switch_channel_object_upper, eon_object_upper, eoff_object_upper = self.switch.find_approx_wp(t_j_upper, v_g, normalize_t_to_v, SwitchEnergyData_dataset_type="graph_i_e")
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
                           'R_th_total': compatibilityTest(self, 'Transistor.switch.thermal_foster.r_th_total') if self.switch.thermal_foster.r_th_total != 0 else 1e-6,
                           'C_th_total': np.double(1),
                           'V_ref_on': np.double(eon_object_upper.v_supply),
                           'V_ref_off': np.double(eon_object_upper.v_supply),
                           'Eon': np.double(e_on_array * 1000),
                           'Eoff': np.double(e_off_array * 1000),
                           'v_channel': np.double(switch_channel_array),
                           'i_vec': np.double(i_interp),
                           }
            ### diode
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
                'R_th_total': compatibilityTest(self, 'Transistor.diode.thermal_foster.r_th_total') if self.diode.thermal_foster.r_th_total != 0 else 1e-6,
                'C_th_total': np.double(1),
                'V_ref_rr': np.double(err_object_lower.v_supply),
                'v_channel': np.double(diode_channel_array),
                'i_vec': np.double(i_interp),
                'Err': np.double(err_array * 1000)

            }

            transistor_dict = {'Name': compatibilityTest(self, 'Transistor.name'),
                               'R_th_CS': compatibilityTest(self, 'Transistor.r_th_cs') if self.r_th_cs != 0 else 1e-6,
                               'R_th_Switch_CS': compatibilityTest(self, 'Transistor.r_th_switch_cs') if self.r_th_switch_cs != 0 else 1e-6,
                               'R_th_Diode_CS': compatibilityTest(self, 'Transistor.r_th_diode_cs') if self.r_th_diode_cs != 0 else 1e-6,
                               'Switch': switch_dict,
                               'Diode': diode_dict,
                               'file_generated': f"{datetime.datetime.today()}",
                               'file_generated_by': "https://github.com/upb-lea/transistordatabase",
                               'r_g_on': np.double(eon_object_lower.r_g),
                               'r_g_off': np.double(eoff_object_lower.r_g),
                               }

            sio.savemat(self.name.replace('-', '_') + '_Simulink_lossmodel.mat', {self.name.replace('-', '_'): transistor_dict})
            print(f"Export files {self.name}_Simulink_lossmodel.mat to {os.getcwd()}")
        except Exception as e:
            print("Simulink exporter failed: {0}".format(e))

    def export_matlab(self):
        """
        Exports a transistor dictionary to a matlab dictionary
        :param transistor: transistor object
        :return: file stored in current working path
        """
        transistor_dict = self.convert_to_dict()
        dict_str = json.dumps(transistor_dict, default=json_util.default)

        # Note: Dict must be cleaned from 'None's to np.nan (= NaN in Matlab)
        # see https://stackoverflow.com/questions/35985923/replace-none-in-a-python-dictionary
        transistor_clean_dict = json.loads(dict_str, object_pairs_hook=dict_clean)
        transistor_clean_dict['file_generated'] = f"{datetime.datetime.today()}"
        transistor_clean_dict['file_generated_by'] = "https://github.com/upb-lea/transistordatabase",

        sio.savemat(self.name.replace('-', '_') + '_Matlab.mat', {self.name.replace('-', '_'): transistor_clean_dict})
        print(f"Export files {self.name.replace('-', '_')}_Matlab.mat to {os.getcwd()}")

    def export_geckocircuits(self, v_supply, v_g_on, v_g_off, r_g_on, r_g_off):
        """
        Export transistor data to GeckoCIRCUITS

        :param Transistor: choose the transistor to export
        :param v_supply: supply voltage for turn-on/off losses
        :param v_g_on: gate turn-on voltage
        :param v_g_off: gate turn-off voltage
        :param r_g_on: gate resistor for turn-on
        :param r_g_off: gate resistor for turn-off
        :return: two output files: 'Transistor.name'_Switch.scl and 'Transistor.name'_Diode.scl for geckoCIRCUITS import
        """

        # programming notes
        # exporting the diode:
        # diode off losses:
        # diode on losses: these on losses must be generated, even if they are zero
        # diode channel: it is not allowed to use more than one current that is zero (otherwise geckocircuits can not calculate the losses)

        amount_v_g_switch_cond = 0
        amount_v_g_switch_sw = 0
        amount_v_g_diode_cond = 0
        amount_v_g_diode_sw = 0

        # set numpy print options to inf, due to geckocircuits requests the data in one single line
        np.set_printoptions(linewidth=np.inf)

        ########################
        # export file for switch
        ########################
        file_switch = open(self.name + "_Switch.scl", "w")

        #### switch channel data
        # count number of arrays with gate v_g == v_g_export
        for n_channel in np.array(range(0, len(self.switch.channel))):
            if self.switch.channel[n_channel].v_g == v_g_on:
                amount_v_g_switch_cond += 1

        file_switch.write("anzMesskurvenPvCOND " + str(amount_v_g_switch_cond) + "\n")
        for n_channel in np.array(range(0, len(self.switch.channel))):
            if self.switch.channel[n_channel].v_g == v_g_on:

                voltage = self.switch.channel[n_channel].graph_v_i[0]
                current = self.switch.channel[n_channel].graph_v_i[1]

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
                file_switch.write(f"\ntj {self.switch.channel[n_channel].t_j}\n")
                file_switch.write("<\LeitverlusteMesskurve>\n")

        #### switch switching loss
        # check for availability of switching loss curves
        # count number of arrays with gate v_g == v_g_export
        for n_on in np.array(range(0, len(self.switch.e_on))):
            if self.switch.e_on[n_on].v_g == v_g_on and self.switch.e_on[n_on].r_g == r_g_on and \
                    self.switch.e_on[n_on].v_supply == v_supply:
                amount_v_g_switch_sw += 1

        file_switch.write(f"anzMesskurvenPvSWITCH {amount_v_g_switch_sw}\n")

        for n_on in np.array(range(0, len(self.switch.e_on))):
            if self.switch.e_on[n_on].v_g == v_g_on and self.switch.e_on[n_on].r_g == r_g_on and \
                    self.switch.e_on[n_on].v_supply == v_supply:

                on_current = self.switch.e_on[n_on].graph_i_e[0]
                on_energy = self.switch.e_on[n_on].graph_i_e[1]

                # search for off loss curves
                for n_off in np.array(range(0, len(self.switch.e_off))):
                    if self.switch.e_off[n_off].v_g == v_g_off and self.switch.e_off[n_off].r_g == r_g_off and \
                            self.switch.e_off[n_off].v_supply == v_supply:
                        # set off current and off energy
                        off_current = self.switch.e_off[n_off].graph_i_e[0]
                        off_energy = self.switch.e_off[n_off].graph_i_e[1]

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
                file_switch.write(f"\ntj {self.switch.e_on[n_on].t_j}\n")
                file_switch.write(f"uBlock {self.switch.e_on[n_on].v_supply}\n")
                file_switch.write("<\SchaltverlusteMesskurve>\n")

        file_switch.close()

        ########################
        # export file for diode
        ########################

        file_diode = open(self.name + "_Diode.scl", "w")
        #### diode channel data
        # count number of arrays for conducting behaviour
        # in case of gan-transistor, search for v_g_off
        # in case of mosfet or igbt use all available data
        for n_channel in np.array(range(0, len(self.diode.channel))):
            if (self.diode.channel[n_channel].v_g == v_g_off and self.type.lower() == 'gan-transistor') or self.type == 'MOSFET' or self.type == 'IGBT':
                amount_v_g_diode_cond += 1

        file_diode.write("anzMesskurvenPvCOND " + str(amount_v_g_diode_cond) + "\n")
        # export conducting behaviour
        for n_channel in np.array(range(0, len(self.diode.channel))):
            # if v_g_diode is given, search for it. Else, use all data in Transistor.diode.channel
            # in case of gan-transistor, search for v_g_off
            # in case of mosfet or igbt use all available data
            if (self.diode.channel[n_channel].v_g == v_g_off and self.type.lower() == 'gan-transistor') or self.type == 'MOSFET' or self.type == 'IGBT':

                voltage = np.abs(self.diode.channel[n_channel].graph_v_i[0])
                current = np.abs(self.diode.channel[n_channel].graph_v_i[1])

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
                file_diode.write(f"\ntj {self.diode.channel[n_channel].t_j}\n")
                file_diode.write("<\LeitverlusteMesskurve>\n")

        #### diode err loss
        # check for availability of switching loss curves
        # in case of no switching losses available, set curves to zero.
        # if switching losses will not set to zero, geckoCIRCUITS will use inital values
        if len(self.diode.e_rr) == 0:
            file_diode.write(f"anzMesskurvenPvSWITCH 1\n")
            file_diode.write("<SchaltverlusteMesskurve>\n")
            file_diode.write(f"data[][] 3 2 0 10 0 0 0 0")
            file_diode.write(f"\ntj 125\n")
            file_diode.write(f"uBlock 400\n")
            file_diode.write("<\SchaltverlusteMesskurve>\n")

        # in case of available data
        #
        else:
            # check for curves with the gate voltage
            # count number of arrays with gate v_g == v_g_export
            for n_rr in np.array(range(0, len(self.diode.e_rr))):
                if self.diode.e_rr[n_rr].v_g == v_g_on and self.diode.e_rr[n_rr].r_g == r_g_on and \
                        self.diode.e_rr[n_rr].v_supply == v_supply:
                    amount_v_g_diode_sw += 1

            # in case of no given v_g for diode (e.g. for igbts)
            if amount_v_g_diode_sw == 0:
                for n_rr in np.array(range(0, len(self.diode.e_rr))):
                    if self.diode.e_rr[n_rr].v_g and self.diode.e_rr[n_rr].r_g == r_g_on and \
                            self.diode.e_rr[n_rr].v_supply == v_supply:
                        amount_v_g_diode_sw += 1

                file_diode.write(f"anzMesskurvenPvSWITCH {amount_v_g_diode_sw}\n")

                for n_rr in np.array(range(0, len(self.diode.e_rr))):
                    if self.diode.e_rr[n_rr].v_g and self.diode.e_rr[n_rr].r_g == r_g_on and self.diode.e_rr[n_rr].v_supply == v_supply:
                        rr_current = self.diode.e_rr[n_rr].graph_i_e[0]
                        rr_energy = self.diode.e_rr[n_rr].graph_i_e[1]

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
                        file_diode.write(f"\ntj {self.diode.e_rr[n_rr].t_j}\n")
                        file_diode.write(f"uBlock {self.diode.e_rr[n_rr].v_supply}\n")
                        file_diode.write("<\SchaltverlusteMesskurve>\n")

              # in case of devices wich include a gate voltage (e.g. GaN-transistors)
            else:
                file_diode.write(f"anzMesskurvenPvSWITCH {amount_v_g_diode_sw}\n")
                for n_rr in np.array(range(0, len(self.diode.e_rr))):
                    if self.diode.e_rr[n_rr].v_g == v_g_on and self.diode.e_rr[n_rr].r_g == r_g_on and \
                            self.diode.e_rr[n_rr].v_supply == v_supply:
                        rr_current = self.diode.e_rr[n_rr].graph_i_e[0]
                        rr_energy = self.diode.e_rr[n_rr].graph_i_e[1]
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
                        file_diode.write(f"\ntj {self.diode.e_rr[n_rr].t_j}\n")
                        file_diode.write(f"uBlock {self.diode.e_rr[n_rr].v_supply}\n")
                        file_diode.write("<\SchaltverlusteMesskurve>\n")

        file_diode.close()
        print(f"Export files {self.name}_Switch.scl and {self.name}_Diode.scl to {os.getcwd()}")
        # set print options back to default
        np.set_printoptions(linewidth=75)

    def export_plecs(self, recheck=True, gate_voltages=list()):
        file_loader = FileSystemLoader(searchpath="./")
        env = Environment(loader=file_loader)
        env.globals["enumerate"] = enumerate
        print(os.getcwd())
        switch_xml_data, diode_xml_data = self.get_curve_data(recheck, gate_voltages)
        for data in filter(None, [switch_xml_data, diode_xml_data]):
            if data['type'] == 'Diode':
                if len(data['TurnOffLoss']['CurrentAxis']) > 1:
                    data['TurnOffLoss']['Energy'][0] = [[0] * len(data['TurnOffLoss']['CurrentAxis'])] * len(
                        data['TurnOffLoss']['TemperatureAxis'])
                data['TurnOnLoss']['Energy'] = collections.OrderedDict(sorted(data['TurnOnLoss']['Energy'].items()))
                data['TurnOffLoss']['Energy'] = collections.OrderedDict(sorted(data['TurnOffLoss']['Energy'].items()))
                template = env.get_template('diodeTemplate.txt')
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
                template = env.get_template('switchTemplate.txt')
                output = template.render(transistor=data)
                str_decoded = output.encode()
                with open(data['partnumber'] + "_switch.xml", "w") as fh:
                    fh.write(str_decoded.decode())

    class FosterThermalModel:
        """Contains data to specify parameters of the Foster thermal_foster model. This model describes the transient
        temperature behavior as a thermal_foster RC-network. The necessary parameters can be estimated by curve-fitting
        transient temperature data supplied in graph_t_rthjc or by manually specifying the individual 2 out of 3 of the
         parameters R, C, and tau."""
        # ToDo: Add function to estimate parameters from transient data.
        # ToDo: Add function to automatically calculate missing parameters from given ones.
        # ToDo: Do these need to be numpy array or should they be lists instead?
        # Thermal resistances of RC-network (array).
        r_th_vector: [List[float], None]  # Unit: K/W  # Optional
        # Sum of thermal_foster resistances of n-pole RC-network (scalar).
        r_th_total: [float, int, None]  # Unit: K/W  # Optional
        # Thermal capacitances of n-pole RC-network (array).
        c_th_vector: [List[float], None]  # Unit: J/K  # Optional
        # Sum of thermal_foster capacitances of n-pole low pass as (scalar).
        c_th_total: [float, int, None]  # Unit: J/K  # Optional
        # Thermal time constants of n-pole RC-network (array).
        tau_vector: [List[float], None]  # Unit: s  # Optional
        # Sum of thermal_foster time constants of n-pole RC-network (scalar).
        tau_total: [float, int, None]  # Unit: s  # Optional
        # Transient data for extraction of the thermal_foster parameters specified above.
        # Represented as a 2xm Matrix where row 1 is the time and row 2 the temperature.
        graph_t_rthjc: ["np.ndarray[np.float64]", None]  # Units: Row 1: s; Row 2: K/W  # Optional

        def __init__(self, args):
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

        def convert_to_dict(self):
            d = dict(vars(self))
            for att_key in d:
                if isinstance(d[att_key], np.ndarray):
                    d[att_key] = d[att_key].tolist()
            return d

    class Switch:
        """Contains data associated with the switchting-characteristics of a MOSFET/SiC-MOSFET or IGBT. Can contain multiple
        channel-, e_on- and e_off-datasets. """
        # Metadata
        comment: [str, None]  # Optional
        manufacturer: [str, None]  # Optional
        technology: [str, None]  # Semiconductor technology. e.g. IGBT3/IGBT4/IGBT7  # Optional
        # These are documented in their respective class definitions.
        thermal_foster: "FosterThermalModel"  # Transient thermal_foster model.  # Optional
        channel: List["ChannelData"]  # Switch channel voltage and current data.
        e_on: List["SwitchEnergyData"]  # Switch on energy data.
        e_off: List["SwitchEnergyData"]  # Switch of energy data.
        linearized_switch: List["LinearizedModel"]  # Static data valid for a specific operating point.
        #
        t_j_max: [float, int]  # Unit: °C # Mandatory

        def __init__(self, switch_args):
            # Current behavior on empty 'foster' dictionary: thermal_foster object is still created but with empty attributes.
            # ToDo: Is this the right behavior or should the 'thermal_foster' attribute be left empty istead?
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

            else:  # Can be constructed from empty or 'None' argument dictionary since no attributes are mandatory.
                self.comment = None
                self.manufacturer = None
                self.technology = None
                self.channel = []
                self.e_on = []
                self.e_off = []
                self.linearized_switch = []

        def convert_to_dict(self):
            d = dict(vars(self))
            d['thermal_foster'] = self.thermal_foster.convert_to_dict()
            d['channel'] = [c.convert_to_dict() for c in self.channel]
            d['e_on'] = [e.convert_to_dict() for e in self.e_on]
            d['e_off'] = [e.convert_to_dict() for e in self.e_off]
            d['linearized_switch'] = [lsw.convert_to_dict() for lsw in self.linearized_switch]
            return d

        def find_next_gate_voltage(self, v_on, v_off, SwitchEnergyData_dataset_type="graph_i_e"):
            # recheck channel characteristics curves at v_supply
            channel_v_gs = np.array([0 if chan.v_g is None else chan.v_g for chan in self.channel])
            v_g = min(channel_v_gs, key=lambda x: abs(x-v_on))
            # recheck turn on energy loss curves at v_supply
            if self.e_on:
                e_ons = [e for e in self.e_on if e.dataset_type == SwitchEnergyData_dataset_type]
                e_on_v_gs = np.array([0 if e.v_g is None else e.v_g for e in e_ons])
                v_on = min(e_on_v_gs, key=lambda x: abs(x-v_on))
            # recheck turn off energy loss curves at v_supply
            if self.e_off:
                e_offs = [e for e in self.e_off if e.dataset_type == SwitchEnergyData_dataset_type]
                e_off_v_gs = np.array([0 if e.v_g is None else e.v_g for e in e_offs])
                v_off = min(e_off_v_gs, key=lambda x: abs(x-v_off))
            print("--Switch Recheck--")
            print(f"channel: v_g = {v_g} V")
            print(f"e_on: v_g = {v_on} V")
            print(f"e_off: v_g = {v_off} V")
            return v_g, v_on, v_off

        def find_approx_wp(self, t_j, v_g, normalize_t_to_v=10, SwitchEnergyData_dataset_type="graph_i_e"):
            """
            This function looks for the smallest distance to stored object value and returns this working point
            :param t_j: junction temperature
            :param v_g: gate voltage
            :param normalize_t_to_v: ratio between t_j and v_g. e.g. 10 means 10°C is same difference as 1V
            :param SwitchEnergyData_dataset_type: preferred dataset_type (single, graph_r_e, graph_i_e) for e_on and
            e_off # ToDo: Should the default be "graph_i_e" or rather a kind of "don't care"?
            :return: channel-object, e_on-object, e_off-object
            """
            # Normalize t_j to v_g for distance metric
            node = np.array([t_j / normalize_t_to_v, v_g])
            # Find closest channeldata
            channeldata_t_js = np.array([chan.t_j for chan in self.channel])
            channeldata_v_gs = np.array([0 if chan.v_g is None else chan.v_g for chan in self.channel])
            nodes = np.array([channeldata_t_js/normalize_t_to_v, channeldata_v_gs]).transpose()
            index_channeldata = distance.cdist([node], nodes).argmin()

            # Find closest e_on
            e_ons = [e for e in self.e_on if e.dataset_type == SwitchEnergyData_dataset_type]
            if not e_ons:
                raise KeyError(f"There is no e_on data with type {SwitchEnergyData_dataset_type} for this Switch object.")
            e_on_t_js = np.array([e.t_j for e in e_ons])
            e_on_v_gs = np.array([0 if e.v_g is None else e.v_g for e in e_ons])
            nodes = np.array([e_on_t_js / normalize_t_to_v, e_on_v_gs]).transpose()
            index_e_on = distance.cdist([node], nodes).argmin()
            # Find closest e_off
            e_offs = [e for e in self.e_off if e.dataset_type == SwitchEnergyData_dataset_type]
            if not e_offs:
                raise KeyError(f"There is no e_off data with type {SwitchEnergyData_dataset_type} for this Switch object.")
            e_off_t_js = np.array([e.t_j for e in e_offs])
            e_off_v_gs = np.array([0 if e.v_g is None else e.v_g for e in e_offs])
            nodes = np.array([e_off_t_js / normalize_t_to_v, e_off_v_gs]).transpose()
            index_e_off = distance.cdist([node], nodes).argmin()
            print(f"run switch.find_approx_wp: closest working point for {t_j = } °C and {v_g = } V:")
            print(f"channel: t_j = {self.channel[index_channeldata].t_j} °C and v_g = {self.channel[index_channeldata].v_g} V")
            print(f"eon:     t_j = {e_ons[index_e_on].t_j} °C and v_g = {e_ons[index_e_on].v_g} V")
            print(f"eoff:    t_j = {e_offs[index_e_off].t_j} °C and v_g = {e_offs[index_e_off].v_g} V")

            return self.channel[index_channeldata], e_ons[index_e_on], e_offs[index_e_off]

        def plot_all_channel_data(self):
            """ Plot all channel data """
            # ToDo: only 12(?) colors available. Change linestyle for more curves.
            plt.figure()
            for i_channel in np.array(range(0, len(self.channel))):
                labelplot = f"vg {self.channel[i_channel].v_g} V, T_J = {self.channel[i_channel].t_j} °C"
                plt.plot(self.channel[i_channel].graph_v_i[0], self.channel[i_channel].graph_v_i[1], label=labelplot)

            plt.legend()
            plt.xlabel('Voltage in V')
            plt.ylabel('Current in A')
            plt.grid()
            plt.show()

        def plot_channel_data_vge(self, gatevoltage):
            """ Plot channel data with a chosen gate-voltage"""
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

        def plot_channel_data_temp(self, temperature):
            """ Plot channel data with chosen temperature"""
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

        def plot_energy_data(self):
            """ Plot all switching data """
            plt.figure()
            # look for e_on losses
            for i_energy_data in np.array(range(0, len(self.e_on))):
                if self.e_on[i_energy_data].dataset_type == 'graph_i_e':
                    labelplot = f"e_on: v_supply = {self.e_on[i_energy_data].v_supply} V, vg = {self.e_on[i_energy_data].v_g} V, T_J = {self.e_on[i_energy_data].t_j} °C, R_g = {self.e_on[i_energy_data].r_g} Ohm"
                    plt.plot(self.e_on[i_energy_data].graph_i_e[0], self.e_on[i_energy_data].graph_i_e[1],
                             label=labelplot)

            # look for e_off losses
            for i_energy_data in np.array(range(0, len(self.e_off))):
                if self.e_off[i_energy_data].dataset_type == 'graph_i_e':
                    labelplot = f"e_off: v_supply = {self.e_off[i_energy_data].v_supply} V, vg = {self.e_off[i_energy_data].v_g} V, T_J = {self.e_off[i_energy_data].t_j} °C, R_g = {self.e_off[i_energy_data].r_g} Ohm"
                    plt.plot(self.e_off[i_energy_data].graph_i_e[0], self.e_off[i_energy_data].graph_i_e[1],
                             label=labelplot)

            plt.legend()
            plt.xlabel('Current in A')
            plt.ylabel('Loss-energy in J')
            plt.grid()
            plt.show()

    class Diode():
        """Contains data associated with the (reverse) diode-characteristics of a MOSFET/SiC-MOSFET or IGBT. Can contain
         multiple channel- and e_rr- datasets."""
        # Metadata
        comment: [str, None]  # Optional
        manufacturer: [str, None]  # Optional
        technology: [str, None]  # Semiconductor technology. e.g. IGBT3/IGBT4/IGBT7  # Optional
        # These are documented in their respective class definitions.
        thermal_foster: ["FosterThermalModel", None]  # Transient thermal_foster model.
        channel: List["ChannelData"]  # Diode forward voltage and forward current data.
        e_rr: List["SwitchEnergyData"]  # Reverse recovery energy data.
        linearized_diode: List["LinearizedModel"]  # Static data. Valid for a specific operating point.
        t_j_max: [float, int]  # Unit: °C # Mandatory

        def __init__(self, diode_args):
            # Current behavior on empty 'foster' dictionary: thermal_foster object is still created but with empty
            # attributes.
            # ToDo: Is this the right behavior or should the 'thermal_foster' attribute be left empty istead?
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
                                # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
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

            else:  # Can be constructed from empty or 'None' argument dictionary since no attributes are mandatory.
                self.comment = None
                self.manufacturer = None
                self.technology = None
                self.channel = []
                self.e_rr = []
                self.linearized_diode = []

        def convert_to_dict(self):
            d = dict(vars(self))
            d['thermal_foster'] = self.thermal_foster.convert_to_dict()
            d['channel'] = [c.convert_to_dict() for c in self.channel]
            d['e_rr'] = [e.convert_to_dict() for e in self.e_rr]
            d['linearized_diode'] = [ld.convert_to_dict() for ld in self.linearized_diode]
            return d

        def find_next_gate_voltage(self, v_d, v_off, SwitchEnergyData_dataset_type="graph_i_e"):
            # recheck channel characteristics curves at v_supply
            channel_v_gs = np.array([0 if chan.v_g is None else chan.v_g for chan in self.channel])
            v_d = min(channel_v_gs, key=lambda x: abs(x-v_d))
            # recheck turn off energy loss curves at v_supply
            if self.e_rr:
                e_rrs = [e for e in self.e_rr if e.dataset_type == SwitchEnergyData_dataset_type]
                e_rr_v_gs = np.array([0 if e.v_g is None else e.v_g for e in e_rrs])
                v_off = min(e_rr_v_gs, key=lambda x: abs(x-v_off))
            print("--Diode Recheck--")
            print(f"channel: v_g = {v_d} V")
            print(f"err: v_g = {v_off} V")
            return v_d, v_off

        def find_approx_wp(self, t_j, v_g, normalize_t_to_v=10, SwitchEnergyData_dataset_type="graph_i_e"):
            """
            This function looks for the smallest distance to stored object value and returns this working point
            :param t_j: junction temperature
            :param v_g: gate voltage
            :param normalize_t_to_v: ratio between t_j and v_g. e.g. 10 means 10°C is same difference as 1V
            :return: channel-object, e_rr-object
            """
            # Normalize t_j to v_g for distance metric
            node = np.array([t_j / normalize_t_to_v, v_g])
            # Find closest channeldata
            channeldata_t_js = np.array([chan.t_j for chan in self.channel])
            channeldata_v_gs = np.array([0 if chan.v_g is None else chan.v_g for chan in self.channel])
            nodes = np.array([channeldata_t_js/normalize_t_to_v, channeldata_v_gs]).transpose()
            index_channeldata = distance.cdist([node], nodes).argmin()
            # Find closest e_rr
            e_rrs = [e for e in self.e_rr if e.dataset_type == SwitchEnergyData_dataset_type]
            if not e_rrs:
                # raise KeyError(f"There is no e_rr data with type {SwitchEnergyData_dataset_type} for this Diode object.")
                e_rrs = [None]
                index_e_rr = 0
            else:
                e_rr_t_js = np.array([e.t_j for e in e_rrs])
                e_rr_v_gs = np.array([0 if e.v_g is None else e.v_g for e in e_rrs])
                nodes = np.array([e_rr_t_js / normalize_t_to_v, e_rr_v_gs]).transpose()
                index_e_rr = distance.cdist([node], nodes).argmin()

                print(f"run diode.find_approx_wp: closest working point for {t_j = } °C and {v_g = } V:")
                print(f"channel: t_j = {self.channel[index_channeldata].t_j} °C and v_g = {self.channel[index_channeldata].v_g} V")
                print(f"err:     t_j = {e_rrs[index_e_rr].t_j} °C and v_g = {e_rrs[index_e_rr].v_g} V")

            return self.channel[index_channeldata], e_rrs[index_e_rr]

        def plot_all_channel_data(self):
            """ Plot all channel data """
            # ToDo: only 12(?) colors available. Change linestyle for more curves.
            plt.figure()
            for i_channel in np.array(range(0, len(self.channel))):
                labelplot = f"vg = {self.channel[i_channel].v_g} V, T_J = {self.channel[i_channel].t_j} °C"
                plt.plot(self.channel[i_channel].graph_v_i[0], self.channel[i_channel].graph_v_i[1], label=labelplot)

            plt.legend()
            plt.xlabel('Voltage in V')
            plt.ylabel('Current in A')
            plt.grid()
            plt.show()

        def plot_energy_data(self):
            """ Plot all switching data """

            # look for e_off losses
            if len(self.e_rr) != 0:
                plt.figure()
                for i_energy_data in np.array(range(0, len(self.e_rr))):
                    # check if data is available as 'graph_i_e'
                    if self.e_rr[i_energy_data].dataset_type == 'graph_i_e':
                        # add label plot
                        labelplot = f"e_rr: v_supply = {self.e_rr[i_energy_data].v_supply} V, T_J = {self.e_rr[i_energy_data].t_j} °C, R_g = {self.e_rr[i_energy_data].r_g} Ohm"
                        # check if gate voltage is given (GaN Transistor, SiC-MOSFET)
                        # if ture, add gate-voltage to label
                        if isinstance(self.e_rr[i_energy_data].v_g, (int, float)):
                            labelplot = labelplot + f", vg = {self.e_rr[i_energy_data].v_g} V"

                        # plot
                        plt.plot(self.e_rr[i_energy_data].graph_i_e[0], self.e_rr[i_energy_data].graph_i_e[1],
                                 label=labelplot)
                plt.legend()
                plt.xlabel('Current in A')
                plt.ylabel('Loss-energy in J')
                plt.grid()
                plt.show()
            else:
                print("No Data available")

    class LinearizedModel:
        """Contains data for a linearized Switch/Diode depending on given operating point. Operating point specified by
        t_j, i_channel and (not for all diode types) v_g."""
        t_j: [int, float]  # Unit: K # Mandatory
        v_g: [int, float, None]  # Unit: V # Mandatory for Switch, Optional for some Diode types
        i_channel: [int, float]  # Unit: A # Mandatory
        r_channel: [int, float]  # Unit: Ohm Mandatory
        v0_channel: [int, float]  # Unit: V # Mandatory

        def __init__(self, args):
            self.t_j = args.get('t_j')
            self.v_g = args.get('v_g')
            self.i_channel = args.get('i_channel')
            self.r_channel = args.get('r_channel')
            self.v0_channel = args.get('v0_channel')

        def convert_to_dict(self):
            d = dict(vars(self))
            return d

    class ChannelData:
        """Contains channel V-I data for either switch or diode. Data is given for only one junction temperature t_j.
        For different temperatures: Create additional ChannelData-objects and store them as a list in the respective
        Diode- or Switch-object.
        This data can be used to linearize the transistor at a specific operating point (ToDo!)"""

        # # Test condition: Must be given as scalar. Create additional objects for different temperatures.
        t_j: [int, float]  # Mandatory
        v_g: [int, float]  # Switch: Mandatory, Diode: optional (standard diode useless, for GaN 'diode' necessary
        # Dataset: Represented as a 2xm Matrix where row 1 is the voltage and row 2 the current.
        graph_v_i: "np.ndarray[np.float64]"  # Units: Row 1: V; Row 2: A  # Mandatory

        def __init__(self, args):
            # Validity of args is checked in the constructor of Diode/Switch class and thus does not need to be
            # checked again here.
            self.t_j = args.get('t_j')
            self.graph_v_i = args.get('graph_v_i')
            self.v_g = args.get('v_g')

        def convert_to_dict(self):
            d = dict(vars(self))
            for att_key in d:
                if isinstance(d[att_key], np.ndarray):
                    d[att_key] = d[att_key].tolist()
            return d

        def plot_graph(self):
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
        t_j: [int, float]  # Mandatory
        # Dataset: Represented as a 2xm Matrix where row 1 is the voltage and row 2 the capacitance.
        graph_v_c: "np.ndarray[np.float64]"  # Units: Row 1: V; Row 2: A  # Mandatory

        def __init__(self, args):
            # Validity of args is checked in the constructor of Diode/Switch class and thus does not need to be
            # checked again here.
            self.t_j = args.get('t_j')
            self.graph_v_c = args.get('graph_v_c')

        def convert_to_dict(self):
            d = dict(vars(self))
            for att_key in d:
                if isinstance(d[att_key], np.ndarray):
                    d[att_key] = d[att_key].tolist()
            return d

    class SwitchEnergyData:
        """Contains switching energy data for either switch or diode. The type of Energy (E_on, E_off or E_rr) is
        already implicitly specified by how the respective objects of this class are used in a Diode- or Switch-object.
        For each set (e.g. every curve in the datasheet) of switching energy data a separate object should be created.
        This also includes the reference values in a datasheet given without a graph. (Those are considered as data sets
        with just a single data point.)
        Data sets with more than one point are given as graph_i_e with an r_g parameter or as graph_r_e with an i_x
        parameter.
        Unused parameters or datasets should be left empty.
        Which of these cases (single point, E vs I dataset, E vs R dataset) is valid for the current object also needs
        to be specified by the dataset_type-property."""

        # Type of the dataset:
        # single: e_x, r_g, i_x are scalars. Given e.g. by a table in the datasheet.
        # graph_r_e: r_e is a 2-dim numpy array with two rows. i_x is a scalar. Given e.g. by an E vs R graph.
        # graph_i_e: i_e is a 2-dim numpy array with two rows. r_g is a scalar. Given e.g. by an E vs I graph.
        dataset_type: str  # Mandatory
        # Test conditions. These must be given as scalars. Create additional objects for e.g. different temperatures.
        t_j: [int, float]  # Unit: °C  # Mandatory
        v_supply: [int, float]  # Unit: V  # Mandatory
        v_g: [int, float]  # Unit: V  # Mandatory
        # Scalar dataset-parameters. Some of these can be 'None' depending on the dataset_type.
        e_x: [int, float, None]  # Unit: J
        r_g: [int, float, None]  # Unit: Ohm
        i_x: [int, float, None]  # Unit: A
        # Dataset. Only one of these is allowed. The other should be 'None'.
        graph_i_e: ["np.ndarray[np.float64]", None]  # Units: Row 1: A; Row 2: J
        graph_r_e: ["np.ndarray[np.float64]", None]  # Units: Row 1: Ohm; Row 2: J

        # ToDo: Add MOSFET capacitance. Discuss with Philipp.
        # ToDo: Add additional class for linearized switching loss model with capacitances. (See infineon application
        #  note.)
        # ToDo: Option 1: Look up table like it's currently implemented.
        # ToDo: Option 2: https://application-notes.digchip.com/070/70-41484.pdf
        # ToDO: Option 3: K_i, K_v, G_i. Add as empty class with pass.

        def __init__(self, args):
            # Validity of args is checked in the constructor of Diode/Switch class and thus does not need to be
            # checked again here.
            # ToDo: Add warning if data is ignored because of dataset_type?
            self.dataset_type = args.get('dataset_type')
            self.v_supply = args.get('v_supply')
            self.v_g = args.get('v_g')
            self.t_j = args.get('t_j')
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

        def convert_to_dict(self):
            d = dict(vars(self))
            for att_key in d:
                if isinstance(d[att_key], np.ndarray):
                    d[att_key] = d[att_key].tolist()
            return d

        def plot_graph(self):
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

    class WP:
        """
        Class WP is for user calculations in python. The user is able to linearize the channel and store the result in
        transistor.wp . Doing so, it will be easy to handle transistor objects in later calculating code.
        Always initialized as None. Always exported as None to .json or to database.
        This is a temporary workspace.
        """
        # type hints
        v_channel: [float, int, None]
        r_channel: [float, int, None]
        e_on: ["np.ndarray[np.float64]", None]  # Units: Row 1: A; Row 2: J
        e_off: ["np.ndarray[np.float64]", None]  # Units: Row 1: A; Row 2: J
        e_rr: ["np.ndarray[np.float64]", None]  # Units: Row 1: A; Row 2: J
        v_switching_ref: [float, int, None]
        e_oss: ["np.ndarray[np.float64]", None]  # Units: Row 1: V; Row 2: J
        q_oss: ["np.ndarray[np.float64]", None]  # Units: Row 1: V; Row 2: C

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

    def parallel_transistors(self, count_parallels=2):
        """
        Connect [count_parallels] transistors in parallel
        The returned transistor object behaves like a single transistor.
         - name will be modified by adding _[count_parallels]_parallel
         - channel characteristics will be modified
         - e_on/e_off/e_rr characteristics will be modified
         - thermal behaviour will be modified
        :param count_parallels: count of parallel transistors of same type
        :return: transistor object with parallel transistors
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
        transistor_dict['switch']['thermal_foster']['graph_t_rthjc'][1] = None if \
        transistor_dict['switch']['thermal_foster']['graph_t_rthjc'] is None else [x / count_parallels for x in
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
        transistor_dict['diode']['thermal_foster']['graph_t_rthjc'][1] = None if \
        transistor_dict['diode']['thermal_foster']['graph_t_rthjc'] is None else [x / count_parallels for x in
                                                                                  transistor_dict['diode'][
                                                                                      'thermal_foster'][
                                                                                      'graph_t_rthjc'][1]]

        return load_from_db(transistor_dict)

    def validate_transistor(self):
        transistor_dict = self.convert_to_dict()
        codes = {'Switch': list(),'Diode': list()}
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

    def get_curve_data(self, channel_recheck, gate_voltages):
        v_g_on, v_g_off, v_d_on, v_d_off = gate_voltages if len(gate_voltages) == 4 else \
            get_gatedefaults(self.type)
        v_g = v_g_on
        v_d = v_d_on
        transistor_dict = self.convert_to_dict()
        exception_codes = self.validate_transistor()
        is_body_diode = transistor_dict['type'].lower() in ['mosfet', 'sic-mosfet']
        # Gather switch data to fill in plecs template exporter
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
                    , "Datsheet Link : {0}".format(re.sub(r'&', '&amp;', transistor_dict['datasheet_hyperlink'])),
                    "File generated : {0}".format(datetime.datetime.today()),
                    "File generated by : https://github.com/upb-lea/transistordatabase"]
            }
            if channel_recheck:
                v_g, v_g_on, v_g_off = self.switch.find_next_gate_voltage(v_g_on, v_g_off)
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
            print(e.args[0], e.em[e.args[0]])
        # Gather diode data to fill in plecs template exporter
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
                    , "Datsheet Link : {0}".format(re.sub(r'&', '&amp;', transistor_dict['datasheet_hyperlink'])),
                    "File generated : {0}".format(datetime.datetime.today()),
                    "File generated by : https://github.com/upb-lea/transistordatabase"]
            }
            if channel_recheck:
                v_d, v_d_off = self.diode.find_next_gate_voltage(v_d_on, v_d_off)
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
            print(e.args[0], e.em[e.args[0]])
        return plecs_transistor if 'plecs_transistor' in locals() and 'Channel' in plecs_transistor['ConductionLoss'] \
                   else None, plecs_diode if 'plecs_diode' in locals() and 'Channel' in plecs_diode['ConductionLoss'] \
                   else None


def get_channel_data(channel_data, plecs_holder, v_on, is_diode, has_body_diode):
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
            plecs_holder['ConductionLoss']['TemperatureAxis'].append(channel['t_j'])  # forward characteristics are defined only at one gate voltage and doesot depend on v_supply
            plecs_holder['ConductionLoss']['Channel'].append(channel_data.tolist())
    return plecs_holder


def get_loss_curves(loss_data, plecs_holder, loss_type, v_g, is_recovery_loss):
    for energy_dict in loss_data:
        if energy_dict['v_g'] == v_g and energy_dict['dataset_type'] == 'graph_i_e' and energy_dict[
            'graph_i_e'] is not None:
            try:
                if limit_current and limit_current > max(energy_dict['graph_i_e'][0]):
                    limit_current = max(energy_dict['graph_i_e'][0])
            except NameError:
                limit_current = max(energy_dict['graph_i_e'][0])
    for energy_dict in loss_data:
        if energy_dict['v_g'] == v_g and energy_dict['dataset_type'] == 'graph_i_e' and energy_dict[
            'graph_i_e'] is not None:
            interp_current = np.linspace(0, limit_current, 20)
            loss_energy = np.interp(interp_current, energy_dict['graph_i_e'][0], energy_dict['graph_i_e'][1])
            if 'Energy' not in plecs_holder[loss_type]:
                plecs_holder[loss_type]['CurrentAxis'] = interp_current.tolist()
                plecs_holder[loss_type]['Energy'] = {}
                plecs_holder[loss_type]['TemperatureAxis'] = list()
            rev_voltage = energy_dict['v_supply'] if not is_recovery_loss else -energy_dict['v_supply']
            if rev_voltage not in plecs_holder[loss_type]['Energy'] :
                plecs_holder[loss_type]['Energy'][rev_voltage] = []
            plecs_holder[loss_type]['Energy'][rev_voltage].append(loss_energy.tolist())
            # Loss curves are defined at one v_g in many v_supply voltages, therefore to avoid redundancy in Tj and v_supply appends
            plecs_holder[loss_type]['TemperatureAxis'].append(energy_dict['t_j']) if energy_dict['t_j'] not in plecs_holder[loss_type]['TemperatureAxis'] else None
    return plecs_holder


def negate_and_append(voltage, current):
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


def get_gatedefaults(type):
    gate_voltages = {'sic-mosfet': [12, 0, 0, 12],
                     'mosfet': [12, 0, 0, 12],
                     'igbt': [15, -15, 0, 15],
                     'gan': [5, 0, 0, 5]
                     }.get(type.lower(), [15, -15, 0, 15])
    return gate_voltages


def check_realnum(x):
    """
    Check if argument is real numeric scalar. Raise TypeError if not. None is also accepted because it is valid for
    optional keys. Mandatory keys that must not contain None are checked somewhere else beforehand.
    :param x: input argument
    :return: True in case of numeric scalar.
    """
    if isinstance(x, (int, float, np.integer, np.floating)) or x is None:
        return True
    raise TypeError(f"{x} is not numeric.")


def check_2d_dataset(x):
    """
    Check if argument is real 2D-dataset of right shape. Raise TypeError if not. None is also accepted because it is
    valid for optional keys. Mandatory keys that must not contain None are checked somewhere else beforehand.
    :param x: 2d-dataset
    :return: True in case of valid 2d-dataset
    """
    if x is None:
        return True
    if isinstance(x, np.ndarray):
        if np.all(np.isreal(x)):
            if x.ndim == 2:
                if x.shape[0] == 2:
                    return True
    raise TypeError("Invalid dataset. Must be 2D-numpy array with shape (2,x) and real numeric values.")


def check_str(x):
    """
    Check if argument is string. Raise TypeError if not. Function not necessary but helpful to keep raising of errors
    consistent with other type checks. None is also accepted because it is valid for optional keys. Mandatory keys that
    must not contain None are checked somewhere else beforehand.
    :param x: input string
    :return: True in case of valid string
    """
    if isinstance(x, str) or x is None:
        return True
    raise TypeError(f"{x} is not a string.")


def csv2array(csv_filename, first_xy_to_00=False, second_y_to_0=False, first_x_to_0=False, mirror_xy_data = False):
    """
    Imports a .csv file and extracts its input to a numpy array. Delimiter in .csv file must be ';'. Both ',' or '.'
    are supported as decimal separators. .csv file can generated from a 2D-graph for example via
    https://apps.automeris.io/wpd/
    :param csv_filename: str. Insert .csv filename, e.g. "switch_channel_25_15v"
    :param first_xy_to_00: boolean True/False. Set 'True' to change the first value pair to zero. This is necessary in
        case of webplotdigitizer returns the first value pair e.g. as -0,13; 0,00349.
    :param second_y_to_0: boolean True/False. Set 'True' to set the second y-value to zero. This is interesting in
        case of diode / igbt forward channel characteristic, if you want to make sure to set the point where the ui-graph
        leaves the u axis on the u-point to zero. Otherwise there might be a very small (and negative) value of u.
    :param first_x_to_0: boolean True/False. Set 'True' to set the first x-value to zero. This is interesting in
        case of nonlinear input/output capacitances, e.g. c_oss, c_iss, c_rss
    :return: 2d array, ready to use in the transistor database
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

    if first_xy_to_00 == True:
        array[0][0] = 0  # x value
        array[0][1] = 0  # y value

    if second_y_to_0 == True:
        array[1][1] = 0  # y value

    if first_x_to_0 == True:
        array[0][0] = 0  # x value

    if mirror_xy_data == True:
        array = np.abs(array)

    return np.transpose(array)  # ToDo: Check if array needs to be transposed? (Always the case for webplotdigitizer)


def print_TDB(filters=[], collection="local"):
    """
    Print all transistorelements stored in the local database
    :param filters: filters for searching the database
    :param collection: Choose database name in local mongodb client. Default name is "collection"
    :return: Return a list with all transistor objects fitting to the search-filter
    """
    if collection == "local":
        collection = connect_local_TDB()
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
    returned_cursor = collection.find({}, filters)
    name_list = []
    for tran in returned_cursor:
        print(tran)
        name_list.append(tran['name'])
    return name_list


def connect_TDB(host):
    if host == "local":
        host = "mongodb://localhost:27017/"
    myclient = MongoClient(host)
    return myclient.transistor_database.collection


def connect_local_TDB():
    host = "mongodb://localhost:27017/"
    myclient = MongoClient(host)
    return myclient.transistor_database.collection


def load(dict_filter, collection="local"):
    """
    load a transistor from your local mongodb-database
    example:
    transistor_imported = import_json('CREE_C3M0016120K.json')
    :param dict_filter: element filter, see example
    :param collection: mongodb connection, predefined value
    :return: transistor object
    """
    if collection == "local":
        collection = connect_local_TDB()
    # ToDo: Implement case where different transistors fit the filter criterium.
    return load_from_db(collection.find_one(dict_filter))


def load_from_db(db_dict):
    """
    :param db_dict:
    :return: transistorobject
    """
    # Convert transistor_args
    transistor_args = db_dict
    if 'c_oss' in transistor_args:
        for i in range(len(transistor_args['c_oss'])):
            transistor_args['c_oss'][i]['graph_v_c'] = np.array(transistor_args['c_oss'][i]['graph_v_c'])
    if 'c_iss' in transistor_args:
        for i in range(len(transistor_args['c_iss'])):
            transistor_args['c_iss'][i]['graph_v_c'] = np.array(transistor_args['c_iss'][i]['graph_v_c'])
    if 'c_rss' in transistor_args:
        for i in range(len(transistor_args['c_rss'])):
            transistor_args['c_rss'][i]['graph_v_c'] = np.array(transistor_args['c_rss'][i]['graph_v_c'])
    if 'graph_v_ecoss' in transistor_args:
        if transistor_args['graph_v_ecoss'] is not None:
            transistor_args['graph_v_ecoss'] = np.array(transistor_args['graph_v_ecoss'])
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
    for i in range(len(switch_args['e_off'])):
        if switch_args['e_off'][i]['dataset_type'] == 'graph_r_e':
            switch_args['e_off'][i]['graph_r_e'] = np.array(switch_args['e_off'][i]['graph_r_e'])
        elif switch_args['e_off'][i]['dataset_type'] == 'graph_i_e':
            switch_args['e_off'][i]['graph_i_e'] = np.array(switch_args['e_off'][i]['graph_i_e'])
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
    return Transistor(transistor_args, switch_args, diode_args)


def update_from_fileexchange(collection="local", overwrite=True):
    """
    Update your local transitor database from transistordatabase-fileexchange from github
    :param collection: name of mongodb collection
    :param overwrite: True to overwrite existing transistor objects in local database, False to not overwrite existing transistor objects in local database.
    :return: -
    """
    print(f"Note: Please make sure that you have installed the latest version of the transistor database, especially if the update_from_fileexchange()-method ends in an error. Find the lastest version here: https://pypi.org/project/transistordatabase/")
    # Remove repo if it is already available to avoid clone error handling.
    if os.path.isdir("./cloned_repo"):
        shutil.rmtree('./cloned_repo')
    if collection == "local":
        collection = connect_local_TDB()
    repo_url = f"https://github.com/upb-lea/transistordatabase_File_Exchange"
    local_dir = "./cloned_repo"
    Repo.clone_from(repo_url, local_dir)
    for subdir, dirs, files in os.walk(local_dir):
        for file in files:
            # print(f"{os.path.join(subdir, file)}")
            filepath = subdir + os.sep + file

            if filepath.endswith(".json"):
                try:
                    transistor = import_json(filepath)
                except Exception as e:
                    print("Failed Transistor : "+filepath)
                else:
                    transistor.save(collection, overwrite)
                    print(f"Update Transistor: {transistor.name}")

    for root, dirs, files in os.walk(local_dir):
        for dir in dirs:
            os.chmod(os.path.join(root, dir), stat.S_IRWXU)
        for file in files:
            os.chmod(os.path.join(root, file), stat.S_IRWXU)
    shutil.rmtree('./cloned_repo')


def import_json(path):
    if isinstance(path, str):
        with open(path, 'r') as myfile:
            data = myfile.read()
        return load_from_db(json_util.loads(data))
    else:
        TypeError(f"{path = } ist not a string.")


def r_g_max_rapid_channel_turn_off(v_gsth, c_ds, c_gd, i_off, v_driver_off):
    """
    Calculates the maximum gate resistor to achieve no turn-off losses when working with MOSFETs
    'rapid channel turn-off' (rcto)
    Note: Input (e.g. i_off can also be a vector)
    Source: D. Kübrich, T. Dürbraum, A. Bucher:
    'Investigation of Turn-Off Behaviour under the Assumption of Linear Capacitances'
    International Conference of Power Electronics Intelligent Motion Power Quality 2006, PCIM 2006, p. 239 –244
    :param v_gsth: gate threshod voltage
    :param c_ds: equivalent drain-source capacitance
    :param c_gd: equivalent gate-drain capacitance
    :param i_off: turn-off current
    :param v_driver_off: Driver voltage during turn-off
    :return: r_g_max_rcto maxiumum gate resistor to achieve rapid channel turn-off
    """
    return (v_gsth-v_driver_off)/i_off * (1 + c_ds/c_gd)

#Export helper functions
def dict_clean(input_dict):
    """
    Cleans a python dict and makes it compatible with matlab
    Dict must be cleaned from 'None's to np.nan (= NaN in Matlab)
    see https://stackoverflow.com/questions/35985923/replace-none-in-a-python-dictionary
    :param input_dict: dictionary
    :return:
    """
    result = {}
    for key, value in input_dict:
        if value is None:
            value = np.nan
        result[key] = value
    return result

def compatibilityTest(Transistor, attribute):
    """
    checks attribute for occurrences of None an replace it with np.nan
    :param Transistor: transistor object
    :param attribute: path to given attribute
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

class MissingDataError(Exception):
    # define the error codes & messages here
    em = {1101: "Switch conduction channel information is missing, cannot export to .xml",
          1111: "Switch conduction channel information is missing at provided v_g, cannot export to .xml",
          1102: "Switch turn on loss curves do not exists at every junction temperature, cannot export to .xml",
          1103: "Switch turn off loss curves do not exists at every junction temperature, cannot export to .xml",
          1104: "Switch turn on loss information is missing",
          1105: "Switch turn off loss information is missing",
          1201: "Diode conduction channel information is missing, cannot export to .xml",
          1211: "Diode conduction channel information is missing at provided v_g, cannot export to .xml",
          1202: "Diode reverse recovery loss information is missing",
          1203: "Diode reverse recovery loss curves do not exists at every junction temperature, cannot export to .xml"}

class PDF(FPDF):
    # notes for A4 pages
    # DIN A4 is 210x297mm

    def header(self):
        title = 'virtual datasheet'
        # helvetica bold 15
        self.set_font('helvetica', 'B', 15)
        # Calculate width of title and position
        w = self.get_string_width(title) + 6
        self.set_x((210 - w) / 2)
        # Colors of frame, background and text
        self.set_draw_color(0, 80, 180)
        self.set_fill_color(230, 230, 0)
        self.set_text_color(220, 50, 50)
        # Thickness of frame (1 mm)
        self.set_line_width(1)
        # Title
        self.cell(w, 9, title, 1, 1, 'C', True)
        # Line break
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # helvetica italic 8
        self.set_font('helvetica', 'I', 8)
        # Text color in gray
        self.set_text_color(128)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')

    def chapter_title(self, num, label):
        # helvetica 12
        self.set_font('helvetica', '', 12)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 6, f'Section {num} : {label}', 0, 1, 'L', True)
        # Line break
        self.ln(4)

    def chapter_body(self, name):
        # Read text file
        with open(name, 'rb') as fh:
            txt = fh.read().decode('latin-1')
        # Times 12
        self.set_font('Times', '', 12)
        # Output justified text
        self.multi_cell(0, 5, txt)
        # Line break
        self.ln()
        # Mention in italics
        self.set_font('', 'I')
        self.cell(0, 5, '(end of excerpt)')

    def print_chapter(self, num, title, name):
        self.add_page()
        self.chapter_title(num, title)
        self.chapter_body(name)

    def figure_left(self, memfile):
        space_fig_left_right = 10
        space_fig_middle = 10
        pagewidth = 210
        figwidth = pagewidth / 2 - space_fig_middle / 2 - space_fig_left_right
        self.image(memfile, x=space_fig_left_right, y=100, w=figwidth)

    def figure_right(self, memfile):
        space_fig_left_right = 10
        space_fig_middle = 10
        pagewidth = 210
        figwidth = pagewidth / 2 - space_fig_middle / 2 - space_fig_left_right
        figright_origin = pagewidth / 2 + space_fig_middle / 2
        self.image(memfile, x=figright_origin, y=100, w=figwidth)

    def print_value(self, variable):
        # get the intial name of the value
        # copied here: https://stackoverflow.com/questions/32000934/python-print-a-variables-name-and-value
        frame = inspect.currentframe().f_back
        s = inspect.getframeinfo(frame).code_context[0]
        r = re.search(r"\((.*)\)", s).group(1)
        vnames = r.split(", ")
        #
        self.set_font('Times', '', 12)
        # Output justified text
        self.multi_cell(0, 3, f'{vnames} = {variable}')
        # Line break
        self.ln()
