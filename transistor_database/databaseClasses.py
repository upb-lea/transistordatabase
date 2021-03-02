import datetime
import numpy as np
import re
import os
from typing import List
from matplotlib import pyplot as plt


class Transistor():
    """Groups data of all other classes for a single transistor. Methods are specified in such a way that only
    user-interaction with this class is necessary (ToDo!)
    Documentation on how to add or extract a transistor-object to/from the database can be found in (ToDo!)
    """
    # ToDo: Add database _id as attribute
    name: str  # Name of the transistor. Choose as specific as possible. # Mandatory
    transistor_type: str  # Mandatory
    # User-specific data
    author: str  # Mandatory
    comment: [str, None]  # Optional
    # Date and template data. Should not be changed manually.
    # ToDo: Add methods to automatically determine dates and template_version on construction or update.
    template_version: str  # Mandatory/Automatic
    template_date: "datetime.date"  # Mandatory/Automatic
    creation_date: "datetime.date"  # Mandatory/Automatic
    last_modified: "datetime.date"  # Mandatory/Automatic
    # Manufacturer- and part-specific data
    manufacturer: str  # Mandatory
    datasheet_hyperlink: [str, None]  # Make sure this link is valid.  # Optional
    datasheet_date: ["datetime.date", None]  # Optional
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
    # Rated operation region
    i_cont: [float, int, None]  # Unit: A  # e.g. Fuji: I_c, Semikron: I_c,nom # Mandatory
    c_oss: List["Transistor_v_c"]  # Transistor_v_c. # Optional
    c_iss: List["Transistor_v_c"]  # Transistor_v_c. # Optional
    c_rss: List["Transistor_v_c"]  # Transistor_v_c. # Optional
    t_c_max: [float, int]  # Unit °C # Optional

    def __init__(self, transistor_args, switch_args, diode_args):
        if self.isvalid_dict(transistor_args, 'Transistor'):
            self.name = transistor_args.get('name')
            self.transistor_type = transistor_args.get('transistor_type')
            self.author = transistor_args.get('author')
            self.technology = transistor_args.get('technology')
            self.template_version = transistor_args.get('template_version')
            self.template_date = transistor_args.get('template_date')
            self.creation_date = transistor_args.get('creation_date')
            self.last_modified = transistor_args.get('last_modified')
            self.comment = transistor_args.get('comment')
            self.manufacturer = transistor_args.get('manufacturer')
            self.datasheet_hyperlink = transistor_args.get('datasheet_hyperlink')
            self.datasheet_date = transistor_args.get('datasheet_date')
            self.datasheet_version = transistor_args.get('datasheet_version')
            self.housing_area = transistor_args.get('housing_area')
            self.cooling_area = transistor_args.get('cooling_area')
            self.t_c_max = transistor_args.get('t_c_max')
            # ToDo: This is a little ugly because the file "housing_types.txt" has to be opened twice.
            # Import list of valid housing types from "housing_types.txt"
            # add housing types to the working direction
            housing_types_file = os.path.join(os.path.dirname(__file__), 'housing_types.txt')
            with open(housing_types_file, "r") as housing_types_txt:
                housing_types = [line.replace("\n", "") for line in housing_types_txt.readlines()]
            # Remove all non alphanumeric characters from housing_type names and convert to lowercase for comparison
            alphanum_housing_types = [re.sub("[^A-Za-z0-9]+", "", line).lstrip().lower() for line in housing_types]
            housing_type = transistor_args.get('housing_type')
            # Get index where the housing_type was found in "housing_types.txt"
            idx = alphanum_housing_types.index(re.sub("[^A-Za-z0-9]+", "", housing_type).lstrip().lower())
            # Don't use the name in transistor_args but the matching name in "housing_types.txt"
            self.housing_type = housing_types[idx]
            self.r_th_cs = transistor_args.get('r_th_cs')
            self.r_th_switch_cs = transistor_args.get('r_th_switch')
            self.r_th_diode_cs = transistor_args.get('r_th_diode_cs')
            self.v_abs_max = transistor_args.get('v_abs_max')
            self.i_abs_max = transistor_args.get('i_abs_max')
            self.i_cont = transistor_args.get('i_cont')
            self.c_oss = []  # Default case: Empty list
            if isinstance(transistor_args.get('c_oss'), list):
                # Loop through list and check each dict for validity. Only create Transistor_v_c objects from
                # valid dicts. 'None' and empty dicts are ignored.
                for dataset in transistor_args.get('c_oss'):
                    try:
                        if Transistor.isvalid_dict(dataset, 'Transistor_v_c'):
                            self.c_oss.append(Transistor.Transistor_v_c(dataset))
                    # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                    except KeyError as error:
                        dict_list = transistor_args.get('c_oss')
                        if not error.args:
                            error.args = ('',)  # This syntax is necessary because error.args is a tuple
                        error.args = ('KeyError occurred for index [' + str(dict_list.index(dataset)) + '] in list '
                                      'of c_oss dictionaries: ',) + error.args
                        raise
            elif Transistor.isvalid_dict(transistor_args.get('c_oss'), 'Transistor_v_c'):
                # Only create Transistor_v_c objects from valid dicts
                self.c_oss.append(Transistor.Transistor_v_c(transistor_args.get('c_oss')))

            self.c_iss = []  # Default case: Empty list
            if isinstance(transistor_args.get('c_iss'), list):
                # Loop through list and check each dict for validity. Only create Transistor_v_c objects from
                # valid dicts. 'None' and empty dicts are ignored.
                for dataset in transistor_args.get('c_iss'):
                    try:
                        if Transistor.isvalid_dict(dataset, 'Transistor_v_c'):
                            self.c_iss.append(Transistor.Transistor_v_c(dataset))
                    # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                    except KeyError as error:
                        dict_list = transistor_args.get('c_iss')
                        if not error.args:
                            error.args = ('',)  # This syntax is necessary because error.args is a tuple
                        error.args = ('KeyError occurred for index [' + str(dict_list.index(dataset)) + '] in list '
                                      'of c_iss dictionaries: ',) + error.args
                        raise
            elif Transistor.isvalid_dict(transistor_args.get('c_iss'), 'Transistor_v_c'):
                # Only create Transistor_v_c objects from valid dicts
                self.c_iss.append(Transistor.Transistor_v_c(transistor_args.get('c_iss')))

            self.c_rss = []  # Default case: Empty list
            if isinstance(transistor_args.get('c_rss'), list):
                # Loop through list and check each dict for validity. Only create Transistor_v_c objects from
                # valid dicts. 'None' and empty dicts are ignored.
                for dataset in transistor_args.get('c_rss'):
                    try:
                        if Transistor.isvalid_dict(dataset, 'Transistor_v_c'):
                            self.c_rss.append(Transistor.Transistor_v_c(dataset))
                    # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                    except KeyError as error:
                        dict_list = transistor_args.get('c_rss')
                        if not error.args:
                            error.args = ('',)  # This syntax is necessary because error.args is a tuple
                        error.args = ('KeyError occurred for index [' + str(dict_list.index(dataset)) + '] in list '
                                      'of c_rss dictionaries: ',) + error.args
                        raise
            elif Transistor.isvalid_dict(transistor_args.get('c_rss'), 'Transistor_v_c'):
                # Only create Transistor_v_c objects from valid dicts
                self.c_rss.append(Transistor.Transistor_v_c(transistor_args.get('c_rss')))
            self.e_coss = transistor_args.get('e_coss')
        else:
            # ToDo: Is this a value or a type error?
            # ToDo: Move these raises to isvalid_dict() by checking dict_type for 'None' or empty dicts?
            raise TypeError("Dictionary 'transistor_args' is empty or 'None'. This is not allowed since following keys"
                            "are mandatory: 'name', 'transistor_type', 'author', 'manufacturer', 'housing_area', "
                            "'cooling_area', 'housing_type', 'v_abs_max', 'i_abs_max', 'i_cont'")

        self.diode = self.Diode(diode_args)
        self.switch = self.Switch(switch_args)

    def __eq__(self, other):
        if not isinstance(other, Transistor):
            # don't attempt to compare against unrelated types
            return NotImplemented
        my_dict = self.convert_to_dict()
        my_dict.pop('_id', None)
        other_dict = other.convert_to_dict()
        other_dict.pop('_id', None)
        return my_dict == other_dict

    def convert_to_dict(self):  # ToDo: Convert 'datetime.date' objects before saving
        d = vars(self)
        d['diode'] = self.diode.convert_to_dict()
        d['switch'] = self.switch.convert_to_dict()
        d['c_oss'] = [c.convert_to_dict() for c in self.c_oss]
        d['c_iss'] = [c.convert_to_dict() for c in self.c_iss]
        d['c_rss'] = [c.convert_to_dict() for c in self.c_rss]
        if isinstance(self.e_coss, np.ndarray):
            d['e_coss'] = self.e_coss.tolist()
        return d

    @staticmethod
    def load_from_db(db_dict):
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
        if 'e_coss' in transistor_args:
            transistor_args['e_coss'] = np.array(transistor_args['e_coss'])
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

    @staticmethod
    def isvalid_dict(dataset_dict, dict_type):
        """This method checks input argument dictionaries for their validity. It is checked whether all mandatory keys
        are present, have the right type and permitted values (e.g. 'MOSFET' or 'IGBT' or 'SiC-MOSFET' for 'transistor_type').
        Returns 'False' if dictionary is 'None' or Empty. These cases should be handled outside this method.
        Raises appropriate errors if dictionary invalid in other ways."""
        # ToDo: Add structure for Errors. e.g.: xx has wrong type, xx has wrong type, etc.
        # ToDo: Error if given key is not allowed?
        instructions = {
            'Transistor': {
                'mandatory_keys': {'name', 'transistor_type', 'author', 'manufacturer', 'housing_area', 'cooling_area',
                                   'housing_type', 'v_abs_max', 'i_abs_max', 'i_cont'},
                'str_keys': {'name', 'transistor_type', 'author', 'manufacturer', 'housing_type'},
                'numeric_keys': {'housing_area', 'cooling_area', 'v_abs_max', 'i_abs_max', 'i_cont', 't_c_max'},
                'array_keys': {'e_coss'},
                'numeric_list_keys': {}},
            'Switch': {
                'mandatory_keys': {'r_g_int', 't_j_max'},
                'str_keys': {'comment', 'manufacturer', 'technology'},
                'numeric_keys': {'c_oss', 'c_iss', 'c_rss', 'r_g_int', 't_j_max'},
                'array_keys': {},
                'numeric_list_keys': {}},
            'Diode': {
                'mandatory_keys': {'t_j_max'},
                'str_keys': {'comment', 'manufacturer', 'technology'},
                'numeric_keys': {'t_j_max'},
                'array_keys': {},
                'numeric_list_keys': {}},
            'Switch_LinearizedModel': {
                'mandatory_keys': {'t_j', 'v_g', 'i_channel', 'r_channel', 'v0_channel'},
                'str_keys': {},
                'numeric_keys' : {'t_j', 'v_g', 'i_channel', 'r_channel', 'v0_channel'},
                'array_keys': {},
                'numeric_list_keys': {}},
            'Diode_LinearizedModel': {
                'mandatory_keys': {'t_j', 'v_g', 'i_channel', 'r_channel'},
                'str_keys': {},
                'numeric_keys': {'t_j', 'v_g', 'i_channel', 'r_channel', 'v0_channel'},
                'array_keys': {},
                'numeric_list_keys': {}},
            'ChannelData': {  # ToDo: v_g mandatory for switch, but not for diode
                'mandatory_keys': {'t_j', 'graph_v_i'},
                'numeric_keys': {'t_j'},
                'str_keys': {},
                'array_keys': {'graph_v_i'},
                'numeric_list_keys': {}},
            'SwitchEnergyData_single': {
                'mandatory_keys': {'t_j', 'v_supply', 'v_g', 'e_x', 'r_g', 'i_x'},
                'str_keys': {},
                'numeric_keys': {'t_j', 'v_supply', 'v_g', 'e_x', 'r_g', 'i_x'},
                'array_keys': {},
                'numeric_list_keys': {}},
            'SwitchEnergyData_graph_r_e': {
                'mandatory_keys': {'t_j', 'v_supply', 'v_g', 'graph_r_e', 'i_x'},
                'str_keys': {},
                'numeric_keys': {'t_j', 'v_supply', 'v_g', 'i_x'},
                'array_keys': {'graph_r_e'},
                'numeric_list_keys': {}},
            'SwitchEnergyData_graph_i_e': {
                'mandatory_keys': {'t_j', 'v_supply', 'v_g', 'graph_i_e', 'r_g'},
                'str_keys': {},
                'numeric_keys': {'t_j', 'v_supply', 'v_g', 'r_g'},
                'array_keys': {'graph_i_e'},
                'numeric_list_keys': {}},
        }
        if dataset_dict is None:
            return False  # None represents an empty dataset. Can be valid depending on circumstances, hence no error.
        elif not isinstance(dataset_dict, dict):
            raise TypeError("Expected dictionary with " + str(dict_type) + " arguments but got "
                            + str(type(dataset_dict)) + " instead.")
        elif not bool(dataset_dict):
            return False  # Empty dictionary. Can be valid depending on circumstances, hence no error.

        elif dict_type == 'ChannelData':
            # ToDo: v_g mandatory for switch, but nut for diode
            # Determine mandatory keys.
            mandatory_keys = {'t_j', 'graph_v_i'}
            # Determine types of mandatory and optional keys.
            numeric_keys = {'t_j'}  # possible keys
            numeric_keys = {numeric_key for numeric_key in numeric_keys
                            if numeric_key in list(dataset_dict.keys())}  # actual keys
            array_keys = {'graph_v_i'}  # possible keys
            array_keys = {array_key for array_key in array_keys
                          if array_key in list(dataset_dict.keys())}  # actual keys
            # Check if all mandatory keys are contained in the dict and none of the mandatory values is 'None'.
            # ToDo: First check might not even be necessary since missing keys return value 'None'?
            if not dataset_dict.keys() >= mandatory_keys or \
                    any([dataset_dict.get(mandatory_key) is None for mandatory_key in mandatory_keys]):
                raise KeyError("Dictionary does not contain all keys necessary for ChannelData object "
                               "creation. Mandatory keys: 't_j', 'graph_v_i'")
            # Check if all values have appropriate types.
            elif all([check_realnum(dataset_dict.get(numeric_key)) for numeric_key in numeric_keys]) and \
                    all([check_2d_dataset(dataset_dict.get(array_key)) for array_key in array_keys]):
                # TypeError is raised in 'check_realnum()' or 'check_2d_dataset()' if check fails.
                return True

        elif dict_type == 'SwitchEnergyData':
            if 'dataset_type' not in dataset_dict:
                raise KeyError("Dictionary does not contain 'dataset_type' key necessary for SwitchEnergyData object "
                               "creation. 'dataset_type' must be 'single', 'r_e' or 'i_e'. Check SwitchEnergyData class"
                               " for further information.")
            # Determine mandatory keys.
            elif dataset_dict.get('dataset_type') == 'single':
                mandatory_keys = {'t_j', 'v_supply', 'v_g', 'e_x', 'r_g', 'i_x'}
                # Determine types of mandatory and optional keys.
                numeric_keys = {'t_j', 'v_supply', 'v_g', 'e_x', 'r_g', 'i_x'}  # possible keys
                numeric_keys = {numeric_key for numeric_key in numeric_keys
                                if numeric_key in list(dataset_dict.keys())}  # actual keys
                array_keys = {}
            elif dataset_dict.get('dataset_type') == 'graph_r_e':
                mandatory_keys = {'t_j', 'v_supply', 'v_g', 'graph_r_e', 'i_x'}
                # Determine types of mandatory and optional keys.
                numeric_keys = {'t_j', 'v_supply', 'v_g', 'i_x'}  # possible keys
                numeric_keys = {numeric_key for numeric_key in numeric_keys
                                if numeric_key in list(dataset_dict.keys())}  # actual keys
                array_keys = {'graph_r_e'}  # possible keys
                array_keys = {array_key for array_key in array_keys
                              if array_key in list(dataset_dict.keys())}  # actual keys
            elif dataset_dict.get('dataset_type') == 'graph_i_e':
                mandatory_keys = {'t_j', 'v_supply', 'v_g', 'graph_i_e', 'r_g'}
                # Determine types of mandatory and optional keys.
                numeric_keys = {'t_j', 'v_supply', 'v_g', 'r_g'}  # possible keys
                numeric_keys = {numeric_key for numeric_key in numeric_keys
                                if numeric_key in list(dataset_dict.keys())}  # actual keys
                array_keys = {'graph_i_e'}
                array_keys = {array_key for array_key in array_keys
                              if array_key in list(dataset_dict.keys())}  # actual keys
            else:
                raise ValueError("Wrong dataset_type for creation of SwitchEnergyData object. Must be 'single', "
                                 "'graph_r_e' or 'graph_i_e'. Check SwitchEnergyData class for further "
                                 "information.")
            # Check if all mandatory keys are contained in the dict and none of the mandatory values is 'None'.
            if not dataset_dict.keys() >= mandatory_keys or \
                    any([dataset_dict.get(mandatory_key) is None for mandatory_key in mandatory_keys]):
                raise KeyError("Dictionary does not contain all keys necessary for SwitchEnergyData object "
                               "creation. Mandatory keys are documented in the SwitchEnergyData class.")
            # Check if all values have appropriate types.
            elif all([check_realnum(dataset_dict.get(numeric_key)) for numeric_key in numeric_keys]) and \
                    all([check_2d_dataset(dataset_dict.get(array_key)) for array_key in array_keys]):
                # TypeError is raised in 'check_realnum()' or 'check_2d_dataset()' if check fails.
                return True

        elif dict_type == 'Switch_LinearizedModel':
            # Determine necessary keys.
            mandatory_keys = {'t_j', 'v_g', 'i_channel', 'r_channel', 'v0_channel'}
            # Determine types of mandatory and optional keys.
            numeric_keys = {'t_j', 'v_g', 'i_channel', 'r_channel', 'v0_channel'}  # possible keys
            numeric_keys = {numeric_key for numeric_key in numeric_keys
                            if numeric_key in list(dataset_dict.keys())}  # actual keys
            # Check if all mandatory keys are contained in the dict and none of the mandatory values is 'None'.
            if not dataset_dict.keys() >= mandatory_keys or \
                    any([dataset_dict.get(mandatory_key) is None for mandatory_key in mandatory_keys]):
                raise KeyError("Dictionary does not contain all keys necessary for Switch LinearizedModel object "
                               "creation. Mandatory keys: 't_j', 'v_g', 'i_channel', 'r_channel', 'v0_channel'")
            # Check if all values have appropriate types.
            elif all([check_realnum(dataset_dict.get(numeric_key)) for numeric_key in numeric_keys]):
                # TypeError is raised in 'check_realnum()' if check fails.
                return True

        elif dict_type == 'Diode_LinearizedModel':
            # Determine mandatory keys.
            mandatory_keys = {'t_j', 'v_g', 'i_channel', 'r_channel'}
            # Determine types of mandatory and optional keys.
            numeric_keys = {'t_j', 'v_g', 'i_channel', 'r_channel', 'v0_channel'}  # possible keys
            numeric_keys = {numeric_key for numeric_key in numeric_keys
                            if numeric_key in list(dataset_dict.keys())}  # actual keys
            # Check if all mandatory keys are contained in the dict and none of the mandatory values is 'None'.
            if not dataset_dict.keys() >= mandatory_keys or \
                    any([dataset_dict.get(mandatory_key) is None for mandatory_key in mandatory_keys]):
                raise KeyError("Dictionary does not contain all keys necessary for Diode LinearizedModel object "
                               "creation. Mandatory keys: 't_j', 'v_g', 'i_channel', 'r_channel'")
            # Check if all values have appropriate types.
            elif all([check_realnum(dataset_dict.get(numeric_key)) for numeric_key in numeric_keys]):
                # TypeError is raised in 'check_realnum()' if check fails.
                return True

        elif dict_type == 'Transistor':
            # Determine mandatory keys.
            mandatory_keys = {'name', 'transistor_type', 'author', 'manufacturer', 'housing_area', 'cooling_area',
                          'housing_type', 'v_abs_max', 'i_abs_max', 'i_cont'}
            # Determine types of mandatory and optional keys.
            str_keys = {'name', 'transistor_type', 'author', 'manufacturer', 'housing_type'}  # possible keys
            str_keys = {str_key for str_key in str_keys if str_key in list(dataset_dict.keys())}  # actual keys
            numeric_keys = {'housing_area', 'cooling_area', 'v_abs_max', 'i_abs_max', 'i_cont', 't_c_max'}  # possible keys
            numeric_keys = {numeric_key for numeric_key in numeric_keys
                            if numeric_key in list(dataset_dict.keys())}  # actual keys
            array_keys = {'e_coss'}  # possible keys
            array_keys = {array_key for array_key in array_keys
                          if array_key in list(dataset_dict.keys())}  # actual keys
            # Check if all mandatory keys are contained in the dict and none of the mandatory values is 'None'.
            if not dataset_dict.keys() >= mandatory_keys or \
                    any([dataset_dict.get(mandatory_key) is None for mandatory_key in mandatory_keys]):
                raise KeyError("Dictionary 'transistor_args' does not contain all keys necessary for Transistor object "
                               "creation. Mandatory keys: 'name', 'transistor_type', 'author', 'manufacturer', "
                               "'housing_area', 'cooling_area', 'housing_type', 'v_abs_max', 'i_abs_max', 'i_cont'")
            elif dataset_dict.get('transistor_type') not in ['MOSFET', 'IGBT', 'SiC-MOSFET', 'GaN-Transistor']:
                raise ValueError("'transistor_type' must be either 'MOSFET' or 'IGBT' or 'SiC-MOSFET'")
            # Check if all values have appropriate types.
            else:
                # Import list of valid housing types from "housing_types.txt"
                housing_types_file =  os.path.join(os.path.dirname(__file__), 'housing_types.txt')
                with open(housing_types_file, "r") as housing_types_txt:
                    housing_types = [line.replace("\n", "") for line in housing_types_txt.readlines()]
                # Remove all non alphanumeric characters from housing_type names and convert to lowercase for comparison
                alphanum_housing_types = [re.sub("[^A-Za-z0-9]+", "", line).lstrip().lower() for line in housing_types]
                housing_type = dataset_dict.get('housing_type')
                if re.sub("[^A-Za-z0-9]+", "", housing_type).lstrip().lower() not in alphanum_housing_types:
                    raise ValueError("Housing type " + str(housing_type) + " is not allowed. See file "
                                     "'housing_types.txt' for a list of supported types.")
                # Check if all attributes have valid type.
                elif all([check_realnum(dataset_dict.get(numeric_key)) for numeric_key in numeric_keys]) and \
                        all([check_str(dataset_dict.get(str_key)) for str_key in str_keys]) and \
                        all([check_2d_dataset(dataset_dict.get(array_key)) for array_key in array_keys]):
                    # TypeError is raised in 'check_realnum()' or 'check_str()' or 'check_2d_dataset()' if check fails.
                    return True

        elif dict_type == 'FosterThermalModel':
            # Determine mandatory keys.
            # mandatory_keys = {}  # FosterThermalModel does not have mandatory keys.
            # Determine types of mandatory and optional keys.
            numeric_keys = {'r_th_total', 'c_th_total', 'tau_total'}  # possible keys
            numeric_keys = {numeric_key for numeric_key in numeric_keys
                            if numeric_key in list(dataset_dict.keys())}  # actual keys
            list_keys = {'r_th_vector', 'c_th_vector', 'tau_vector'}  # possible keys
            list_keys = {list_key for list_key in list_keys
                         if list_key in list(dataset_dict.keys()) and dataset_dict[list_key] is not None}  # actual keys
            array_keys = {'graph_t_rthjc'}  # possible keys
            array_keys = {array_key for array_key in array_keys
                          if array_key in list(dataset_dict.keys())}  # actual keys
            # Check if any lists are given. Otherwise some of these next checks may cause trouble
            # ToDo: This may not be the right way to handle the "empty lists" case.
            if len(list_keys) != 0:
                # Check if all elements in 'r_th_vector', 'c_th_vector', 'tau_vector' are real numeric (float, int)
                bool_list_numeric = all([all([check_realnum(single_value) for single_value in dataset_dict.get(list_key)])
                                        for list_key in list_keys])
                # Check if 'r_th_vector', 'c_th_vector', 'tau_vector' have same length
                # ToDo: Check if at least 2/3 of C, R, tau are given.
                list_sizes = [len(dataset_dict.get(list_key)) for list_key in list_keys]
                if not list_sizes.count(list_sizes[0]) == len(list_sizes):
                    raise TypeError("The lists 'r_th_vector', 'c_th_vector', 'tau_vector' (if given) must be the same "
                                    "size.")
            else:
                bool_list_numeric = True  # ToDo: This may not be the right way to handle the "empty lists" case.
            # Check if all values have appropriate types.
            if all([check_realnum(dataset_dict.get(numeric_key)) for numeric_key in numeric_keys]) and \
                    all([check_2d_dataset(dataset_dict.get(array_key)) for array_key in array_keys]) and \
                    bool_list_numeric:
                # TypeError is raised in 'check_realnum()' or 'check_2d_dataset()' if check fails.
                return True

        elif dict_type == 'Switch':
            # Determine mandatory keys.
            mandatory_keys = {'r_g_int', 't_j_max'}
            # Determine types of mandatory and optional keys.
            str_keys = {'comment', 'manufacturer', 'technology'}  # possible keys
            str_keys = {str_key for str_key in str_keys if str_key in list(dataset_dict.keys())}  # actual keys
            numeric_keys = {'c_oss', 'c_iss', 'c_rss', 'r_g_int', 't_j_max'}  # possible keys
            numeric_keys = {numeric_key for numeric_key in numeric_keys
                            if numeric_key in list(dataset_dict.keys())}  # actual keys
            # Check if all mandatory keys are contained in the dict and none of the mandatory values is 'None'.
            if not dataset_dict.keys() >= mandatory_keys or \
                    any([dataset_dict.get(mandatory_key) is None for mandatory_key in mandatory_keys]):
                raise KeyError("Dictionary 'switch_args' does not contain all keys necessary for Transistor object "
                               "creation. Mandatory keys: 'r_g_int', 't_j_max'")
            else:
                # Check if all values have appropriate types.
                if all([check_realnum(dataset_dict.get(numeric_key)) for numeric_key in numeric_keys]) and \
                        all([check_str(dataset_dict.get(str_key)) for str_key in str_keys]):
                    # TypeError is raised in 'check_realnum()' or 'check_str()' if check fails.
                    return True

        elif dict_type == 'Diode':
            # ToDo: check for mandatory keys
            # ToDo: check for numeric keys
            # Determine mandatory keys.
            mandatory_keys = {'t_j_max'}  # Diode does not have mandatory keys (yet).
            # Determine types of mandatory and optional keys.
            str_keys = {'comment', 'manufacturer', 'technology'}  # possible keys
            str_keys = {str_key for str_key in str_keys if str_key in list(dataset_dict.keys())}  # actual keys
            # Check if all values have appropriate types.
            if all([check_str(dataset_dict.get(str_key)) for str_key in str_keys]):
                # TypeError is raised in 'check_realnum()' or 'check_str()' if check fails.
                return True

        elif dict_type == 'Transistor_v_c':
            # Determine mandatory keys.
            mandatory_keys = {'t_j', 'graph_v_c'}
            # Determine types of mandatory and optional keys.
            numeric_keys = {'t_j'}  # possible keys
            numeric_keys = {numeric_key for numeric_key in numeric_keys
                            if numeric_key in list(dataset_dict.keys())}  # actual keys
            array_keys = {'graph_v_c'}  # possible keys
            array_keys = {array_key for array_key in array_keys
                          if array_key in list(dataset_dict.keys())}  # actual keys
            # Check if all mandatory keys are contained in the dict and none of the mandatory values is 'None'.
            if not dataset_dict.keys() >= mandatory_keys or \
                    any([dataset_dict.get(mandatory_key) is None for mandatory_key in mandatory_keys]):
                raise KeyError("Dictionary 'Transistor_v_c' does not contain all keys necessary for Transistor object "
                               "creation. Mandatory keys: 't_j', 'graph_v_c")
            else:
                # Check if all values have appropriate types.
                if all([check_realnum(dataset_dict.get(numeric_key)) for numeric_key in numeric_keys]) and \
                        all([check_2d_dataset(dataset_dict.get(array_key)) for array_key in array_keys]):
                        # TypeError is raised in 'check_realnum()' or 'check_2d_dataset()' if check fails.
                    return True

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
            d = vars(self)
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
        # Constant Capacitances
        c_oss: [float, int, None]  # Unit: F  # Optional
        c_iss: [float, int, None]  # Unit: F  # Optional
        c_rss: [float, int, None]  # Unit: F  # Optional
        #
        r_g_int: [float, int]  # Unit: Ohm # Mandatory
        t_j_max: [float, int]  # Unit: °C # Mandatory

        def __init__(self, switch_args):
            # Current behavior on empty 'foster' dictionary: thermal_foster object is still created but with empty attributes.
            # ToDo: Is this the right behavior or should the 'thermal_foster' attribute be left empty istead?
            self.thermal_foster = Transistor.FosterThermalModel(switch_args.get('thermal_foster'))
            if Transistor.isvalid_dict(switch_args, 'Switch'):
                self.c_oss = switch_args.get('c_oss')
                self.c_iss = switch_args.get('c_iss')
                self.c_rss = switch_args.get('c_rss')
                self.r_g_int = switch_args.get('r_g_int')
                self.t_j_max = switch_args.get('t_j_max')
                self.comment = switch_args.get('comment')
                self.manufacturer = switch_args.get('manufacturer')
                self.technology = switch_args.get('technology')
                # This currently accepts dictionaries and lists of dictionaries. Validity is only checked by keys and
                # not their values.
                self.channel = []  # Default case: Empty list
                if isinstance(switch_args.get('channel'), list):
                    # Loop through list and check each dict for validity. Only create ChannelData objects from valid
                    # dicts. 'None' and empty dicts are ignored.
                    for dataset in switch_args.get('channel'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'ChannelData'):
                                self.channel.append(Transistor.ChannelData(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = switch_args.get('channel')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = ('KeyError occurred for index [' + str(dict_list.index(dataset)) + '] in list '
                                          'of Switch-ChannelData dictionaries: ',) + error.args
                            raise
                elif Transistor.isvalid_dict(switch_args.get('channel'), 'ChannelData'):
                    # Only create ChannelData objects from valid dicts
                    self.channel.append(Transistor.ChannelData(switch_args.get('channel')))

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
                            error.args = ('KeyError occurred for index [' + str(dict_list.index(dataset)) + '] in list '
                                          'of Switch-SwitchEnergyData dictionaries for e_on: ',) + error.args
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
                            error.args = ('KeyError occurred for index [' + str(dict_list.index(dataset)) + '] in list '
                                          'of Switch-SwitchEnergyData dictionaries for e_off: ',) + error.args
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
                            error.args = ('KeyError occurred for index [' + str(dict_list.index(dataset)) + '] in list '
                                          'of Switch-LinearizedModel dictionaries: ',) + error.args
                            raise
                elif Transistor.isvalid_dict(switch_args.get('linearized_switch'), 'Switch_LinearizedModel'):
                    # Only create LinearizedModel objects from valid dicts
                    self.linearized_switch.append(Transistor.LinearizedModel(switch_args.get('linearized_switch')))

            else:  # Can be constructed from empty or 'None' argument dictionary since no attributes are mandatory.
                self.c_oss = None
                self.c_iss = None
                self.c_rss = None
                self.comment = None
                self.manufacturer = None
                self.technology = None
                self.channel = []
                self.e_on = []
                self.e_off = []
                self.linearized_switch = []

        def convert_to_dict(self):
            d = vars(self)
            d['thermal_foster'] = self.thermal_foster.convert_to_dict()
            d['channel'] = [c.convert_to_dict() for c in self.channel]
            d['e_on'] = [e.convert_to_dict() for e in self.e_on]
            d['e_off'] = [e.convert_to_dict() for e in self.e_off]
            d['linearized_switch'] = [lsw.convert_to_dict() for lsw in self.linearized_switch]
            return d

        def plot_all_channel_data(self):
            """ Plot all channel data """
            # ToDo: only 12(?) colors available. Change linestyle for more curves.
            plt.figure()
            for i_channel in np.array(range(0,len(self.channel))):
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
            for i_channel in np.array(range(0,len(self.channel))):
                if self.channel[i_channel].v_g == gatevoltage:
                    labelplot = f"vg = {self.channel[i_channel].v_g} V, T_J = {self.channel[i_channel].t_j} °C"
                    plt.plot(self.channel[i_channel].graph_v_i[0], self.channel[i_channel].graph_v_i[1], label=labelplot)

            plt.legend()
            plt.xlabel('Voltage in V')
            plt.ylabel('Current in A')
            plt.grid()
            plt.show()

        def plot_channel_data_temp(self, temperature):
            """ Plot channel data with chosen temperature"""
            plt.figure()
            for i_channel in np.array(range(0,len(self.channel))):
                if self.channel[i_channel].t_j == temperature:
                    labelplot = f"vg = {self.channel[i_channel].v_g} V, T_J = {self.channel[i_channel].t_j} °C"
                    plt.plot(self.channel[i_channel].graph_v_i[0], self.channel[i_channel].graph_v_i[1], label=labelplot)

            plt.legend()
            plt.xlabel('Voltage in V')
            plt.ylabel('Current in A')
            plt.grid()
            plt.show()

        def plot_energy_data(self):
            """ Plot all switching data """
            plt.figure()
            # look for e_on losses
            for i_energy_data in np.array(range(0,len(self.e_on))):
                if self.e_on[i_energy_data].dataset_type == 'graph_i_e':
                    labelplot = f"e_on: v_supply = {self.e_on[i_energy_data].v_supply} V, vg = {self.e_on[i_energy_data].v_g} V, T_J = {self.e_on[i_energy_data].t_j} °C, R_g = {self.e_on[i_energy_data].r_g} Ohm"
                    plt.plot(self.e_on[i_energy_data].graph_i_e[0], self.e_on[i_energy_data].graph_i_e[1], label=labelplot)

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

    class Diode:
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
                if isinstance(diode_args.get('channel'), list):
                    # Loop through list and check each dict for validity. Only create ChannelData objects from valid
                    # dicts. 'None' and empty dicts are ignored.
                    for dataset in diode_args.get('channel'):
                        try:
                            if Transistor.isvalid_dict(dataset, 'ChannelData'):
                                self.channel.append(Transistor.ChannelData(dataset))
                        # If KeyError occurs during this, raise KeyError and add index of list occurrence to the message
                        except KeyError as error:
                            dict_list = diode_args.get('channel')
                            if not error.args:
                                error.args = ('',)  # This syntax is necessary because error.args is a tuple
                            error.args = ('KeyError occurred for index [' + str(dict_list.index(dataset)) + '] in list '
                                          'of Diode-ChannelData dictionaries: ',) + error.args
                            raise
                elif Transistor.isvalid_dict(diode_args.get('channel'), 'ChannelData'):
                    # Only create ChannelData objects from valid dicts
                    self.channel.append(Transistor.ChannelData(diode_args.get('channel')))

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
                            error.args = ('KeyError occurred for index [' + str(
                                dict_list.index(dataset)) + '] in list '
                                                            'of Diode-SwitchEnergyData dictionaries for e_rr: ',) + error.args
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
                            error.args = ('KeyError occurred for index [' + str(dict_list.index(dataset)) + '] in list '
                                          'of Diode-LinearizedModel dictionaries: ',) + error.args
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
            d = vars(self)
            d['thermal_foster'] = self.thermal_foster.convert_to_dict()
            d['channel'] = [c.convert_to_dict() for c in self.channel]
            d['e_rr'] = [e.convert_to_dict() for e in self.e_rr]
            d['linearized_diode'] = [ld.convert_to_dict() for ld in self.linearized_diode]
            return d

        def plot_all_channel_data(self):
            """ Plot all channel data """
            # ToDo: only 12(?) colors available. Change linestyle for more curves.
            plt.figure()
            for i_channel in np.array(range(0,len(self.channel))):
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
            d = vars(self)
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
            d = vars(self)
            for att_key in d:
                if isinstance(d[att_key], np.ndarray):
                    d[att_key] = d[att_key].tolist()
            return d

    class Transistor_v_c:
        """Contains graph_v_c data for transistor class. Data is given for only one junction temperature t_j.
        For different temperatures: Create additional Transistor_v_c-objects and store them as a list in the transistor-object.
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
            d = vars(self)
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
            d = vars(self)
            for att_key in d:
                if isinstance(d[att_key], np.ndarray):
                    d[att_key] = d[att_key].tolist()
            return d

    def linearize_channel_ui_graph(self, t_j, v_g, i_channel, switch_or_diode):
        """Get interpolated channel parameters. This function searches for ui_graphs with the chosen t_j and v_g. At
        the desired current, the equivalent parameters for u_channel and r_channel are returned"""
        # ToDo: rethink method name. May include switch or diode as a parameter and use one global function
        # ToDo: check if this function works for all types of transistors
        # ToDo: Error handling
        # ToDo: Unittest for this method
        # in case of failure, return None
        v_channel = None
        r_channel = None

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
            if self.transistor_type in ['MOSFET', 'SiC-MOSFET']:
                # transistor has no forward voltage
                # return values
                v_channel = 0  # no forward voltage du to resistance behaviour
                r_channel = voltage_interpolated / i_channel
            else:
                # transistor has forward voltage. Other interpolating point will be with 10% more current
                # ToDo: Test this function if IGBT is available
                voltage_interpolated_2 = np.interp(i_channel * 1.1, candidate_datasets[0].graph_v_i[1],
                                                   candidate_datasets[0].graph_v_i[0])
                r_channel = (voltage_interpolated_2 - voltage_interpolated)/(0.1 * i_channel)
                v_channel = voltage_interpolated - r_channel * i_channel
        elif switch_or_diode == 'diode':
            if self.transistor_type in ['SiC-MOSFET', 'GaN-Transistor']:
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
            voltage_interpolated_2 = np.interp(i_channel * 1.1, candidate_datasets[0].graph_v_i[1],
                                               candidate_datasets[0].graph_v_i[0])
            r_channel = (voltage_interpolated_2 - voltage_interpolated) / (0.1 * i_channel)
            v_channel = voltage_interpolated - r_channel * i_channel
        else:
            raise ValueError("switch_or_diode must be either specified as 'switch' or 'diode' for channel "
                             "linearization.")
        return round(v_channel, 2), round(r_channel, 4)


def check_realnum(x):
    """Check if argument is real numeric scalar. Raise TypeError if not. None is also accepted because it is valid for
    optional keys. Mandatory keys that must not contain None are checked somewhere else beforehand."""
    if not any([isinstance(x, int), isinstance(x, float), x is None, isinstance(x, np.integer),
                isinstance(x, np.floating)]):
        raise TypeError('{0} is not numeric.'.format(x))
    else:
        return True


def check_2d_dataset(x):
    """Check if argument is real 2D-dataset of right shape. Raise TypeError if not. None is also accepted because it is
    valid for optional keys. Mandatory keys that must not contain None are checked somewhere else beforehand."""
    if isinstance(x, np.ndarray):
        if np.all(np.isreal(x)):
            if x.ndim == 2:
                if x.shape[0] == 2:
                    return True
    elif x is None:
        return True
    raise TypeError("Invalid dataset. Must be 2D-numpy array with shape (2,x) and real numeric values.")


def check_str(x):
    """Check if argument is string. Raise TypeError if not. Function not necessary but helpful to keep raising of errors
    consistent with other type checks. None is also accepted because it is valid for optional keys. Mandatory keys that
    must not contain None are checked somewhere else beforehand."""
    if isinstance(x, str) or x is None:
        return True
    raise TypeError('{0} is not a string.'.format(x))


def csv2array(csv_filename, set_first_value_to_zero, set_second_y_value_to_zero, set_first_x_value_to_zero):
    """Imports a .csv file and extracts its input to a numpy array. Delimiter in .csv file must be ';'. Both ',' or '.'
    are supported as decimal separators. .csv file can generated from a 2D-graph for example via
    https://apps.automeris.io/wpd/

    csv_filename: str. Insert .csv filename, e.g. "switch_channel_25_15v"

    set_first_value_to_zero: boolean True/False. Set 'True' to change the first value pair to zero. This is necessary in
        case of webplotdigitizer returns the first value pair e.g. as -0,13; 0,00349.

    set_second_y_value_to_zero: boolean True/False. Set 'True' to set the second y-value to zero. This is interesting in
        case of diode / igbt forward channel characteristic, if you want to make sure to set the point where the ui-graph
        leaves the u axis on the u-point to zero. Otherwise there might be a very small (and negative) value of u.

    set_first_x_value_to_zero: boolean True/False. Set 'True' to set the first x-value to zero. This is interesting in
        case of nonlinear input/output capacitances, e.g. c_oss, c_iss, c_rss
    """
    array = np.genfromtxt(csv_filename, delimiter=";",
                          converters={0: lambda s: float(s.decode("UTF-8").replace(",", ".")),
                                      1: lambda s: float(s.decode("UTF-8").replace(",", "."))})

    if set_first_value_to_zero == True:
        array[0][0] = 0    # x value
        array[0][1] = 0    # y value

    if set_second_y_value_to_zero == True:
        array[1][1] = 0    # y value

    if set_first_x_value_to_zero == True:
        array[0][0] = 0    # x value

    return np.transpose(array)  # ToDo: Check if array needs to be transposed? (Always the case for webplotdigitizer)
