import unittest
import numpy as np
import datetime
from databaseClasses import Transistor


class MyTestCase(unittest.TestCase):
    # Values for basic example
    name = 'Test-Transistor'
    transistor_type = 'IGBT'
    v_max = 200
    i_max = 200
    i_cont = 200
    author = 'Manuel Klaedtke'
    comment = 'test_comment'
    manufacturer = 'Fuji'
    datasheet_hyperlink = 'hyperlink'
    datasheet_date = datetime.date.today()
    datasheet_version = "1.0.0"
    housing_area = 200
    cooling_area = 200
    housing_type = 'TO220'
    t_j = 1.0
    v_i_data = np.array([[1, 2], [3, 4]])
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
    transient_data = np.array([[1, 2], [3, 4]])
    technology = 'IGBT3'
    c_oss = 1
    c_iss = 1
    c_rss = 1
    # Create dataset dictionaries
    channel = {'t_j': t_j, 'v_i_data': v_i_data}
    switchenergy = {'dataset_type': dataset_type, 't_j': t_j, 'v_supply': v_supply, 'v_g': v_g,
                    'e_x': e_x, 'r_g': r_g, 'i_x': i_x}
    # Create argument dictionaries
    transistor_args = {'name': name, 'transistor_type': transistor_type, 'v_max': v_max,
                       'i_max': i_max, 'i_cont': i_cont}
    metadata_args = {'author': author, 'comment': comment, 'manufacturer': manufacturer,
                     'datasheet_hyperlink': datasheet_hyperlink, 'datasheet_date': datasheet_date,
                     'datasheet_version': datasheet_version, 'housing_area': housing_area,
                     'cooling_area': cooling_area, 'housing_type': housing_type}

    foster_args = {'r_th_vector': r_th_vector, 'r_th_total': r_th_total, 'c_th_vector': c_th_vector,
                   'c_th_total': c_th_total, 'tau_vector': tau_vector, 'tau_total': tau_total,
                   'transient_data': transient_data}
    switch_args = {'comment': comment, 'manufacturer': manufacturer, 'technology': technology,
                   'c_oss': c_oss, 'c_iss': c_iss, 'c_rss': c_rss, 'channel': channel,
                   'e_on': switchenergy, 'e_off': switchenergy}
    diode_args = {'comment': comment, 'manufacturer': manufacturer, 'technology': technology,
                  'channel': channel, 'e_rr': switchenergy}

    def test_basic(self):
        # Create transistor object
        transistor = Transistor(self.transistor_args, self.metadata_args, self.foster_args, self.switch_args,
                                self.diode_args)
        # Test transistor attributes
        self.assertEqual(transistor.name, self.name)
        self.assertEqual(transistor.transistor_type, self.transistor_type)
        self.assertEqual(transistor.v_max, self.v_max)
        self.assertEqual(transistor.i_max, self.i_max)
        self.assertEqual(transistor.i_cont, self.i_cont)
        # Test metadata attributes
        self.assertEqual(transistor.meta.author, self.author)
        self.assertEqual(transistor.meta.comment, self.comment)
        self.assertEqual(transistor.meta.manufacturer, self.manufacturer)
        self.assertEqual(transistor.meta.datasheet_hyperlink, self.datasheet_hyperlink)
        self.assertEqual(transistor.meta.datasheet_date, self.datasheet_date)
        self.assertEqual(transistor.meta.datasheet_version, self.datasheet_version)
        self.assertEqual(transistor.meta.housing_area, self.housing_area)
        self.assertEqual(transistor.meta.cooling_area, self.cooling_area)
        self.assertEqual(transistor.meta.housing_type, self.housing_type)
        # Test Diode attributes
        self.assertEqual(transistor.diode.comment, self.comment)
        self.assertEqual(transistor.diode.manufacturer, self.manufacturer)
        self.assertEqual(transistor.diode.technology, self.technology)
        # Test Diode channel attributes
        self.assertEqual(transistor.diode.channel[0].t_j, self.t_j)
        np.testing.assert_array_equal(transistor.diode.channel[0].v_i_data, self.v_i_data)
        # Test Diode e_rr attributes
        self.assertEqual(transistor.diode.e_rr[0].dataset_type, self.dataset_type)
        self.assertEqual(transistor.diode.e_rr[0].t_j, self.t_j)
        self.assertEqual(transistor.diode.e_rr[0].v_supply, self.v_supply)
        self.assertEqual(transistor.diode.e_rr[0].v_g, self.v_g)
        self.assertEqual(transistor.diode.e_rr[0].e_x, self.e_x)
        self.assertEqual(transistor.diode.e_rr[0].r_g, self.r_g)
        self.assertEqual(transistor.diode.e_rr[0].i_x, self.i_x)
        # Test Diode thermal attributes
        self.assertEqual(transistor.diode.thermal.r_th_vector, self.r_th_vector)
        self.assertEqual(transistor.diode.thermal.r_th_total, self.r_th_total)
        self.assertEqual(transistor.diode.thermal.c_th_vector, self.c_th_vector)
        self.assertEqual(transistor.diode.thermal.c_th_total, self.c_th_total)
        self.assertEqual(transistor.diode.thermal.tau_vector, self.tau_vector)
        self.assertEqual(transistor.diode.thermal.tau_total, self.tau_total)
        np.testing.assert_array_equal(transistor.diode.thermal.transient_data, self.transient_data)
        # Test Switch attributes
        self.assertEqual(transistor.switch.comment, self.comment)
        self.assertEqual(transistor.switch.manufacturer, self.manufacturer)
        self.assertEqual(transistor.switch.technology, self.technology)
        self.assertEqual(transistor.switch.c_oss, self.c_oss)
        self.assertEqual(transistor.switch.c_iss, self.c_iss)
        self.assertEqual(transistor.switch.c_rss, self.c_rss)
        # Test Switch channel attributes
        self.assertEqual(transistor.switch.channel[0].t_j, self.t_j)
        np.testing.assert_array_equal(transistor.switch.channel[0].v_i_data, self.v_i_data)
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
        # Test Switch thermal attributes
        self.assertEqual(transistor.switch.thermal.r_th_vector, self.r_th_vector)
        self.assertEqual(transistor.switch.thermal.r_th_total, self.r_th_total)
        self.assertEqual(transistor.switch.thermal.c_th_vector, self.c_th_vector)
        self.assertEqual(transistor.switch.thermal.c_th_total, self.c_th_total)
        self.assertEqual(transistor.switch.thermal.tau_vector, self.tau_vector)
        self.assertEqual(transistor.switch.thermal.tau_total, self.tau_total)
        np.testing.assert_array_equal(transistor.switch.thermal.transient_data, self.transient_data)


if __name__ == '__main__':
    unittest.main()
