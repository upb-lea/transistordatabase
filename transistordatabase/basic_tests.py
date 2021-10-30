# import numpy as np
# import databaseClasses as dC
# from databaseClasses import Transistor
#
# transistor_args = {"name": "Test-Transistor", "type": 'MOSFET', "v_max": 200, "i_max": 200, 'i_cont': 200, "author": "Manuel Klaedtke", "manufacturer": "Fuji", "housing_area": 200, "cooling_area": 200,
#                  "housing_type": "TO-220"}
# metadata_args = {"author": "Manuel Klaedtke", "manufacturer": "Fuji", "housing_area": 200, "cooling_area": 200,
#                  "housing_type": "TO-220"}
# channel1 = {"t_j": 1.0,
#             "graph_v_i": np.array([[1, 2],
#                                   [3, 4]])}
# channel2 = {"t_j": 2.0,
#             "graph_v_i": np.array([[1, 2],
#                                   [3, 4]])}
#
# switchenergy1 = {'dataset_type': 'single', 't_j': 1, 'v_supply': 1, 'v_g': 1, 'e_x': 1, 'r_g': 1, 'i_x': 1}
# switchenergy2 = {'dataset_type': 'graph_r_e', 't_j': 1, 'v_supply': 1, 'v_g': 1, 'graph_r_e': np.array([[1, 2], [3, 4]]),
#                  'i_x': 1}
# switchenergies = [switchenergy1, switchenergy2]
# channels = [channel1, channel2]
# foster_args = dict()
#
# dpt_safe_dict = {'path': 'C:/Users/Henning/Documents/Sciebo/Bachelorarbeit/Messungen DPT/Henning/GaN-Systems/400V/*.csv',
#                  'load_l': 750,
#                  'measurement_date': 10092021,
#                  'measurement_testbench': 'LEA-UPB Testbench',
#                  'v_g': 18,
#                  'v_g_off': 0,
#                  'energies': None,
#                  'integration_interval': 'IEC 60747-8'}
#
# dpt_energies = dC.dpt_safe_data(dpt_safe_dict)
#
# switch_args = {'channel': channels, 'e_off_meas': dpt_energies['e_off_meas'], 'e_on_meas': dpt_energies['e_on_meas']}
# diode_args = {'channel': channel1, 'e_rr': switchenergies}
#
# testTransistor = Transistor(transistor_args, switch_args, diode_args)
# # testTransistor2 = Transistor()
# # testTransistor3 = Transistor(transistor_args,metadata_args)

import databaseClasses as dC

import transistordatabase as tdb
import numpy as np
import datetime
import pytest
from pytest import approx

