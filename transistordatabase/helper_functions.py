"""Helper functions."""
# Python standard libraries
from __future__ import annotations
from matplotlib import pyplot as plt
from PyQt5 import QtWidgets, QtWebEngineWidgets
import xml.etree.ElementTree as et
import numpy as np
import sys
import os
import re
import base64
import io
import logging

# Third party libraries
from bson.objectid import ObjectId

# Local libraries
from transistordatabase.checker_functions import check_realnum, check_str, check_2d_dataset
from transistordatabase.constants import *

logger = logging.getLogger(__name__)

transistor_name_regex = "(\S*)( \((\d*)\))?"


# ==== Validation functions ====
def isvalid_transistor_name(transistor_name: str) -> bool:
    """
    Check if the given transistor name is valid.

    :param transistor_name: transistor name
    :type transistor_name: str
    :return: True in case of the transistor name is valid
    :rtype: bool
    """
    return False if re.match(transistor_name_regex, transistor_name) is None else True

def isvalid_dict(dataset_dict: dict, dict_type: str) -> bool:
    """
    Check input argument dictionaries for their validity.

    It is checked whether all mandatory keys
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
                             'r_th_diode_cs', 'r_g_on_recommended', 'r_g_off_recommended'},
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
        'SwitchEnergyData_graph_t_e': {
            'mandatory_keys': {'v_supply', 'v_g', 'graph_t_e', 'r_g', 'i_x'},
            'str_keys': {},
            'numeric_keys': {'v_supply', 'v_g', 'r_g', 'i_x'},
            'array_keys': {'graph_t_e'}},
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
        text_file_dict = {'manufacturer': r'data/module_manufacturers.txt', 'housing_type': r'data/housing_types.txt'}
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
                        housing_file_path = os.path.join(os.path.dirname(__file__), 'housing_types.txt')
                        raise ValueError('{} {} is not allowed. The supported {}s are\n {} \n See file {} for a list of supported housing types.'.format(
                            name, dataset_value, name, alphanum_values, housing_file_path))
                    elif name == 'Manufacturer':
                        module_file_path = os.path.join(os.path.dirname(__file__), 'module_manufacturers.txt')
                        raise ValueError(
                            '{} {} is not allowed. The supported {}s are\n {} \n See file {} for a list of supported module manufacturers.'.format(
                                name, dataset_value, name, alphanum_values, module_file_path))

    if dict_type == 'SwitchEnergyData':
        if dataset_dict.get('dataset_type') not in ['single', 'graph_r_e', 'graph_i_e', 'graph_t_e']:
            raise KeyError("Dictionary does not contain 'dataset_type' key necessary for SwitchEnergyData object "
                           "creation. 'dataset_type' must be 'single', 'graph_r_e', 'graph_i_e' or graph_t_e. "
                           "Check SwitchEnergyData class for further information.")
        if dataset_dict['dataset_type'] == 'single':
            dict_type = 'SwitchEnergyData_single'
        if dataset_dict['dataset_type'] == 'graph_r_e':
            dict_type = 'SwitchEnergyData_graph_r_e'
        if dataset_dict['dataset_type'] == 'graph_i_e':
            dict_type = 'SwitchEnergyData_graph_i_e'
        if dataset_dict['dataset_type'] == 'graph_t_e':
            dict_type = 'SwitchEnergyData_graph_t_e'

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

def matlab_compatibility_test(transistor, attribute):
    """
    Check attribute for occurrences of None an replace it with np.nan.

    .. todo: This function might can be replaced by dict_clean()

    :param transistor: transistor object
    :type transistor: Transistor
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
    

# ==== Input/Output ====
def get_xml_data(file: str) -> dict:
    """
    Import_xml_data method to extract the xml file data i.e turn on/off energies, channel data, foster thermal data. Helper function.

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
            if character_node.tag == '{' + namespaces['plecs'] + '}' + 'TurnOnLoss' and \
                    character_node.find('plecs:ComputationMethod', namespaces).text.lower() == 'table only':
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

            if character_node.tag == '{' + namespaces['plecs'] + '}' + 'TurnOffLoss' and \
                    character_node.find('plecs:ComputationMethod', namespaces).text.lower() == 'table only':
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

            if character_node.tag == '{' + namespaces['plecs'] + '}' + 'ConductionLoss' and \
                    character_node.find('plecs:ComputationMethod', namespaces).text.lower() == 'table only':
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
            foster_args['r_th_total'], foster_args['tau_total'] = (r_par[0], tau_par[0]) if len(r_par) == 1 else (sum(foster_args['r_th_vector']),
                                                                                                                  sum(foster_args['tau_vector']))
        return info, energy_on_list, energy_off_list, channel_list, foster_args
    else:
        raise ImportError('Import of ' + file + ' Not possible: Only table type xml data are accepted')

def read_data_file(file_path: str):
    """
    Read data from a given file (Used for housing_types.txt and module_manufacturers.txt).

    :param file_path: Path to housing_types.txt and/or module_manufacturers.txt
    :type file_path: str
    """
    if not os.path.isfile(file_path):
        raise Exception(f"File {file_path} does not exist.")
    
    data = []

    with open(file_path, "r") as fd:
        for line in fd.read().splitlines():
            if line.startswith("#") or line.isspace() or not line:
                continue

            data.append(str(line))

    return data

def html_to_pdf(html: List | str, name: List | str, path: List | str):
    """
    Convert the generated html document to pdf file using qt WebEngineWidgets tool. Helper method.

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
        logger.info(f"Export virtual datasheet {name_item} to {os.getcwd()}")
        logger.info(f"Open Datasheet here: {os.getcwd()}")
        if not fetch_next():
            app.quit()

    def handle_load_finished(status):
        if status:
            nonlocal path_item
            page.printToPdf(path_item)
        else:
            logger.info("Failed")
            app.quit()

    page.pdfPrintingFinished.connect(handle_print_finished)
    page.loadFinished.connect(handle_load_finished)
    if isinstance(html, list):
        html_and_paths = iter(zip(html, name, path))
    else:
        html_and_paths = iter(zip([html], [name], [path]))
    fetch_next()
    app.exec_()


