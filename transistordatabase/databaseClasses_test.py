import unittest
import numpy as np
import datetime
from databaseClasses import Transistor


class MyTestCase(unittest.TestCase):
    # Values for basic example
    name = 'Test-Transistor'
    type = 'IGBT'
    v_abs_max = 200
    i_abs_max = 200
    i_cont = 200
    author = 'Manuel Klaedtke'
    comment = 'test_comment'
    manufacturer = 'Fuji'
    datasheet_hyperlink = 'hyperlink'
    datasheet_date = datetime.datetime.utcnow()
    datasheet_version = "1.0.0"
    housing_area = 200
    cooling_area = 200
    housing_type = 'TO220'
    t_j = 1.0
    t_j_max = 10
    graph_v_i = np.array([[1, 2], [3, 4]])
    dataset_type = 'single'
    v_supply = 1
    v_g = 1
    e_x = 1
    r_g = 1
    i_x = 1
    r_th_vector = [1, 2, 3]
    r_th_total = 6
    c_th_vector = [1, 2, 3]
    c_th_total = 6
    tau_vector = [1, 4, 9]
    tau_total = 14
    graph_t_rthjc = np.array([[1, 2], [3, 4]])
    technology = 'IGBT3'
    r_g_int = 10
    c_oss_fix = 1
    c_iss_fix = 1
    c_rss_fix = 1
    c_oss_v_c = {'t_j': t_j, 'graph_v_c': np.array([[1, 2], [3, 4]])}
    c_iss_v_c = {'t_j': t_j, 'graph_v_c': np.array([[1, 2], [3, 4]])}
    c_rss_v_c = {'t_j': t_j, 'graph_v_c': np.array([[1, 2], [3, 4]])}
    e_coss = np.array([[1, 2], [3, 4]])
    # Create dataset dictionaries
    switch_channel = {'t_j': t_j, 'graph_v_i': graph_v_i, 'v_g': v_g}
    diode_channel = {'t_j': t_j, 'graph_v_i': graph_v_i}
    switchenergy = {'dataset_type': dataset_type, 't_j': t_j, 'v_supply': v_supply, 'v_g': v_g,
                    'e_x': e_x, 'r_g': r_g, 'i_x': i_x}
    foster_args = {'r_th_vector': r_th_vector, 'r_th_total': r_th_total, 'c_th_vector': c_th_vector,
                   'c_th_total': c_th_total, 'tau_vector': tau_vector, 'tau_total': tau_total,
                   'graph_t_rthjc': graph_t_rthjc}
    # Create argument dictionaries
    transistor_args = {'name': name, 'type': type, 'author': author, 'comment': comment,
                       'manufacturer': manufacturer, 'datasheet_hyperlink': datasheet_hyperlink,
                       'datasheet_date': datasheet_date,
                       'datasheet_version': datasheet_version, 'housing_area': housing_area,
                       'cooling_area': cooling_area, 'housing_type': housing_type, 'v_abs_max': v_abs_max,
                       'i_abs_max': i_abs_max, 'i_cont': i_cont, 'c_oss_fix': c_oss_fix, 'c_iss': c_iss_fix,
                       'c_rss': c_rss_fix, 'c_oss': c_oss_v_c, 'c_iss': c_iss_v_c, 'c_rss': c_rss_v_c,
                       'graph_v_ecoss': e_coss, 'r_g_int': r_g_int}
    switch_args = {'t_j_max': t_j_max, 'comment': comment, 'manufacturer': manufacturer, 'technology': technology,
                   'channel': switch_channel,
                   'e_on': switchenergy, 'e_off': switchenergy, 'thermal_foster': foster_args}
    diode_args = {'t_j_max': t_j_max,'comment': comment, 'manufacturer': manufacturer, 'technology': technology,
                  'channel': diode_channel, 'e_rr': switchenergy, 'thermal_foster': foster_args}

    def test_basic(self):
        # Create transistor object
        transistor = Transistor(self.transistor_args, self.switch_args, self.diode_args)
        # Test transistor attributes
        self.assertEqual(transistor.name, self.name)
        self.assertEqual(transistor.type, self.type)
        self.assertEqual(transistor.author, self.author)
        self.assertEqual(transistor.comment, self.comment)
        self.assertEqual(transistor.manufacturer, self.manufacturer)
        self.assertEqual(transistor.datasheet_hyperlink, self.datasheet_hyperlink)
        self.assertEqual(transistor.datasheet_date, self.datasheet_date)
        self.assertEqual(transistor.datasheet_version, self.datasheet_version)
        self.assertEqual(transistor.housing_area, self.housing_area)
        self.assertEqual(transistor.cooling_area, self.cooling_area)
        self.assertEqual(transistor.housing_type, self.housing_type)
        self.assertEqual(transistor.v_abs_max, self.v_abs_max)
        self.assertEqual(transistor.i_abs_max, self.i_abs_max)
        self.assertEqual(transistor.i_cont, self.i_cont)
        self.assertEqual(transistor.c_oss_fix, self.c_oss_fix)
        self.assertEqual(transistor.c_oss_fix, self.c_oss_fix)
        self.assertEqual(transistor.c_oss_fix, self.c_oss_fix)
        self.assertEqual(transistor.c_oss[0].t_j, self.c_oss_v_c['t_j'])
        self.assertEqual(transistor.c_iss[0].t_j, self.c_iss_v_c['t_j'])
        self.assertEqual(transistor.c_rss[0].t_j, self.c_rss_v_c['t_j'])
        self.assertEqual(transistor.r_g_int, self.r_g_int)
        np.testing.assert_array_equal(transistor.c_oss[0].graph_v_c, self.c_oss_v_c['graph_v_c'])
        np.testing.assert_array_equal(transistor.c_iss[0].graph_v_c, self.c_iss_v_c['graph_v_c'])
        np.testing.assert_array_equal(transistor.c_rss[0].graph_v_c, self.c_rss_v_c['graph_v_c'])
        np.testing.assert_array_equal(transistor.graph_v_ecoss, self.e_coss)
        # Test Diode attributes
        self.assertEqual(transistor.diode.comment, self.comment)
        self.assertEqual(transistor.diode.manufacturer, self.manufacturer)
        self.assertEqual(transistor.diode.technology, self.technology)
        # Test Diode channel attributes
        self.assertEqual(transistor.diode.channel[0].t_j, self.t_j)
        np.testing.assert_array_equal(transistor.diode.channel[0].graph_v_i, self.graph_v_i)
        # Test Diode e_rr attributes
        self.assertEqual(transistor.diode.e_rr[0].dataset_type, self.dataset_type)
        self.assertEqual(transistor.diode.e_rr[0].t_j, self.t_j)
        self.assertEqual(transistor.diode.e_rr[0].v_supply, self.v_supply)
        self.assertEqual(transistor.diode.e_rr[0].v_g, self.v_g)
        self.assertEqual(transistor.diode.e_rr[0].e_x, self.e_x)
        self.assertEqual(transistor.diode.e_rr[0].r_g, self.r_g)
        self.assertEqual(transistor.diode.e_rr[0].i_x, self.i_x)
        # Test Diode thermal_foster attributes
        self.assertEqual(transistor.diode.t_j_max, self.t_j_max)
        self.assertEqual(transistor.diode.thermal_foster.r_th_vector, self.r_th_vector)
        self.assertEqual(transistor.diode.thermal_foster.r_th_total, self.r_th_total)
        self.assertEqual(transistor.diode.thermal_foster.c_th_vector, self.c_th_vector)
        self.assertEqual(transistor.diode.thermal_foster.c_th_total, self.c_th_total)
        self.assertEqual(transistor.diode.thermal_foster.tau_vector, self.tau_vector)
        self.assertEqual(transistor.diode.thermal_foster.tau_total, self.tau_total)
        np.testing.assert_array_equal(transistor.diode.thermal_foster.graph_t_rthjc, self.graph_t_rthjc)
        # Test Switch attributes
        self.assertEqual(transistor.switch.t_j_max, self.t_j_max)
        self.assertEqual(transistor.switch.comment, self.comment)
        self.assertEqual(transistor.switch.manufacturer, self.manufacturer)
        self.assertEqual(transistor.switch.technology, self.technology)
        # Test Switch channel attributes
        self.assertEqual(transistor.switch.channel[0].t_j, self.t_j)
        np.testing.assert_array_equal(transistor.switch.channel[0].graph_v_i, self.graph_v_i)
        # Test Switch e_on attributes
        self.assertEqual(transistor.switch.e_on[0].dataset_type, self.dataset_type)
        self.assertEqual(transistor.switch.e_on[0].t_j, self.t_j)
        self.assertEqual(transistor.switch.e_on[0].v_supply, self.v_supply)
        self.assertEqual(transistor.switch.e_on[0].v_g, self.v_g)
        self.assertEqual(transistor.switch.e_on[0].e_x, self.e_x)
        self.assertEqual(transistor.switch.e_on[0].r_g, self.r_g)
        self.assertEqual(transistor.switch.e_on[0].i_x, self.i_x)
        # Test Switch e_off attributes
        self.assertEqual(transistor.switch.e_off[0].dataset_type, self.dataset_type)
        self.assertEqual(transistor.switch.e_off[0].t_j, self.t_j)
        self.assertEqual(transistor.switch.e_off[0].v_supply, self.v_supply)
        self.assertEqual(transistor.switch.e_off[0].v_g, self.v_g)
        self.assertEqual(transistor.switch.e_off[0].e_x, self.e_x)
        self.assertEqual(transistor.switch.e_off[0].r_g, self.r_g)
        self.assertEqual(transistor.switch.e_off[0].i_x, self.i_x)
        # Test Switch thermal_foster attributes
        self.assertEqual(transistor.switch.thermal_foster.r_th_vector, self.r_th_vector)
        self.assertEqual(transistor.switch.thermal_foster.r_th_total, self.r_th_total)
        self.assertEqual(transistor.switch.thermal_foster.c_th_vector, self.c_th_vector)
        self.assertEqual(transistor.switch.thermal_foster.c_th_total, self.c_th_total)
        self.assertEqual(transistor.switch.thermal_foster.tau_vector, self.tau_vector)
        self.assertEqual(transistor.switch.thermal_foster.tau_total, self.tau_total)
        np.testing.assert_array_equal(transistor.switch.thermal_foster.graph_t_rthjc, self.graph_t_rthjc)


if __name__ == '__main__':
    unittest.main()
