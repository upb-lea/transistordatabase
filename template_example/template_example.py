"""See how to create a transistor object."""
# imports
import transistordatabase as tdb
import os
import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


# Template to generate a transistor
def template_example(database):
    """
    Template to create a transistor object.

    :param database: database
    :type database:
    """
    ####################################
    # transistor parameters
    ####################################

    c_iss_normal = tdb.csv2array('transistor_c_iss.csv', first_x_to_0=True)
    c_iss_detail = tdb.csv2array('transistor_c_iss_detail.csv', first_x_to_0=True)

    c_oss_normal = tdb.csv2array('transistor_c_oss.csv', first_x_to_0=True)
    c_oss_detail = tdb.csv2array('transistor_c_oss_detail.csv', first_x_to_0=True)

    c_rss_normal = tdb.csv2array('transistor_c_rss.csv', first_x_to_0=True)
    c_rss_detail = tdb.csv2array('transistor_c_rss_detail.csv', first_x_to_0=True)

    soa_t_pulse_100ms = {'t_c': 25, 'time_pulse': 100e-3, 'graph_i_v': tdb.csv2array('soa_t_pulse_100ms.csv')}
    soa_t_pulse_1ms = {'t_c': 25, 'time_pulse': 1e-3, 'graph_i_v': tdb.csv2array('soa_t_pulse_1ms.csv')}
    soa_t_pulse_100us = {'t_c': 25, 'time_pulse': 100e-6, 'graph_i_v': tdb.csv2array('soa_t_pulse_100us.csv')}
    soa_t_pulse_10us = {'t_c': 25, 'time_pulse': 10e-6, 'graph_i_v': tdb.csv2array('soa_t_pulse_10us.csv')}

    c_iss_merged = tdb.merge_curve(c_iss_normal, c_iss_detail)
    c_oss_merged = tdb.merge_curve(c_oss_normal, c_oss_detail)
    c_rss_merged = tdb.merge_curve(c_rss_normal, c_rss_detail)

    # Create argument dictionaries
    transistor_args = {'name': 'CREE_C3M0016120K',
                       'type': 'SiC-MOSFET',
                       'author': 'Nikolas Förster',
                       'comment': '',
                       'manufacturer': 'Wolfspeed',
                       'datasheet_hyperlink': 'https://www.wolfspeed.com/downloads/dl/file/id/1483/product/0/c3m0016120k.pdf',
                       'datasheet_date': '2019-04',
                       'datasheet_version': "unknown",
                       'housing_area': 367e-6,
                       'cooling_area': 160e-6,
                       'housing_type': 'TO247',
                       'v_abs_max': 1200,
                       'i_abs_max': 250,
                       'i_cont': 115,
                       'c_iss': {"t_j": 25, "graph_v_c": c_iss_merged},  # insert csv here
                       'c_oss': {"t_j": 25, "graph_v_c": c_oss_merged},  # insert csv here
                       'c_rss': {"t_j": 25, "graph_v_c": c_rss_merged},  # insert csv here
                       'c_oss_er': None,    # if given will be provided as : {"c_o": 180e-12 , "v_gs": 0 ,"v_ds": 800V }
                       'c_oss_tr': None,    # if given will be provided as : {"c_o": 20e-12 , "v_gs": 0 ,"v_ds": 800V }
                       'c_iss_fix': 6085e-12,
                       'c_oss_fix': 230e-12,
                       'c_rss_fix': 13e-12,
                       'graph_v_ecoss': tdb.csv2array('transistor_V_Eoss.csv'),
                       'r_g_int': 2.6,
                       'r_th_cs': 0,
                       'r_th_diode_cs': 0,
                       'r_th_switch_cs': 0,
                       }

    ####################################
    # switch parameters
    ####################################
    # Metadata
    comment = "SiC switch"  # Optional
    manufacturer = "CREE"  # Optional
    technology = "unknown"  # Semiconductor technology. e.g. IGBT3/IGBT4/IGBT7  # Optional

    # Channel parameters
    # channel data minus 40 degree
    channel_m40_15 = {"t_j": -40, 'v_g': 15, "graph_v_i": tdb.csv2array('switch_channel_m40_15V.csv', first_xy_to_00=True)}  # insert csv here
    channel_m40_13 = {"t_j": -40, 'v_g': 13, "graph_v_i": tdb.csv2array('switch_channel_m40_13V.csv', first_xy_to_00=True)}  # insert csv here
    channel_m4_11 = {"t_j": -40, 'v_g': 11, "graph_v_i": tdb.csv2array('switch_channel_m40_11V.csv', first_xy_to_00=True)}  # insert csv here
    channel_m40_9 = {"t_j": -40, 'v_g': 9, "graph_v_i": tdb.csv2array('switch_channel_m40_9V.csv', first_xy_to_00=True)}  # insert csv here
    channel_m40_7 = {"t_j": -40, 'v_g': 7, "graph_v_i": tdb.csv2array('switch_channel_m40_7V.csv', first_xy_to_00=True)}  # insert csv here
    # channel data 25 degree
    channel_25_15 = {"t_j": 25, 'v_g': 15, "graph_v_i": tdb.csv2array('switch_channel_25_15V.csv', first_xy_to_00=True)}  # insert csv here
    channel_25_13 = {"t_j": 25, 'v_g': 13, "graph_v_i": tdb.csv2array('switch_channel_25_13V.csv', first_xy_to_00=True)}  # insert csv here
    channel_25_11 = {"t_j": 25, 'v_g': 11, "graph_v_i": tdb.csv2array('switch_channel_25_11V.csv', first_xy_to_00=True)}  # insert csv here
    channel_25_9 = {"t_j": 25, 'v_g': 9, "graph_v_i": tdb.csv2array('switch_channel_25_9V.csv', first_xy_to_00=True)}  # insert csv here
    channel_25_7 = {"t_j": 25, 'v_g': 7, "graph_v_i": tdb.csv2array('switch_channel_25_7V.csv', first_xy_to_00=True)}  # insert csv here
    # channel data 175 degree
    channel_175_15 = {"t_j": 175, 'v_g': 15, "graph_v_i": tdb.csv2array('switch_channel_175_15V.csv', first_xy_to_00=True)}  # insert csv here
    channel_175_13 = {"t_j": 175, 'v_g': 13, "graph_v_i": tdb.csv2array('switch_channel_175_13V.csv', first_xy_to_00=True)}  # insert csv here
    channel_175_11 = {"t_j": 175, 'v_g': 11, "graph_v_i": tdb.csv2array('switch_channel_175_11V.csv', first_xy_to_00=True)}  # insert csv here
    channel_175_9 = {"t_j": 175, 'v_g': 9, "graph_v_i": tdb.csv2array('switch_channel_175_9V.csv', first_xy_to_00=True)}  # insert csv here
    channel_175_7 = {"t_j": 175, 'v_g': 7, "graph_v_i": tdb.csv2array('switch_channel_175_7V.csv', first_xy_to_00=True)}  # insert csv here

    # switching parameters
    e_on_25_600 = {"dataset_type": "graph_i_e",
                   "t_j": 25,
                   'v_g': 15,
                   'v_supply': 600,
                   'r_g': 2.5,
                   "graph_i_e": tdb.csv2array('switch_switching_eon_2.5Ohm_600V_25deg_15V.csv')}  # insert csv here
    e_on_25_800 = {"dataset_type": "graph_i_e",
                   "t_j": 25,
                   'v_g': 15,
                   'v_supply': 800,
                   'r_g': 2.5,
                   "graph_i_e": tdb.csv2array('switch_switching_eon_2.5Ohm_800V_25deg_15V.csv')}  # insert csv here
    e_off_25_600 = {"dataset_type": "graph_i_e",
                    "t_j": 25,
                    'v_g': -4,
                    'v_supply': 600,
                    'r_g': 2.5,
                    "graph_i_e": tdb.csv2array('switch_switching_eoff_2.5Ohm_600V_25deg_-4V.csv')}  # insert csv here
    e_off_25_800 = {"dataset_type": "graph_i_e",
                    "t_j": 25,
                    'v_g': -4,
                    'v_supply': 800,
                    'r_g': 2.5,
                    "graph_i_e": tdb.csv2array('switch_switching_eoff_2.5Ohm_800V_25deg_-4V.csv')}  # insert csv here

    e_off_75A_800V = {"dataset_type": "graph_t_e",
                      'v_g': -4,
                      'v_supply': 800,
                      'r_g': 2.5,
                      'i_x': 75,
                      "graph_t_e": tdb.csv2array('switch_switching_eoff_2.5Ohm_800V_75A_-4V.csv')}  # insert csv here

    e_on_75A_800V = {"dataset_type": "graph_t_e",
                     'v_g': 15,
                     'v_supply': 800,
                     'r_g': 2.5,
                     'i_x': 75,
                     "graph_t_e": tdb.csv2array('switch_switching_eon_2.5Ohm_800V_75A_15V.csv')}  # insert csv here

    switch_gate_charge_curve_800 = {
        'i_channel': 20,
        't_j': 25,
        'v_supply': 800,
        'i_g': 50e-3,
        'graph_q_v': tdb.csv2array('gate_charge.csv', first_x_to_0=True)
    }  # insert csv here

    switch_ron_args_11 = {
        'i_channel': 75,
        'v_g': 11,
        'dataset_type': 't_r',
        'r_channel_nominal': 16e-3,
        'graph_t_r': tdb.csv2array('switch_on_res_vg_11V.csv')
    }  # insert csv here
    switch_ron_args_13 = {
        'i_channel': 75,
        'v_g': 13,
        'dataset_type': 't_r',
        'r_channel_nominal': 16e-3,
        'graph_t_r': tdb.csv2array('switch_on_res_vg_13V.csv')
    }  # insert csv here
    switch_ron_args_15 = {
        'i_channel': 75,
        'v_g': 15,
        'dataset_type': 't_r',
        'r_channel_nominal': 16e-3,
        'graph_t_r': tdb.csv2array('switch_on_res_vg_15V.csv')
    }  # insert csv here

    # switch foster parameters
    switch_foster_args = {
        # 'r_th_vector': r_th_vector,
        'r_th_total': 0.27,
        # 'c_th_vector': c_th_vector,
        # 'c_th_total': c_th_total,
        # 'tau_vector': tau_vector,
        # 'tau_total': tau_total,
        # 'graph_t_rthjc': graph_t_rthjc
    }
    # switch_foster_args = None

    # Bring the switch_args together
    switch_args = {
        'comment': comment,
        'manufacturer': manufacturer,
        'technology': technology,
        't_j_max': 175,
        'channel': [channel_m40_7, channel_m40_9, channel_m4_11, channel_m40_13, channel_m40_15, channel_25_15, channel_25_13, channel_25_11,
                    channel_25_9, channel_25_7, channel_175_15, channel_175_13, channel_175_11, channel_175_9, channel_175_7],
        'e_on': [e_on_25_600, e_on_25_800, e_on_75A_800V],
        'e_off': [e_off_25_600, e_off_25_800, e_off_75A_800V],
        'charge_curve': [switch_gate_charge_curve_800],
        'r_channel_th': [switch_ron_args_11, switch_ron_args_13, switch_ron_args_15],
        'thermal_foster': switch_foster_args,
        'soa': [soa_t_pulse_100ms, soa_t_pulse_1ms, soa_t_pulse_100us, soa_t_pulse_10us],
    }

    ####################################
    # diode parameters
    ####################################
    comment = 'comment diode'
    manufacturer = 'manufacturer diode'
    technology = 'technology diode'

    # Channel parameters
    channel_25_0 = {"t_j": 25, 'v_g': 0, "graph_v_i": tdb.csv2array('diode_channel_25_0vgs.csv',
                                                                    first_xy_to_00=True, second_y_to_0=True, mirror_xy_data=True)}  # insert csv here
    channel_25_neg2 = {"t_j": 25, 'v_g': -2, "graph_v_i": tdb.csv2array('diode_channel_25_-2vgs.csv',
                                                                        first_xy_to_00=True, second_y_to_0=True, mirror_xy_data=True)}  # insert csv here
    channel_25_neg4 = {"t_j": 25, 'v_g': -4, "graph_v_i": tdb.csv2array('diode_channel_25_-4vgs.csv',
                                                                        first_xy_to_00=True, second_y_to_0=True, mirror_xy_data=True)}  # insert csv here

    channel_175_0 = {"t_j": 175, 'v_g': 0, "graph_v_i": tdb.csv2array('diode_channel_175_0vgs.csv',
                                                                      first_xy_to_00=True, second_y_to_0=True, mirror_xy_data=True)}  # insert csv here
    channel_175_neg2 = {"t_j": 175, 'v_g': -2, "graph_v_i": tdb.csv2array('diode_channel_175_-2vgs.csv',
                                                                          first_xy_to_00=True, second_y_to_0=True, mirror_xy_data=True)}  # insert csv here
    channel_175_neg4 = {"t_j": 175, 'v_g': -4, "graph_v_i": tdb.csv2array('diode_channel_175_-4vgs.csv',
                                                                          first_xy_to_00=True, second_y_to_0=True, mirror_xy_data=True)}  # insert csv here

    # diode foster parameters
    diode_foster_args = {
        # 'r_th_vector': r_th_vector,
        'r_th_total': 0,
        # 'c_th_vector': c_th_vector,
        # 'c_th_total': c_th_total,
        # 'tau_vector': tau_vector,
        # 'tau_total': tau_total,
        # 'graph_t_rthjc': graph_t_rthjc
    }

    diode_args = {'comment': comment,
                  'manufacturer': manufacturer,
                  'technology': technology,
                  't_j_max': 175,
                  'channel': [channel_25_0, channel_25_neg2, channel_25_neg4, channel_175_0, channel_175_neg2, channel_175_neg4],
                  'e_rr': [],
                  'thermal_foster': diode_foster_args}

    ####################################
    # create transistor object
    ####################################
    return tdb.Transistor(transistor_args, switch_args, diode_args, possible_housing_types=database.housing_types,
                          possible_module_manufacturers=database.module_manufacturers)


