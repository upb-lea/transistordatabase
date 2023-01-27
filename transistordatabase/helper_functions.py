# Python standard libraries
from __future__ import annotations
from typing import List, Dict
from matplotlib import pyplot as plt
import numpy as np
import warnings
import os
import re
import pathlib

# Third party libraries
from bson.objectid import ObjectId

# Local libraries
from transistordatabase.checker_functions import check_realnum, check_str, check_2d_dataset
from transistordatabase.mongodb_handling import connect_local_tdb

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

    :Example: (e.g. merges c_oss curve from 0-200V and from 0-1000V)

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


def print_tdb(filters: List[str] | None = None, collection_name: str = "local") -> List[str]:
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
    >>> tdb.print_tdb()
    >>> # or
    >>> tdb.print_tdb(collection = 'type')
    """
    # Note: Never use mutable default arguments
    # see https://florimond.dev/en/posts/2018/08/python-mutable-defaults-are-the-source-of-all-evil/
    # This is the better solution
    filters = filters or []

    if collection_name == "local":
        mongodb_collection = connect_local_tdb()
    else:
        # TODO: support other collections. As of now, other database connections also connects to local-tdb
        warnings.warn("Connection of other databases than the local on not implemented yet. Connect so local database")
        mongodb_collection = connect_local_tdb()
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


def r_g_max_rapid_channel_turn_off(v_gsth: float, c_ds: float, c_gd: float, i_off: float | List[float],
                                   v_driver_off: float) -> float:
    """
    Calculates the maximum gate resistor to achieve no turn-off losses when working with MOSFETs
    'rapid channel turn-off' (rcto)

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

    .. note::
        Input (e.g. i_off can also be a vector)

    .. seealso::
        D. Kubrick, T. Dürbaum, A. Bucher
        'Investigation of Turn-Off Behaviour under the Assumption of Linear Capacitances'
        International Conference of Power Electronics Intelligent Motion Power Quality 2006, PCIM 2006, p. 239 –244
    """
    return (v_gsth - v_driver_off) / i_off * (1 + c_ds / c_gd)


def compare_list(parameter: List):
    """
    check through the list of value for odd one out.
    """
    for i, j in enumerate(parameter[:-1]):
        if j != parameter[i + 1]:
            return False
    return True


def compare_plot(transistor_list: List, temperature: float, gatevoltage: float):
    fig1, axs = plt.subplots(3, 2, sharex='row', sharey='row')

    for transistor in transistor_list:
        transistor.update_wp(temperature, gatevoltage, transistor.i_cont)

        # plot forward characteristics
        axs[1, 0].plot(transistor.wp.switch_channel.graph_v_i[0], transistor.wp.switch_channel.graph_v_i[1],
                       label=transistor.name)
        axs[1, 1].plot(transistor.wp.diode_channel.graph_v_i[0], transistor.wp.diode_channel.graph_v_i[1],
                       label=transistor.name)

        # plot energy losses
        axs[0, 0].plot(transistor.wp.e_on.graph_i_e[0], transistor.wp.e_on.graph_i_e[1], label=transistor.name)
        axs[0, 1].plot(transistor.wp.e_off.graph_i_e[0], transistor.wp.e_off.graph_i_e[1], label=transistor.name)

        # plot energy in c_oss
        if transistor.graph_v_ecoss is not None:
            axs[2, 0].plot(transistor.graph_v_ecoss[0], transistor.graph_v_ecoss[1], label=transistor.name)

    axs[0, 0].set_title('Turn-on')
    axs[0, 0].legend()
    axs[0, 0].grid()
    axs[0, 0].set_xlabel('Current in A')
    axs[0, 0].set_ylabel('Eon in J')

    axs[0, 1].set_title('Turn-off')
    axs[0, 1].legend()
    axs[0, 1].grid()
    axs[0, 1].set_xlabel('Current in A')
    axs[0, 1].set_ylabel('Eoff in J')

    axs[1, 0].set_title('Switch forward characteristic')
    axs[1, 0].legend()
    axs[1, 0].grid()
    axs[1, 0].set_xlabel('Voltage in V')
    axs[1, 0].set_ylabel('Current in A')

    axs[1, 1].set_title('Diode forward characteristic')
    axs[1, 1].legend()
    axs[1, 1].grid()
    axs[1, 1].set_xlabel('Voltage in V')
    axs[1, 1].set_ylabel('Current in A')

    axs[2, 0].set_title('Energy in C_oss')
    axs[2, 0].legend()
    axs[2, 0].grid()
    axs[2, 0].set_xlabel('Voltage in V')
    axs[2, 0].set_ylabel('Energy in J')
    plt.tight_layout()
    plt.show()


def isvalid_dict(dataset_dict: Dict, dict_type: str) -> bool:
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

