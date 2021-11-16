# imports
import numpy as np
import datetime
import sys
import os
from pymongo import MongoClient
from matplotlib import pyplot as plt
import json
import transistordatabase as tdb


# Template to generate a transistor
def Template():
    """
    * Initial author: N. Foerster
    * Date of creation: 8.2.2021
    * Last modified by: -
    * Date of modification: -
    * Version: 1.0.0
    * Compatibility: Python 3.9
    * Other files required:
    * Link to function:
    Syntax:


    Description:
    Template to generate a transistor object

    Input parameters:


    Output parameters:
     * Transistor

    Example:


    Known Bugs:


    """



    ####################################
    # transistor parameters
    ####################################

    graph_t_zthjc = tdb.csv2array('graph_t_zthjc.csv', first_x_to_0=True)

    # Create argument dictionaries
    transistor_args = {'name': 'GaNSystems_GS66506T',
                       'type': 'GaN-Transistor',
                       'author': 'Mohan Nagella',
                       'comment': '',
                       'manufacturer': 'GaN Systems',
                       'datasheet_hyperlink': 'https://gansystems.com/wp-content/uploads/2020/04/GS66506T-DS-Rev-200402.pdf',
                       'datasheet_date': '2021-10',
                       'datasheet_version': "Rev 200402",
                       'housing_area': 24.86e-6,
                       'cooling_area': 15.78e-6,
                       'housing_type': 'GaNPX',
                       'v_abs_max': 650,
                       'i_abs_max': 22.5,  #pulse drain current
                       'i_cont': 18,    #at 100
                       'c_iss':  {"t_j": 25, "graph_v_c": tdb.csv2array('Ciss_in_pF.csv', first_x_to_0=True)},  # insert csv here
                       'c_oss': {"t_j": 25, "graph_v_c": tdb.csv2array('Coss_in_pF.csv', first_x_to_0=True)},  # insert csv here
                       'c_rss': {"t_j": 25, "graph_v_c": tdb.csv2array('Crss_in_pF.csv', first_x_to_0=True)},  # insert csv here
                       'c_oss_er': {'c_type': 'energy_related', 'c_o': 73e-12, 'v_gs': 0, 'v_ds': 400},
                       'c_oss_tr': {'c_type': 'time_related', 'c_o': 117e-12, 'v_gs': 0, 'v_ds': 400},
                       'graph_v_ecoss': tdb.csv2array('V_Eoss.csv'), #Cossstoredenergy
                       'r_g_int': 1.1,
                       'r_th_cs': 0,  #as zero
                       'r_th_diode_cs': 0, #other too for devices with separate switch and diode
                       'r_th_switch_cs': 0, #""
                       }

    ####################################
    # switch parameters
    ####################################
    #### Metadata
    comment = " "  # Optional
    manufacturer = "GaN System"  # Optional
    technology = "Top-side cooled E-mode"  # Semiconductor technology. e.g. IGBT3/IGBT4/IGBT7  # Optional

    #### Channel parameters
    # channel data 25 degree
    channel_25_2 = {"t_j": 25, 'v_g': 2, "graph_v_i": tdb.csv2array('channel_25_2V.csv', first_xy_to_00=True)}  # insert csv here
    channel_25_3 = {"t_j": 25, 'v_g': 3, "graph_v_i": tdb.csv2array('channel_25_3V.csv', first_xy_to_00=True)}  # insert csv here
    channel_25_4 = {"t_j": 25, 'v_g': 4, "graph_v_i": tdb.csv2array('channel_25_4V.csv', first_xy_to_00=True)}  # insert csv here
    channel_25_5 = {"t_j": 25, 'v_g': 5, "graph_v_i": tdb.csv2array('channel_25_5V.csv', first_xy_to_00=True)}  # insert csv here
    channel_25_6 = {"t_j": 25, 'v_g': 6, "graph_v_i": tdb.csv2array('channel_25_6V.csv', first_xy_to_00=True)}  # insert csv here
    #channel_25_7 = {"t_j": 25, 'v_g': 7, "graph_v_i": tdb.csv2array('channel_25_7V.csv', first_xy_to_00=True)}  # insert csv here
    #channel_25_8 = {"t_j": 25, 'v_g': 8, "graph_v_i": tdb.csv2array('channel_25_8V.csv', first_xy_to_00=True)}  # insert csv here
    #channel_25_10 = {"t_j": 25, 'v_g': 10, "graph_v_i": tdb.csv2array('channel_25_10V.csv', first_xy_to_00=True)}  # insert csv here
    #channel_25_20 = {"t_j": 25, 'v_g': 20, "graph_v_i": tdb.csv2array('channel_25_20V.csv', first_xy_to_00=True)}  # insert csv here

    # channel data 175 degree
    channel_150_2 = {"t_j": 150, 'v_g': 2, "graph_v_i": tdb.csv2array('channel_150_2V.csv', first_xy_to_00=True)}  # insert csv here
    channel_150_3 = {"t_j": 150, 'v_g': 3, "graph_v_i": tdb.csv2array('channel_150_3V.csv', first_xy_to_00=True)}  # insert csv here
    channel_150_4 = {"t_j": 150, 'v_g': 4, "graph_v_i": tdb.csv2array('channel_150_4V.csv', first_xy_to_00=True)}  # insert csv here
    channel_150_5 = {"t_j": 150, 'v_g': 5, "graph_v_i": tdb.csv2array('channel_150_5V.csv', first_xy_to_00=True)}  # insert csv here
    channel_150_6 = {"t_j": 150, 'v_g': 6, "graph_v_i": tdb.csv2array('channel_150_6V.csv', first_xy_to_00=True)}  # insert csv here

    channel_50_6 = {"t_j": 50, 'v_g': 6, "graph_v_i": tdb.csv2array('channel_50_6V.csv', first_xy_to_00=True)}  # insert csv here
    channel_75_6 = {"t_j": 75, 'v_g': 6, "graph_v_i": tdb.csv2array('channel_75_6V.csv', first_xy_to_00=True)}  # insert csv here
    channel_100_6 = {"t_j": 100, 'v_g': 6, "graph_v_i": tdb.csv2array('channel_100_6V.csv', first_xy_to_00=True)}  # insert csv here
    channel_125_6 = {"t_j": 125, 'v_g': 6, "graph_v_i": tdb.csv2array('channel_125_6V.csv', first_xy_to_00=True)}  # insert csv here

    r_th_vector = [0.02, 0.32, 0.34, 0.02]
    c_th_vector = [5.3E-5, 5.3E-4, 4.64E-3, 1.43E-3]
    ### switch foster parameters
    switch_foster_args = {
        'r_th_vector': r_th_vector,
        'r_th_total': 0.7,
        'c_th_vector': c_th_vector,
        #'c_th_total': c_th_total,
        #'tau_vector': tau_vector,
        #'tau_total': tau_total,
        'graph_t_rthjc': graph_t_zthjc
        }
    # switch_foster_args = None

    graph_t_r = tdb.csv2array('rd_on_vs_tj.csv')
    graph_t_r_2 = tdb.csv2array('rd_on_vs_tj.csv')
    graph_t_r_2[1] = graph_t_r_2[1] * 2
    switch_ron_args = {
        'i_channel': 12,
        'v_g': 15,
        'dataset_type': 't_factor',
        'r_channel_nominal': 67,
        'graph_t_r': graph_t_r
    }
    switch_ron_args_2 = {
        'i_channel': 12,
        'v_g': 20,
        'dataset_type': 't_factor',
        'r_channel_nominal': 67,
        'graph_t_r': graph_t_r_2
    }


    #### Bring the switch_args together
    switch_args = {
        'comment': comment,
        'manufacturer': manufacturer,
        'technology': technology,
        't_j_max': 150,
        'channel': [channel_25_4, channel_25_5, channel_25_2, channel_25_6, channel_25_3, channel_50_6, channel_75_6, channel_100_6,channel_125_6, channel_150_2,channel_150_3,channel_150_4,channel_150_5,channel_150_6],
        'e_on': None,
        'e_off': None,
        'r_channel_th': [switch_ron_args],
        'thermal_foster': switch_foster_args}



    ####################################
    # diode parameters
    ####################################
    comment = 'intrinsic diode'
    manufacturer = 'GaN Systems'
    technology = 'Top-side cooled E-mode'

    #### Channel parameters
    channel_25_0V = {"t_j": 25, 'v_g': 0, "graph_v_i": tdb.csv2array('diode_channel_25_0V.csv', first_xy_to_00=True, second_y_to_0=True, mirror_xy_data=True)}  # insert csv here
    channel_25_6V = {"t_j": 25, 'v_g': 6, "graph_v_i": tdb.csv2array('diode_channel_25_6V.csv', first_xy_to_00=True, second_y_to_0=False, mirror_xy_data=True)}  # insert csv here
    channel_25_n3V = {"t_j": 25, 'v_g': -3, "graph_v_i": tdb.csv2array('diode_channel_25_-3V.csv', first_xy_to_00=True, second_y_to_0=True, mirror_xy_data=True)}  # insert csv here

    channel_150_0V = {"t_j": 150, 'v_g': 0, "graph_v_i": tdb.csv2array('diode_channel_150V_0V.csv', first_xy_to_00=True, second_y_to_0=True, mirror_xy_data=True)}  # insert csv here
    channel_150_6V = {"t_j": 150, 'v_g': 6, "graph_v_i": tdb.csv2array('diode_channel_150_6V.csv', first_xy_to_00=True, second_y_to_0=False, mirror_xy_data=True)}  # insert csv here
    channel_150_n3V = {"t_j": 150, 'v_g': -3, "graph_v_i": tdb.csv2array('diode_channel_150_-3V.csv', first_xy_to_00=True, second_y_to_0=True, mirror_xy_data=True)}  # insert csv here

    ### diode foster parameters
    diode_foster_args = {
        #'r_th_vector': r_th_vector,
        'r_th_total': 0,
        #'c_th_vector': c_th_vector,1
        #'c_th_total': c_th_total,
        #'tau_vector': tau_vector,
        #'tau_total': tau_total,
        #'graph_t_rthjc': graph_t_rthjc
        }

    diode_args = {'comment': comment,
                  'manufacturer': manufacturer,
                  'technology': technology,
                  't_j_max': 150,
                  'channel': [channel_25_0V, channel_25_6V,channel_25_n3V,channel_150_0V,channel_150_6V,channel_150_n3V],
                  'e_rr': None,
                  'thermal_foster': diode_foster_args}

    ####################################
    # create transistor object
    ####################################
    return tdb.Transistor(transistor_args, switch_args, diode_args)

