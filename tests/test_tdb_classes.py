"""Unit tests for the transistor database."""
import copy
import transistordatabase as tdb
import numpy as np
import pytest
from pytest import approx
import mongomock
from unittest.mock import patch
import os
import json

################
# DEPRECATED - May not work since refactoring
################

@pytest.fixture()
def my_transistor():
    """Fixture transistor for further unit test."""
    # Values for basic example only
    name = 'Test-Transistor'
    type = 'IGBT'
    v_abs_max = 200
    i_abs_max = 200
    i_cont = 200
    author = 'Mohan Nagella'
    comment = 'test_comment'
    manufacturer = 'Fuji Electric'
    datasheet_hyperlink = 'hyperlink'
    datasheet_date = "2023-xx-xx"  # datetime.datetime.utcnow()
    datasheet_version = "1.0.0"
    housing_area = 367e-6
    cooling_area = 160e-6
    housing_type = 'TO247'
    r_th_switch_cs = 0
    r_th_diode_cs = 0
    r_th_cs = 0.05
    t_j = 25
    t_j_max = 175
    graph_v_i = np.array([[0, 0.59, 0.67, 0.75, 0.81, 0.9, 0.96, 1.07, 1.19, 1.31, 1.39, 1.51, 1.61, 1.73, 1.83, 1.9],
                          [0, 1e-03, 2.38, 5.71, 10, 19, 26.6, 40.9, 60.9, 82.3, 98.1, 120.48, 140.95, 163.33, 183.3, 198.5]])
    dataset_type_i_e = 'graph_i_e'
    dataset_type_r_e = 'graph_r_e'
    v_supply = 600
    v_g = 15
    e_x = 1
    r_g = 1
    i_x = 400
    r_th_vector = [1, 2, 3]
    r_th_total = 0.5
    c_th_vector = [1, 2, 3]
    c_th_total = 2
    tau_vector = [1, 4, 9]
    tau_total = 1
    graph_t_rthjc = np.array([[0.001, 0.00125, 0.00171, 0.00241, 0.0035, 0.00573, 0.00772, 0.01138, 0.01728, 0.03047, 0.04766, 0.07347, 0.13544, 0.24235,
                               0.53439, 1],
                              [0.03162, 0.03736, 0.04796, 0.06157, 0.07906, 0.11033, 0.13035, 0.16191, 0.20449, 0.28542, 0.35457, 0.43321, 0.51221, 0.53913,
                               0.5492, 0.55003]])
    graph_i_e = np.array([[0, 5.79, 15, 26, 38, 47, 56, 69, 81, 94, 106, 118, 133, 152, 170, 186, 200],
                          [0, 4.9e-04, 9.3e-04, 1.27e-03, 1.51e-03, 1.71e-03, 1.85e-03, 2.07e-03, 2.22e-03, 2.41e-03, 2.54e-03, 2.68e-03, 2.8e-03, 2.93e-03,
                           3.02e-03, 3.10e-03, 3.15e-03]])
    graph_r_e = np.array([[9.911100e-01, 1.403740e+00, 2.078880e+00, 3.134180e+00, 4.478810e+00, 6.997800e+00, 9.911150e+00, 1.342477e+01, 1.884490e+01,
                           2.692976e+01, 3.219229e+01],
                          [1.950000e-02, 1.947000e-02, 1.926000e-02, 1.941000e-02, 1.975000e-02, 2.028000e-02, 2.155000e-02, 2.358000e-02, 2.635000e-02,
                           2.967000e-02, 3.096000e-02]])

    graph_t_r = np.array([[-48.61961104, -29.94016048, - 16.23147015, - 2.52277982, 11.18591051, 24.89460084, 38.60329117, 52.3119815,
                           65.69427445, 79.07656739, 92.78525772, 105.51475588,
                           116.93866449, 128.03617571, 139.13368693, 147.29362165],
                          [0.89684619, 1.14140658, 1.33157082, 1.52997052, 1.75270226, 1.98628983, 2.22811286, 2.50212905, 2.81644284,
                           3.14224884, 3.46530345, 3.79703024, 4.12598987, 4.45476966,
                           4.78863606, 5.03701277]])
    graph_q_v = np.array([[0.00000000e+00, 3.12612221e-10, 5.21272373e-10, 7.29932526e-10, 9.47664859e-10, 1.16539719e-09, 1.46477915e-09,
                           1.84581073e-09, 2.22684231e-09, 2.78591544e-09,
                           2.94354458e-09, 3.22478217e-09, 3.49694759e-09, 3.76911301e-09, 4.04127842e-09, 4.31344384e-09, 4.49488745e-09],
                          [0.00000000e+0, 7.34864824e-01, 1.20581561e+00, 1.67976883e+00, 2.17153141e+00, 2.66423762e+00, 2.98759885e+00,
                           2.99104052e+00, 2.98962929e+00, 2.99726445e+00,
                           3.19787364e+00, 3.67892685e+00, 4.14972822e+00, 4.61675511e+00, 5.08453690e+00, 5.55307359e+00, 5.86870259e+00]])
    graph_i_v = np.array([[1.20259306e+00, 1.71723866e+00, 2.45212507e+00, 3.50150361e+00, 5.06397984e+00, 7.13967597e+00, 1.10896969e+01,
                           1.85389674e+01, 3.16339544e+01, 5.39785764e+01,
                           9.21063068e+01, 1.57165533e+02, 2.68179300e+02, 4.57607565e+02, 6.28968471e+02, 6.33788175e+02, 6.41087068e+02,
                           6.53439159e+02, 6.53439159e+02, 6.53439159e+02,
                           6.53439159e+02, 6.53439159e+02, 6.53439159e+02, 6.53439159e+02, 6.53439159e+02, 6.53439159e+02, 6.53439159e+02,
                           6.53439159e+02, 6.53439159e+02, 6.53439159e+02],
                          [5.10323760e+00, 7.28269824e+00, 1.03929501e+01, 1.48315100e+01, 2.12981497e+01, 3.00519626e+01, 4.66674327e+01,
                           4.80948414e+01, 4.79713287e+01, 4.80948414e+01,
                           4.80948414e+01, 4.80948414e+01, 4.80948414e+01, 4.80948414e+01, 4.61859291e+01, 2.83951494e-01, 2.08151346e+00,
                           2.89502318e+01, 2.04908911e+01, 1.45033939e+01,
                           1.02654606e+01, 7.26586360e+00, 5.14275742e+00, 3.64002895e+00, 1.29071761e+00, 9.13566221e-01, 6.46619551e-01,
                           4.57675464e-01, 1.62287110e-01, 1.16113623e-01]])
    technology = 'IGBT3'
    r_g_int = 10
    c_oss_fix = 1
    c_iss_fix = 1
    c_rss_fix = 1
    c_oss_v_c = {'t_j': t_j, 'graph_v_c': np.array([[1, 2, 4, 5, 6], [3, 4, 5, 6, 7]])}
    c_iss_v_c = {'t_j': t_j, 'graph_v_c': np.array([[1, 2, 4, 5, 6], [3, 4, 5, 6, 7]])}
    c_rss_v_c = {'t_j': t_j, 'graph_v_c': np.array([[1, 2, 4, 5, 6], [3, 4, 5, 6, 7]])}
    e_coss = np.array([[1, 2, 4, 5, 6], [3, 4, 5, 6, 7]])

    # Create dataset dictionaries
    switch_channel = {'t_j': t_j, 'graph_v_i': graph_v_i, 'v_g': v_g}
    diode_channel = {'t_j': t_j, 'graph_v_i': graph_v_i}
    switch_energy_i_e = {'dataset_type': dataset_type_i_e, 't_j': t_j, 'v_supply': v_supply, 'v_g': v_g,
                         'r_g': r_g, 'graph_i_e': graph_i_e}  # 'e_x': e_x, 'i_x': i_x,
    switch_energy_r_e = {'dataset_type': dataset_type_r_e, 't_j': t_j, 'v_supply': v_supply, 'v_g': v_g,
                         'r_g': None, 'graph_r_e': graph_r_e, 'i_x': i_x}  # 'e_x': e_x,

    foster_args = {'r_th_vector': r_th_vector, 'r_th_total': r_th_total, 'c_th_vector': c_th_vector,
                   'c_th_total': c_th_total, 'tau_vector': tau_vector, 'tau_total': tau_total,
                   'graph_t_rthjc': graph_t_rthjc}
    c_oss_er = {'c_o': 73e-12, 'v_gs': 0, 'v_ds': 400}
    c_oss_tr = None

    switch_ron_args = {
        'i_channel': 12,
        'v_g': 15,
        'dataset_type': 't_factor',
        'r_channel_nominal': 67,
        'graph_t_r': graph_t_r
    }
    switch_gate_charge = {
        'i_channel': 12.3,
        't_j': 25,
        'v_supply': 400,
        'i_g': None,
        'graph_q_v': graph_q_v
    }
    soa_object = {
        't_c': 25,
        'time_pulse': 50e-6,
        'graph_i_v': graph_i_v
    }

    # Create argument dictionaries
    transistor_args = {'name': name, 'type': type, 'author': author, 'comment': comment,
                       'manufacturer': manufacturer, 'datasheet_hyperlink': datasheet_hyperlink,
                       'datasheet_date': datasheet_date,
                       'datasheet_version': datasheet_version, 'housing_area': housing_area,
                       'cooling_area': cooling_area, 'housing_type': housing_type, 'v_abs_max': v_abs_max,
                       'i_abs_max': i_abs_max, 'i_cont': i_cont, 'c_oss_fix': c_oss_fix, 'c_iss_fix': c_iss_fix,
                       'c_rss_fix': c_rss_fix, 'c_oss': c_oss_v_c, 'c_iss': c_iss_v_c, 'c_rss': c_rss_v_c,
                       'c_oss_er': c_oss_er, 'c_oss_tr': c_oss_tr, 'graph_v_ecoss': e_coss, 'r_g_int': r_g_int, 'r_th_cs': r_th_cs,
                       'r_th_diode_cs': r_th_diode_cs, 'r_th_switch_cs': r_th_switch_cs,
                       }
    switch_args = {'t_j_max': t_j_max, 'comment': comment, 'manufacturer': manufacturer, 'technology': technology,
                   'channel': [switch_channel],
                   'e_on': [switch_energy_i_e, switch_energy_r_e], 'e_off': [switch_energy_i_e, switch_energy_r_e],
                   'thermal_foster': foster_args, 'r_channel_th': switch_ron_args, 'charge_curve': switch_gate_charge, 'soa': soa_object}
    diode_args = {'t_j_max': t_j_max, 'comment': comment, 'manufacturer': manufacturer, 'technology': technology,
                  'channel': [diode_channel], 'e_rr': [switch_energy_i_e, switch_energy_r_e], 'thermal_foster': foster_args, 'soa': soa_object}
    return transistor_args, switch_args, diode_args