#@pytest.fixture()
def my_transistor():
   # Values for basic example
    name = 'Test-Transistor'
    type = 'IGBT'
    v_abs_max = 200
    i_abs_max = 200
    i_cont = 200
    author = 'Mohan Nagella'
    comment = 'test_comment'
    manufacturer = 'Fuji Electric'
    datasheet_hyperlink = 'hyperlink'
    datasheet_date = datetime.datetime.utcnow()
    datasheet_version = "1.0.0"
    housing_area = 367e-6
    cooling_area = 160e-6
    housing_type = 'TO247'
    r_th_switch_cs = 0
    r_th_diode_cs = 0
    r_th_cs = 0.05
    t_j = 25
    t_j_max = 175
    graph_v_i = np.array([[0, 0.59, 0.67, 0.75, 0.81, 0.9,  0.96, 1.07, 1.19, 1.31, 1.39, 1.51, 1.61, 1.73, 1.83, 1.9],
                          [0, 1e-03, 2.38, 5.71, 10, 19, 26.6, 40.9, 60.9, 82.3, 98.1, 120.48, 140.95, 163.33, 183.3, 198.5]])
    dataset_type = 'single'
    v_supply = 600
    v_g = 15
    e_x = 1
    r_g = 1
    i_x = 1
    r_th_vector = [1, 2, 3]
    r_th_total = 0.5
    c_th_vector = [1, 2, 3]
    c_th_total = 2
    tau_vector = [1, 4, 9]
    tau_total = 1
    graph_t_rthjc = np.array([[0.001, 0.00125, 0.00171, 0.00241, 0.0035,  0.00573, 0.00772, 0.01138, 0.01728, 0.03047, 0.04766, 0.07347, 0.13544, 0.24235, 0.53439, 1],
                              [0.03162, 0.03736, 0.04796, 0.06157, 0.07906, 0.11033, 0.13035, 0.16191, 0.20449, 0.28542, 0.35457, 0.43321, 0.51221, 0.53913, 0.5492, 0.55003]])
    graph_i_e = [[0, 5.79, 15, 26, 38, 47, 56, 69, 81, 94, 106, 118, 133, 152, 170, 186, 200],
        [0, 4.9e-04, 9.3e-04, 1.27e-03, 1.51e-03, 1.71e-03, 1.85e-03, 2.07e-03, 2.22e-03, 2.41e-03, 2.54e-03, 2.68e-03, 2.8e-03, 2.93e-03, 3.02e-03, 3.10e-03, 3.15e-03]]
    technology = 'IGBT3'
    r_g_int = 10
    c_oss_fix = 1
    c_iss_fix = 1
    c_rss_fix = 1
    c_oss_v_c = {'t_j': t_j, 'graph_v_c': np.array([[1, 2, 4, 5, 6], [3, 4, 5, 6, 7]])}
    c_iss_v_c = {'t_j': t_j, 'graph_v_c': np.array([[1, 2, 4, 5, 6], [3, 4, 5, 6, 7]])}
    c_rss_v_c = {'t_j': t_j, 'graph_v_c': np.array([[1, 2, 4, 5, 6], [3, 4, 5, 6, 7]])}
    e_coss = np.array([[1, 2, 4, 5, 6], [3, 4, 5, 6, 7]])


    dpt_safe_dict = {
        'path': 'C:/Users/Henning/Documents/Sciebo/Bachelorarbeit/Messungen DPT/Henning/ROHM/*.csv',
        'dataset_type': 'graph_i_e',
        'load_l': 750,
        'measurement_date': 10092021,
        'measurement_testbench': 'LEA-UPB Testbench',
        'v_g': 18,
        'v_g_off': 0,
        'energies': 'both',
        'integration_interval': 'IEC 60747-8'}

    dpt_energies_dict = dC.dpt_safe_data(dpt_safe_dict)

    # Create dataset dictionaries
    switch_channel = {'t_j': t_j, 'graph_v_i': graph_v_i, 'v_g': v_g}
    diode_channel = {'t_j': t_j, 'graph_v_i': graph_v_i}
    switchenergy = {'dataset_type': dataset_type, 't_j': t_j, 'v_supply': v_supply, 'v_g': v_g,
                    'e_x': e_x, 'r_g': r_g, 'i_x': i_x, 'graph_i_e': graph_i_e}
    foster_args = {'r_th_vector': r_th_vector, 'r_th_total': r_th_total, 'c_th_vector': c_th_vector,
                   'c_th_total': c_th_total, 'tau_vector': tau_vector, 'tau_total': tau_total,
                   'graph_t_rthjc': graph_t_rthjc}
    # Create argument dictionaries
    transistor_args = {'name': name, 'type': type, 'author': author, 'comment': comment,
                       'manufacturer': manufacturer, 'datasheet_hyperlink': datasheet_hyperlink,
                       'datasheet_date': datasheet_date,
                       'datasheet_version': datasheet_version, 'housing_area': housing_area,
                       'cooling_area': cooling_area, 'housing_type': housing_type, 'v_abs_max': v_abs_max,
                       'i_abs_max': i_abs_max, 'i_cont': i_cont, 'c_oss_fix': c_oss_fix, 'c_iss_fix': c_iss_fix,
                       'c_rss': c_rss_fix, 'c_oss': c_oss_v_c, 'c_iss': c_iss_v_c, 'c_rss': c_rss_v_c,
                       'graph_v_ecoss': e_coss, 'r_g_int': r_g_int, 'r_th_cs': r_th_cs, 'r_th_diode_cs': r_th_diode_cs,
                       'r_th_switch_cs': r_th_switch_cs, 'raw_measurement_data': dpt_energies_dict['dpt_raw_data']}
    switch_args = {'t_j_max': t_j_max, 'comment': comment, 'manufacturer': manufacturer, 'technology': technology,
                   'channel': switch_channel, 'e_on': switchenergy, 'e_off': switchenergy,
                   'e_off_meas': dpt_energies_dict['e_off_meas'], 'e_on_meas': dpt_energies_dict['e_on_meas'],
                   'thermal_foster': foster_args}
    diode_args = {'t_j_max': t_j_max, 'comment': comment, 'manufacturer': manufacturer, 'technology': technology,
                  'channel': [diode_channel], 'e_rr': switchenergy, 'thermal_foster': foster_args}
    return transistor_args, switch_args, diode_args


transistor_args, switch_args, diode_args = my_transistor()
print(switch_args)
transistor = dC.Transistor(transistor_args, switch_args, diode_args)

print(transistor.switch.e_on_meas)