# ==== Plot ====
def get_vc_plots(cap_data: dict):
    """
    Plot and convert voltage dependant capacitance plots in raw data format. Invoked internally by export_datasheet() method. Helper function.

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

def compare_plot(transistor_list: list, temperature: float, gatevoltage: float):
    """Compare transistors.

    - forward characteristics
    - turn-on energies
    - turn-off energies
    - c_oss
    :param transistor_list: list of transistors
    :type transistor_list: list
    :param temperature: junction temperature in °C
    :type temperature: float
    :param gatevoltage: gate voltage
    :type gatevoltage: float
    """
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


# === Data ===
def get_gatedefaults(transistor_type: str) -> list:
    """
    Define gate voltage defaults depending on the transistor type.

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

def negate_and_append(voltage: list, current: list) -> tuple[list, np.array]:
    """
    Negate the channel current x-axis data for the transistors of type mosfet. Helper function.

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

def get_loss_curves(loss_data: list, plecs_holder: dict, loss_type: str, v_g: int, is_recovery_loss: bool) -> dict:
    """
    Extract loss information of switch/diode for plecs exporter. Called internally by get_curve_data() for using plecs exporter feature. Helper function.

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
            plecs_holder[loss_type]['TemperatureAxis'].append(energy_dict['t_j']) \
                if energy_dict['t_j'] not in plecs_holder[loss_type]['TemperatureAxis'] else None
    return plecs_holder

def get_channel_data(channel_data: list, plecs_holder: dict, v_on: int, is_diode: bool, has_body_diode: bool) -> dict:
    """
    Extract channel data of switch/diode for plecs exporter. Called internally by get_curve_data() for using plecs exporter feature. Helper function.

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
            # forward characteristics are defined only at one gate voltage and does not depend on v_supply
            plecs_holder['ConductionLoss']['TemperatureAxis'].append(channel['t_j'])
            plecs_holder['ConductionLoss']['Channel'].append(channel_data.tolist())
    return plecs_holder

def gen_exp_func(order: int):
    """
    Generate the required ordered function for curve fitting. A helper function to calc_thermal_params method.

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
        return lambda t, rn, tau, rn2, tau2, rn3, tau3, rn4, \
            tau4: rn * (1 - np.exp(-t / tau)) + rn2 * (1 - np.exp(-t / tau2)) + rn3 * (1 - np.exp(-t / tau3)) + rn4 * (1 - np.exp(-t / tau4))
    elif order == 5:
        return lambda t, rn, tau, rn2, tau2, rn3, tau3, rn4, tau4, rn5, \
            tau5: rn * (1 - np.exp(-t / tau)) + rn2 * (1 - np.exp(-t / tau2)) + rn3 * (1 - np.exp(-t / tau3)) + rn4 * \
            (1 - np.exp(-t / tau4)) + rn5 * (1 - np.exp(-t / tau5))

def merge_curve(curve: np.array, curve_detail: np.array) -> np.array:
    """
    Merge two equal curves, one of which contains an enlarged section of the first curve.

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

def r_g_max_rapid_channel_turn_off(v_gsth: float, c_ds: float, c_gd: float, i_off: float | list[float],
                                   v_driver_off: float) -> float:
    """
    Calculate the maximum gate resistor to achieve no turn-off losses when working with MOSFETs 'rapid channel turn-off' (rcto).

    :param v_gsth: gate threshold voltage
    :type v_gsth: float
    :param c_ds: equivalent drain-source capacitance
    :type c_ds: float
    :param c_gd: equivalent gate-drain capacitance
    :type c_gd: float
    :param i_off: turn-off current
    :type i_off: float or list[float]
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

def compare_list(parameter: list):
    """
    Check through the list of value for odd one out.

    :param parameter:
    :type parameter: list
    """
    for i, j in enumerate(parameter[:-1]):
        if j != parameter[i + 1]:
            return False
    return True

def get_copy_transistor_name(current_name: str) -> str:
    """
    Return the current name but with an index at the end similar to windows copies.

    :param current_name: name of transistor
    :type current_name: str

    '{current_name} (i)'
    """
    result = re.match(transistor_name_regex, current_name)
    if len(result.groups) == 2:
        # Name is default-name -> ' (1)' will be added.
        return f"{current_name} (1)"
    elif len(result.group) == 4:
        # Name is already a copy-name -> Copy number will be raised
        index = result.group(4)
        return f"{current_name[-2]}{index+1})"
    else:
        raise Exception(f"Given transistor name {current_name} is not a valid name and therefore a copy-name cannot be created.")

def get_img_raw_data(plot):
    """
    Convert the plot images to raw data which is further used to display plots in virtual datasheet. Helper method.

    :param plot: pyplot object
    :type plot: plt.Figure

    :return: decoded raw image data to utf-8
    """
    buf = io.BytesIO()
    plot.gcf().set_size_inches(3.5, 2.2)
    plot.savefig(buf, format='png', bbox_inches='tight')
    encoded_img_data = base64.b64encode(buf.getvalue())
    plot.close()
    return encoded_img_data.decode('UTF-8')