def test_transistor(my_transistor):
    """
    Unit test for a test transistor.

    :param my_transistor: Transistor
    :type my_transistor: Transistor
    """
    transistor_args, switch_args, diode_args = my_transistor
    possible_housing_types = ['TO247']
    possible_module_manufacturers = ["Fuji Electric"]

    transistor = tdb.Transistor(transistor_args, switch_args, diode_args,
                                possible_housing_types=possible_housing_types,
                                possible_module_manufacturers=possible_module_manufacturers)
    # transistor_args test
    assert transistor.name == transistor_args['name']
    assert transistor.type == transistor_args['type']
    assert transistor.author == transistor_args['author']
    assert transistor.comment == transistor_args['comment']
    assert transistor.manufacturer == transistor_args['manufacturer']
    assert transistor.datasheet_hyperlink == transistor_args['datasheet_hyperlink']
    assert transistor.datasheet_date == transistor_args['datasheet_date']
    assert transistor.datasheet_version == transistor_args['datasheet_version']
    assert transistor.v_abs_max == transistor_args['v_abs_max']
    assert transistor.i_abs_max == transistor_args['i_abs_max']
    assert transistor.i_cont == transistor_args['i_cont']
    assert transistor.housing_area == transistor_args['housing_area']
    assert transistor.cooling_area == transistor_args['cooling_area']
    assert transistor.housing_type == transistor_args['housing_type']
    assert transistor.r_th_cs == transistor_args['r_th_cs']
    assert transistor.r_th_switch_cs == transistor_args['r_th_switch_cs']
    assert transistor.r_th_diode_cs == transistor_args['r_th_diode_cs']
    assert transistor.r_g_int == transistor_args['r_g_int']
    assert transistor.c_oss_fix == transistor_args['c_oss_fix']
    assert transistor.c_iss_fix == transistor_args['c_iss_fix']
    assert transistor.c_rss_fix == transistor_args['c_rss_fix']
    assert transistor.c_oss[0].t_j == transistor_args['c_oss']['t_j']
    assert transistor.c_iss[0].t_j == transistor_args['c_iss']['t_j']
    assert transistor.c_rss[0].t_j == transistor_args['c_rss']['t_j']
    assert transistor.c_oss_er.c_o == transistor_args['c_oss_er']['c_o']
    assert transistor.c_oss_er.v_gs == transistor_args['c_oss_er']['v_gs']
    assert transistor.c_oss_er.v_ds == transistor_args['c_oss_er']['v_ds']
    assert transistor.c_oss_tr == transistor_args['c_oss_tr']

    # switch_args test
    assert transistor.switch.t_j_max == switch_args['t_j_max']
    assert transistor.switch.comment == switch_args['comment']
    assert transistor.switch.manufacturer == switch_args['manufacturer']
    assert transistor.switch.technology == switch_args['technology']
    assert transistor.switch.channel[0].t_j == switch_args['channel'][0]['t_j']
    assert transistor.switch.channel[0].v_g == switch_args['channel'][0]['v_g']
    assert transistor.switch.channel[0].graph_v_i.any() == switch_args['channel'][0]['graph_v_i'].any()
    assert transistor.switch.e_on[0].graph_i_e.any() == switch_args['e_on'][0]['graph_i_e'].any()
    assert transistor.switch.e_off[0].graph_i_e.any() == switch_args['e_off'][0]['graph_i_e'].any()
    assert transistor.switch.r_channel_th[0].graph_t_r.any() == switch_args['r_channel_th']['graph_t_r'].any()
    assert transistor.switch.charge_curve[0].graph_q_v.any() == switch_args['charge_curve']['graph_q_v'].any()
    assert transistor.switch.soa[0].graph_i_v.any() == switch_args['soa']['graph_i_v'].any()

    # diode_args test
    assert transistor.diode.t_j_max == diode_args['t_j_max']
    assert transistor.diode.comment == diode_args['comment']
    assert transistor.diode.manufacturer == diode_args['manufacturer']
    assert transistor.diode.technology == diode_args['technology']
    assert transistor.diode.channel[0].t_j == diode_args['channel'][0]['t_j']
    assert transistor.diode.channel[0].graph_v_i.any() == diode_args['channel'][0]['graph_v_i'].any()
    assert transistor.diode.e_rr[0].t_j == diode_args['channel'][0]['t_j']
    assert transistor.diode.e_rr[0].graph_i_e.any() == diode_args['e_rr'][0]['graph_i_e'].any()
    assert transistor.diode.soa[0].graph_i_v.any() == diode_args['soa']['graph_i_v'].any()