if __name__ == '__main__':
    db = tdb.DatabaseManager()
    db.set_operation_mode_json()

    # update the database
    # db.update_from_fileexchange(True)

    transistor = template_example(db)

    ####################################
    # Method examples
    ####################################

    # transistor methods #
    # transistor.wp.switch_v_channel, transistor.wp.switch_r_channel = transistor.calc_lin_channel(175, 15, 40, 'switch')
    # linearization at 175 degree, 15V gatevoltage, 40A channel current
    # print(f"{transistor.wp.switch_v_channel=} V")
    # print(f"{transistor.wp.switch_r_channel=} Ohm")
    # print(transistor.calc_v_eoss())
    # transistor.plot_v_eoss()
    # transistor.plot_v_qoss()

    # connect transistors in parallel
    # parallel_transistors = db.parallel_transistors(transistor, 3)
    # db.export_single_transistor_to_json(parallel_transistors, os.getcwd())

    # switch methods #
    # transistor.switch.plot_energy_data()
    # transistor.switch.plot_all_channel_data()
    # transistor.switch.plot_channel_data_vge(15)
    # transistor.switch.plot_channel_data_temp(175)

    # diode methods #
    # transistor.diode.plot_energy_data()
    # transistor.diode.plot_all_channel_data()

    ####################################
    # exporter example
    ####################################

    # Windows users: export datasheet
    # html_str = transistor.export_datasheet()

    # Linux users: export datasheet as html
    # look for CREE_C3M0016120K.html in template_example folder.
    # html_str = transistor.export_datasheet(build_collection=True)
    # Html_file = open(f"{transistor.name}.html", "w")
    # Html_file.write(html_str)
    # Html_file.close()

    # Export to MATLAB
    # transistor.export_matlab()

    # Export to SIMULINK
    # NOTE: Exporter is only working for IGBTs. This Template contains a SiC-MOSFET!
    # transistor.export_simulink_loss_model()

    # Export to PLECS
    # transistor.export_plecs()

    # Export to geckoCIRCUITS
    # transistor.export_geckocircuits(True, 600, 15, -4, 2.5, 2.5)

    ####################################
    # Database example
    ####################################

    # update the database
    db.update_from_fileexchange(True)

    # print ALL database content
    db.print_tdb()

    # print database content of housing and datasheet hyperlink
    db.print_tdb(['housing_type', 'datasheet_hyperlink'])

    # load transistor
    # optional argument: collection. If no collection is specified, it connects to local TDB
    transistor_loaded = db.load_transistor('CREE_C3M0016120K')
    print(transistor_loaded.switch.t_j_max)

    # export to json
    # optional argument: path. If no path is specified, saves exports to local folder
    # db.export_single_transistor_to_json(transistor, os.getcwd())

    ####################################
    # Examples to fill-in transistor.wp-class
    ####################################
    # full-automated example
    # transistor.quickstart_wp()

    # half-automated example
    # transistor.update_wp(125, 15, 50)

    # non-automated example
    # # calculate energy and charge in c_oss
    # transistor.wp.e_oss = transistor.calc_v_eoss()
    # transistor.wp.q_oss = transistor.calc_v_qoss()
    #
    # # switch, linearize channel and search for loss curves
    # transistor.wp.switch_v_channel, transistor.wp.switch_r_channel = transistor.calc_lin_channel(25, 15, 150, 'switch')
    # transistor.wp.e_on = transistor.get_object_i_e('e_on', 25, 15, 600, 2.5).graph_i_e
    # transistor.wp.e_off = transistor.get_object_i_e('e_off', 25, -4, 600, 2.5).graph_i_e
    #
    # # diode, linearize channel and search for loss curves
    # transistor.wp.diode_v_channel, transistor.wp.diode_r_channel = transistor.calc_lin_channel(25, -4, 150, 'diode')
