import transistordatabase as tdb
import numpy as np
import datetime
import pytest
from pytest import approx

@pytest.fixture()
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
                       'graph_v_ecoss': e_coss, 'r_g_int': r_g_int,'r_th_cs':r_th_cs , 'r_th_diode_cs': r_th_diode_cs, 'r_th_switch_cs': r_th_switch_cs}
    switch_args = {'t_j_max': t_j_max, 'comment': comment, 'manufacturer': manufacturer, 'technology': technology,
                   'channel': switch_channel,
                   'e_on': switchenergy, 'e_off': switchenergy, 'thermal_foster': foster_args}
    diode_args = {'t_j_max': t_j_max, 'comment': comment, 'manufacturer': manufacturer, 'technology': technology,
                  'channel': [diode_channel], 'e_rr': switchenergy, 'thermal_foster': foster_args}
    return transistor_args, switch_args, diode_args


def test_calc_thermal_params(my_transistor):
    """
    Test case for the transistor method to check if respective thermal parameters are generated or ignored
    as per the 4 possible handling situations

    :param my_transistor: a fixture a load the arrange the required transistor object that goes into testing

    :return: assertion based result
    """
    transistor_args, switch_args, diode_args = my_transistor
    transistor = tdb.Transistor(transistor_args, switch_args, diode_args)
    tst_type = 'switch'
    poly_len = 3
    fixed_rth_value = 0.5
    fit_rth_vector = [0.06413, 0.3, 0.18463]
    fit_tau_vector = [0.00255, 0.04281, 0.06846]
    fit_rth_value = sum(fit_rth_vector)
    fit_tau_value = sum(fit_tau_vector)

    # Case 0: When vectors are available irrespective of R_th_total
    transistor.switch.thermal_foster.c_th_total = None
    r_th_vector = transistor.switch.thermal_foster.r_th_vector
    r_th_total = transistor.switch.thermal_foster.r_th_total
    tau_total = transistor.switch.thermal_foster.tau_total
    transistor.calc_thermal_params(input_type=tst_type, order=poly_len)  # compute c_th_total and c_th_vector if missing
    assert transistor.switch.thermal_foster.r_th_total is r_th_total
    assert transistor.switch.thermal_foster.c_th_total == tau_total/r_th_total
    assert r_th_vector is transistor.switch.thermal_foster.r_th_vector


    # Case 1: Only rth_graph is available
    transistor.switch.thermal_foster.r_th_total = None
    transistor.switch.thermal_foster.tau_total = None
    transistor.switch.thermal_foster.r_th_vector = None
    transistor.switch.thermal_foster.tau_vector = None
    transistor.calc_thermal_params(input_type=tst_type, order=poly_len)  # reestimate all parameters from polynomial of order 3
    assert transistor.switch.thermal_foster.r_th_total == approx(fit_rth_value, 0.0001)
    assert transistor.switch.thermal_foster.c_th_total == approx(fit_tau_value/fit_rth_value, 0.0001)


    # Case 2: When vectors are None and r_th_total, rth_graph is available
    transistor.switch.thermal_foster.r_th_total = fixed_rth_value
    transistor.switch.thermal_foster.r_th_vector = None
    transistor.switch.thermal_foster.tau_vector = None
    transistor.calc_thermal_params(input_type=tst_type, order=poly_len)  # re-estimate all parameters but do not overwrite r_th_total
    assert transistor.switch.thermal_foster.r_th_total is fixed_rth_value
    assert transistor.switch.thermal_foster.r_th_vector == approx(fit_rth_vector, 0.0001)

    # Case 3: When r_th_vectors, rth_graph are None and r_th_total is available
    transistor.switch.thermal_foster.r_th_total = fixed_rth_value
    transistor.switch.thermal_foster.r_th_vector = None
    transistor.switch.thermal_foster.graph_t_rthjc = None
    transistor.calc_thermal_params(input_type=tst_type, order=poly_len)   # compute c_th_total if tau_total is available
    if transistor.switch.thermal_foster.tau_total is not None:
        assert transistor.switch.thermal_foster.c_th_total == transistor.switch.thermal_foster.tau_total/fixed_rth_value
    assert transistor.switch.thermal_foster.r_th_total is fixed_rth_value
    assert transistor.switch.thermal_foster.r_th_vector is None

    # Case 4: When nothing is available do nothing
    transistor.switch.thermal_foster.r_th_total = None
    transistor.switch.thermal_foster.r_th_vector = None
    transistor.switch.thermal_foster.tau_vector = None
    transistor.switch.thermal_foster.graph_t_rthjc = None
    transistor.calc_thermal_params(input_type=tst_type, order=poly_len)  # do nothing
    assert transistor.switch.thermal_foster.r_th_total is None