def test_get_gatedefaults():
    """Unit test for get_gatedefaults."""
    igbt_expected_list = [15, -15, 0, 15]
    mos_expected_list = [10, 0, 0, 10]
    sic_expected_list = [15, -4, 0, 15]
    gan_expected_list = [6, -3, 0, 6]
    sw_type = {'123': igbt_expected_list, 'igbt': igbt_expected_list, 'mosfet': mos_expected_list,
               'sic-mosfet': sic_expected_list, 'gan-transistor': gan_expected_list}
    for key, value in sw_type.items():
        return_list = tdb.get_gatedefaults(key)
        assert return_list == value


def test_calc_thermal_params(my_transistor):
    """
    Test case for the transistor method to check if respective thermal parameters are generated or ignored as per the 4 possible handling situations.

    :param my_transistor: a fixture a load the arrange the required transistor object that goes into testing
    :type my_transistor: transistor object
    """
    transistor_args, switch_args, diode_args = my_transistor
    possible_housing_types = ['TO247']
    possible_module_manufacturers = ["Fuji Electric"]

    transistor = tdb.Transistor(transistor_args, switch_args, diode_args,
                                possible_housing_types=possible_housing_types,
                                possible_module_manufacturers=possible_module_manufacturers)
    tst_type = 'switch'
    poly_len = 3
    fixed_rth_value = 0.5
    fit_rth_vector = [0.18151, 0.18151, 0.18151]
    fit_tau_vector = [0.01142, 0.06765, 0.06766]
    fit_rth_value = sum(fit_rth_vector)
    fit_tau_value = sum(fit_tau_vector)

    # Case 0: When vectors are available irrespective of R_th_total
    transistor.switch.thermal_foster.c_th_total = None
    r_th_vector = transistor.switch.thermal_foster.r_th_vector
    r_th_total = transistor.switch.thermal_foster.r_th_total
    tau_total = transistor.switch.thermal_foster.tau_total
    transistor.calc_thermal_params(input_type=tst_type, order=poly_len)  # compute c_th_total and c_th_vector if missing
    assert transistor.switch.thermal_foster.r_th_total is r_th_total
    assert transistor.switch.thermal_foster.c_th_total == tau_total / r_th_total
    assert r_th_vector is transistor.switch.thermal_foster.r_th_vector

    # Case 1: Only rth_graph is available
    transistor.switch.thermal_foster.r_th_total = None
    transistor.switch.thermal_foster.tau_total = None
    transistor.switch.thermal_foster.r_th_vector = None
    transistor.switch.thermal_foster.tau_vector = None
    transistor.calc_thermal_params(input_type=tst_type, order=poly_len)  # reestimate all parameters from polynomial of order 3
    assert transistor.switch.thermal_foster.r_th_total == approx(fit_rth_value, 0.0001)
    assert transistor.switch.thermal_foster.c_th_total == approx(fit_tau_value / fit_rth_value, 0.001)

    # Case 2: When vectors are None and r_th_total, rth_graph is available
    transistor.switch.thermal_foster.r_th_total = fixed_rth_value
    transistor.switch.thermal_foster.r_th_vector = None
    transistor.switch.thermal_foster.tau_vector = None
    transistor.calc_thermal_params(input_type=tst_type, order=poly_len)  # re-estimate all parameters but do not overwrite r_th_total
    assert transistor.switch.thermal_foster.r_th_total is fixed_rth_value
    assert transistor.switch.thermal_foster.r_th_vector == approx(fit_rth_vector, 0.001)

    # Case 3: When r_th_vectors, rth_graph are None and r_th_total is available
    transistor.switch.thermal_foster.r_th_total = fixed_rth_value
    transistor.switch.thermal_foster.r_th_vector = None
    transistor.switch.thermal_foster.graph_t_rthjc = None
    transistor.calc_thermal_params(input_type=tst_type, order=poly_len)  # compute c_th_total if tau_total is available
    if transistor.switch.thermal_foster.tau_total is not None:
        assert transistor.switch.thermal_foster.c_th_total == transistor.switch.thermal_foster.tau_total / fixed_rth_value
    assert transistor.switch.thermal_foster.r_th_total is fixed_rth_value
    assert transistor.switch.thermal_foster.r_th_vector is None

    # Case 4: When nothing is available do nothing
    transistor.switch.thermal_foster.r_th_total = None
    transistor.switch.thermal_foster.r_th_vector = None
    transistor.switch.thermal_foster.tau_vector = None
    transistor.switch.thermal_foster.graph_t_rthjc = None
    transistor.calc_thermal_params(input_type=tst_type, order=poly_len)  # do nothing
    assert transistor.switch.thermal_foster.r_th_total is None