if __name__ == '__main__':

    transistor = Template()
    #1transistor.export_datasheet()
    transistor.export_json()
    transistor.export_datasheet()


    #update_from_fileexchange()
    #transistor = load({'name': 'Fuji_2MBI100XAA120-50'})
    #transistor.quickstart_wp()
    #transistor.calc_thermal_params(order=5, input_type="switch", plotbit=True)
    ####################################
    # Method examples
    ####################################

    #### transistor methods ####
    # transistor.wp.switch_v_channel, transistor.wp.switch_r_channel = transistor.calc_lin_channel(175, 15, 40, 'switch')  # linearisation at 175 degree, 15V gatevoltage, 40A channel current
    # print(f"{transistor.wp.switch_v_channel = } V")
    # print(f"{transistor.wp.switch_r_channel = } Ohm")
    # print(transistor.calc_v_eoss())
    # transistor.plot_v_eoss()
    #transistor.plot_v_qoss()

    # connect transistors in parallel
    #parallel_transistors = transistor.parallel_transistors(3)

    #### switch methods ####
    #transistor.switch.plot_energy_data()
    # transistor.switch.plot_all_channel_data()
    # transistor.switch.plot_channel_data_vge(15)
    # transistor.switch.plot_channel_data_temp(175)

    #### diode methods ####
    # transistor.diode.plot_energy_data()
    # transistor.diode.plot_all_channel_data()


    ####################################
    # exporter example
    ####################################

    # Export virtual datasheet
    # transistor.export_datasheet()

    # Export to MATLAB
    # transistor.export_matlab()

    # Export to SIMULINK
    # NOTE: Exporter is only working for IGBTs. This Template contains a SiC-MOSFET!
    # transistor.export_simulink_loss_model()

    # Export to PLECS
    # transistor.export_plecs()

    # Export to geckoCIRCUITS
    # transistor.export_geckocircuits(600, 15, -4, 2.5, 2.5)

    ####################################
    # Database example
    ####################################

    # print ALL database content
    # tdb.print_TDB()

    # print database content of housing and datasheet hyperlink
    # tdb.print_TDB(['housing_type','datasheet_hyperlink'])

    # before init mongo, you need to install mongodb and start the database via the command line by using 'mongo' command
    # init mongodb
    # collection = tdb.connect_local_TDB()  # Collection

    # reset the mongodb database
    # collection.drop()

    # store transistor
    # optional argument: collection. If no collection is specified, it connects to local TDB
    # transistor.save()

    # load transistor
    # optional argument: collection. If no collection is specified, it connects to local TDB
    # transistor_loaded = tdb.load({'name': 'CREE_C3M0016120K'})
    # print(transistor_loaded.switch.t_j_max)

    # export to json
    # optional argument: path. If no path is specified, saves exports to local folder
    # transistor.export_json()

    # import from json
    # optional argument: path. If no path is specified, it loads from to local folder
    # transistor_imported = tdb.import_json('CREE_C3M0016120K.json')
    # print(transistor_imported.switch.t_j_max)

    # Rename transistor arguments
    # tdb.connect_local_TDB().update_many({}, {"$rename": {"transistor_type": "type"}})

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
    # # switch, linearize channel and search for losscurves
    # transistor.wp.switch_v_channel, transistor.wp.switch_r_channel = transistor.calc_lin_channel(25, 15, 150, 'switch')
    # transistor.wp.e_on = transistor.get_object_i_e('e_on', 25, 15, 600, 2.5).graph_i_e
    # transistor.wp.e_off = transistor.get_object_i_e('e_off', 25, -4, 600, 2.5).graph_i_e
    #
    # # diode, linearize channel and search for losscurves
    # transistor.wp.diode_v_channel, transistor.wp.diode_r_channel = transistor.calc_lin_channel(25, -4, 150, 'diode')