gecko_exporter_test_cases = [{'case': 1, 'recheck': True, 'file': 'master_data/test_data_Fuji_2MBI400XBE065-50.json', 'r_g_on': 2,
                              'r_g_off': 4, 'v_g_on': 8, 'v_g_off': -8, 'v_supply': 600},
                             {'case': 2, 'recheck': True, 'file': 'master_data/test_data_Fuji_2MBI400XBE065-50.json', 'r_g_on': None,
                              'r_g_off': None, 'v_g_on': None, 'v_g_off': None,
                              'v_supply': None},
                             {'case': 3, 'recheck': True, 'file': 'master_data/test_data_CREE_C3M0060065J.json', 'r_g_on': None,
                              'r_g_off': None, 'v_g_on': None, 'v_g_off': None, 'v_supply': None},
                             {'case': 4, 'recheck': False, 'file': 'master_data/test_data_CREE_C3M0060065J.json', 'v_g_on': 100,
                              'v_g_off': 100, 'r_g_on': None, 'r_g_off': None, 'v_supply': None}]


@pytest.fixture(params=gecko_exporter_test_cases)
def data_setup_for_gecko_exporter(request):
    """
    Fixture to arrange the required transistor object and recording the results that obtained during act operation.

    The recorded results are used for assertion.
    :param request: a dict which is provided as parameter which enacts the 4 test scenarios of the gecko exporter
    :type request:
    :return: dict with read .scl files generated after the act process
    """
    tdb_json = tdb.DatabaseManager()
    tdb_json.set_operation_mode_json()

    actual_data = {}
    actual_data['case'] = request.param['case']
    with open(request.param['file'], "r") as fd:
        transistor_test_data = tdb_json.convert_dict_to_transistor_object(json.load(fd))
    if request.param['case'] == 2:
        for index in range(len(transistor_test_data.switch.e_on) - 1, -1, -1):
            if transistor_test_data.switch.e_on[index].dataset_type == 'graph_r_e':
                del transistor_test_data.switch.e_on[index]
        for index in range(len(transistor_test_data.switch.e_off) - 1, -1, -1):
            if transistor_test_data.switch.e_off[index].dataset_type == 'graph_r_e':
                del transistor_test_data.switch.e_off[index]
        for index in range(len(transistor_test_data.diode.e_rr) - 1, -1, -1):
            if transistor_test_data.diode.e_rr[index].dataset_type == 'graph_r_e':
                del transistor_test_data.diode.e_rr[index]
    if request.param['case'] == 3:
        assert transistor_test_data.type.lower() == 'sic-mosfet'
        transistor_test_data.switch.e_on = []

    transistor_test_data.export_geckocircuits(recheck=request.param['recheck'], r_g_on=request.param['r_g_on'], r_g_off=request.param['r_g_off'],
                                              v_g_on=request.param['v_g_on'], v_g_off=request.param['v_g_off'],
                                              v_supply=request.param['v_supply'])
    for file in os.listdir():
        # Check whether file is in text format or not
        if file.endswith(".scl"):
            with open(file) as f:
                actual_data['switch' if 'Switch' in file else 'diode'] = f.read()
    yield actual_data
    # teardown code
    for file in os.listdir():
        if file.endswith(".scl"):
            os.remove(file)


def test_export_geckocircuits(data_setup_for_gecko_exporter):
    """
    Test case for the transistor method to check if the gecko exporter handles the 4 possible cases while exporting a transistor to .scl files.

    :param data_setup_for_gecko_exporter: a fixture to arrange the required transistor object and recording the results that obtained during act operation.
    :type data_setup_for_gecko_exporter: dict
    The recorded results are used for assertion
    """
    actual_data = data_setup_for_gecko_exporter
    expected = {}
    if actual_data['case'] == 1:
        with open('master_data/expected_Fuji_2MBI400XBE065-50_Switch.scl') as f:
            expected['switch'] = f.read()
        with open('master_data/expected_Fuji_2MBI400XBE065-50_Diode.scl') as f:
            expected['diode'] = f.read()
        assert expected['switch'] == actual_data['switch']
        assert expected['diode'] == actual_data['diode']

    if actual_data['case'] == 2:
        with open('master_data/expected_Fuji_2MBI400XBE065-50_Switch(rg_on_3.3)(rg_off_10).scl') as f:
            expected['switch'] = f.read()
        with open('master_data/expected_Fuji_2MBI400XBE065-50_Diode(rg_3.3).scl') as f:
            expected['diode'] = f.read()
        assert expected['switch'] == actual_data['switch']
        assert expected['diode'] == actual_data['diode']

    if actual_data['case'] == 3:
        expected_string = '\ndata[][] 3 2 0 10 0 0 0 0\ntj 25\nuBlock 400\n'
        diode_data = actual_data['diode']
        switch_data = actual_data['switch']
        actual_err = diode_data[diode_data.find(start := '<SchaltverlusteMesskurve>') + len(start):diode_data.find('<\SchaltverlusteMesskurve>')]
        actual_eon_eoff = switch_data[switch_data.find(start := '<SchaltverlusteMesskurve>') + len(start):switch_data.find('<\SchaltverlusteMesskurve>')]
        assert actual_err == expected_string
        assert actual_eon_eoff == expected_string

    if actual_data['case'] == 4:
        assert 'switch' not in actual_data
        assert 'diode' not in actual_data
    assert True


def test_export_json(my_transistor):
    """
    Pytest for export_json() function. Test for incorrect inputs.

    :param my_transistor: transistor object
    :type my_transistor: transistor object
    """
    transistor_args, switch_args, diode_args = my_transistor
    possible_housing_types = ['TO247']
    possible_module_manufacturers = ["Fuji Electric"]

    tdb_json = tdb.DatabaseManager()

    transistor = tdb.Transistor(transistor_args, switch_args, diode_args,
                                possible_housing_types=possible_housing_types,
                                possible_module_manufacturers=possible_module_manufacturers)
    tdb_json.export_single_transistor_to_json(transistor, os.path.join(os.getcwd(), "trial.json"))

    with pytest.raises(FileNotFoundError):
        tdb_json.export_single_transistor_to_json(transistor, "/not/existing/path/")


def test_check_realnum():
    """Unit test for check_realnum."""
    assert tdb.check_realnum(123)
    assert tdb.check_realnum(12.3)
    assert tdb.check_realnum(None)
    with pytest.raises(TypeError):
        tdb.check_realnum('döner')


def test_check_2d_dataset():
    """Unit test for check_2d_dataset."""
    assert tdb.check_2d_dataset(None)
    assert tdb.check_2d_dataset(np.array([[1, 2, 3], [4, 5, 6]]))
    with pytest.raises(TypeError):
        tdb.check_2d_dataset('Döner')
        tdb.check_2d_dataset(5)


def test_check_str():
    """Unit test for check_str."""
    assert tdb.check_str('Hello')
    assert tdb.check_str(None)
    with pytest.raises(TypeError):
        tdb.check_str(5)
        tdb.check_str(np.array([[1, 2], [3, 4]]))
        tdb.check_str([1, 2, 3])


@patch.object(tdb, "connect_local_tdb")
def test_connect_local_tdb(connect_local_tdb):
    """
    TDB local connection to mongodb.

    :param connect_local_tdb:
    :type connect_local_tdb:
    """
    mocked_mongo = mongomock.MongoClient()
    db = mocked_mongo['transistor_databasefake']
    connect_local_tdb.return_value = db.collection
    result = tdb.connect_local_tdb()
    assert result.full_name == db.collection.full_name


@pytest.fixture()
def my_database(my_transistor):
    """
    Fixture for unit tests.

    :param my_transistor: transistor object
    :type my_transistor: transistor object
    """
    transistor_args, switch_args, diode_args = my_transistor
    switch_args['soa'].clear()
    possible_housing_types = ['TO247']
    possible_module_manufacturers = ["Fuji Electric"]

    transistor = tdb.Transistor(transistor_args, switch_args, diode_args,
                                possible_housing_types=possible_housing_types,
                                possible_module_manufacturers=possible_module_manufacturers)

    mocked_mongo = mongomock.MongoClient()
    fake_collection = mocked_mongo['transistor_database_fake'].collection
    transistor_dict = transistor.convert_to_dict()
    fake_collection.insert_one(transistor_dict)
    yield transistor, fake_collection
    fake_collection.drop()


def test_add_soa_data(my_database, monkeypatch):
    """
    Unit test for add_soa_data.

    :param my_database: database
    :type my_database: database
    :param monkeypatch:
    :type monkeypatch:
    """
    graph_i_v_one = np.array([[1, 2, 3, 4, 5, 6], [1.2, 2.5, 3.6, 4.8, 8.2, 9.5]])
    graph_i_v_two = np.array([[1.5, 3, 3.4, 4.5, 5.8, 7], [i * 2 for i in [1.2, 2.5, 3.6, 4.8, 8.2, 9.5]]])
    graph_i_v_three = np.array([[1.5, 3, 3.4, 4.5, 5.8, 7], [i * 3 for i in [1.2, 2.5, 3.6, 4.8, 8.2, 9.5]]])
    soa_object_one = {
        't_c': 25,
        'time_pulse': None,
        'graph_i_v': graph_i_v_one
    }
    soa_object_two = {
        't_c': 25,
        'time_pulse': 50e-6,
        'graph_i_v': graph_i_v_two
    }
    soa_object_three = {
        't_c': 25,
        'time_pulse': 0.2e-6,
        'graph_i_v': graph_i_v_three
    }

    transistor, fake_collection = my_database

    soa_list_one = copy.deepcopy([soa_object_one, soa_object_two])
    transistor.add_soa_data(soa_list_one, 'switch', True)
    assert 2 == len(transistor.switch.soa)

    # deep copy is necessary as the graph_v_i in list format is modified when the add_soa_data is called
    soa_list_three = copy.deepcopy([soa_object_one, soa_object_two, soa_object_three, soa_object_one])
    transistor.add_soa_data(soa_list_three, 'switch')
    assert len(transistor.switch.soa) == 3


def test_add_gate_charge_data(my_database, monkeypatch):
    """
    Unit test for add_gate_charge_data.

    :param my_database: database
    :type my_database: database
    :param monkeypatch:
    :type monkeypatch:
    """
    graph_q_v_one = np.array([[1, 2, 3, 4, 5, 6], [1.2, 2.5, 3.6, 4.8, 8.2, 9.5]])
    graph_q_v_two = np.array([[1.5, 3, 3.4, 4.5, 5.8, 7], [i * 2 for i in [1.2, 2.5, 3.6, 4.8, 8.2, 9.5]]])

    switch_charge_curves_100 = {
        'i_channel': 12,
        't_j': 25,
        'v_supply': 100,
        'i_g': None,
        'graph_q_v': graph_q_v_one
    }

    switch_charge_curves_400 = {
        'i_channel': 12,
        't_j': 25,
        'v_supply': 400,
        'i_g': 12.2,
        'graph_q_v': graph_q_v_two
    }

    transistor, fake_collection = my_database

    def mock_return():
        return fake_collection

    qc_list_one = copy.deepcopy([switch_charge_curves_100])
    transistor.add_gate_charge_data(qc_list_one, True)
    assert 1 == len(transistor.switch.charge_curve)

    # deep copy is necessary as the graph_q_v in list format is modified when the add_gate_charge_data is called
    qc_list_three = copy.deepcopy([switch_charge_curves_400, switch_charge_curves_400, switch_charge_curves_100, switch_charge_curves_100])
    transistor.add_gate_charge_data(qc_list_three)
    assert len(transistor.switch.charge_curve) == 2


def test_add_temp_depend_resis_data(my_database, monkeypatch):
    """
    Unit test for add_temp_depend_resistor_data.

    :param my_database: database
    :type my_database: database
    :param monkeypatch:
    :type monkeypatch:
    """
    graph_t_r_one = np.array([[1, 2, 3, 4, 5, 6], [1.2, 2.5, 3.6, 4.8, 8.2, 9.5]])
    graph_t_r_two = np.array([[1.5, 3, 3.4, 4.5, 5.8, 7], [i * 2 for i in [1.2, 2.5, 3.6, 4.8, 8.2, 9.5]]])
    switch_ron_args = {
        'i_channel': 12,
        'v_g': 15,
        'dataset_type': 't_factor',
        'r_channel_nominal': 67,
        'graph_t_r': graph_t_r_one
    }
    switch_ron_args_2 = {
        'i_channel': 12,
        'v_g': 20,
        'dataset_type': 't_factor',
        'r_channel_nominal': 67,
        'graph_t_r': graph_t_r_two
    }

    transistor, fake_collection = my_database

    rth_list_one = copy.deepcopy([switch_ron_args])
    transistor.add_temp_depend_resistor_data(rth_list_one, True)
    assert 1 == len(transistor.switch.r_channel_th)

    # deep copy is necessary as the graph_t_r in list format is modified when the add_temp_depend_resis_data is called
    rth_list_three = copy.deepcopy([switch_ron_args_2, switch_ron_args_2, switch_ron_args, switch_ron_args])
    transistor.add_temp_depend_resistor_data(rth_list_three)
    assert len(transistor.switch.r_channel_th) == 2


def test_get_object_i_e_simplified(my_transistor):
    """
    Unit test for get_object_i_e_simplified.

    :param my_transistor: transistor object
    :type my_transistor: transistor object
    """
    transistor_args, switch_args, diode_args = my_transistor
    switch_energy_new = {'dataset_type': 'graph_i_e', 't_j': 25, 'v_supply': 600, 'v_g': 12,
                         'r_g': 1, 'graph_i_e': np.array([[1, 2, 3], [4, 5, 6]])}

    possible_housing_types = ['TO247']
    possible_module_manufacturers = ["Fuji Electric"]

    transistor = tdb.Transistor(transistor_args, switch_args, diode_args,
                                possible_housing_types=possible_housing_types,
                                possible_module_manufacturers=possible_module_manufacturers)

    with pytest.raises(ValueError):
        transistor.get_object_i_e_simplified("e_off", 200)
    i_e_object, r_e_object = transistor.get_object_i_e_simplified("e_off", 25)
    assert r_e_object is None
    # When i_e object list has more than one matching items at t_j
    transistor.switch.e_off.append(tdb.SwitchEnergyData(switch_energy_new))
    i_e_object, r_e_object = transistor.get_object_i_e_simplified("e_off", 25)
    assert r_e_object is not None


def test_get_object_r_e_simplified(my_transistor):
    """
    Unit test for get_object_r_e_simplified.

    :param my_transistor: transistor object
    :type my_transistor: transistor object
    """
    transistor_args, switch_args, diode_args = my_transistor
    possible_housing_types = ['TO247']
    possible_module_manufacturers = ["Fuji Electric"]

    transistor = tdb.Transistor(transistor_args, switch_args, diode_args,
                                possible_housing_types=possible_housing_types,
                                possible_module_manufacturers=possible_module_manufacturers)
    with pytest.raises(ValueError):
        transistor.get_object_r_e_simplified("e_off", 25, 15, 1000, 10)
    r_e_object = transistor.get_object_r_e_simplified("e_off", 200, 60, 600, 10)
    assert r_e_object.t_j == 25
    assert r_e_object.v_g == 15
