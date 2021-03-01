# imports
import numpy as np
import datetime
import sys
import os


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
    # Create argument dictionaries
    transistor_args = {'name': 'CREE_C3M0016120K',
                       'transistor_type': 'SiC-MOSFET',
                       'author': 'Nikolas Förster',
                       'comment': '',
                       'manufacturer': 'Wolfspeed',
                       'datasheet_hyperlink': 'https://www.wolfspeed.com/downloads/dl/file/id/1483/product/0/c3m0016120k.pdf',
                       'datasheet_date': '2019-04',
                       'datasheet_version': "unknown",
                       'housing_area': 367e-6,
                       'cooling_area': 160e-6,
                       'housing_type': 'TO247',
                       'v_max': 1200,
                       'i_max': 250,
                       'i_cont': 115,
                       'c_iss':  {"t_j": 25, "graph_v_c": csv2array('transistor_c_iss.csv', False, False, True)},  # insert csv here
                       'c_oss': {"t_j": 25, "graph_v_c": csv2array('transistor_c_oss.csv', False, False, True)},  # insert csv here
                       'c_rss': {"t_j": 25, "graph_v_c": csv2array('transistor_c_rss.csv', False, False, True)},  # insert csv here
                       'e_coss': csv2array('transistor_V_Eoss.csv', False, False, False)
                       }

    ####################################
    # switch parameters
    ####################################
    #### Metadata
    comment = "SiC switch"  # Optional
    manufacturer = "CREE"  # Optional
    technology = "unknown"  # Semiconductor technology. e.g. IGBT3/IGBT4/IGBT7  # Optional
    r_g_int = 2.6  # mandatory

    # Constant Capacitances
    c_oss = 5   # Unit: F  # Optional
    c_iss = 3  # Unit: F  # Optional
    c_rss = 4    # Unit: F  # Optional

    #### Channel parameters
    # channel data minus 40 degree
    channel_m40_15 = {"t_j": -40, 'v_g': 15,"graph_v_i": csv2array('switch_channel_m40_15V.csv', True, False, False)}  # insert csv here
    channel_m40_13 = {"t_j": -40, 'v_g': 13, "graph_v_i": csv2array('switch_channel_m40_13V.csv', True, False, False)}  # insert csv here
    channel_m4_11 = {"t_j": -40, 'v_g': 11, "graph_v_i": csv2array('switch_channel_m40_11V.csv', True, False, False)}  # insert csv here
    channel_m40_9 = {"t_j": -40, 'v_g': 9, "graph_v_i": csv2array('switch_channel_m40_9V.csv', True, False, False)}  # insert csv here
    channel_m40_7 = {"t_j": -40, 'v_g': 7, "graph_v_i": csv2array('switch_channel_m40_7V.csv', True, False, False)}  # insert csv here
    # channel data 25 degree
    channel_25_15 = {"t_j": 25, 'v_g': 15,"graph_v_i": csv2array('switch_channel_25_15V.csv', True, False, False)}  # insert csv here
    channel_25_13 = {"t_j": 25, 'v_g': 13, "graph_v_i": csv2array('switch_channel_25_13V.csv', True, False, False)}  # insert csv here
    channel_25_11 = {"t_j": 25, 'v_g': 11, "graph_v_i": csv2array('switch_channel_25_11V.csv', True, False, False)}  # insert csv here
    channel_25_9 = {"t_j": 25, 'v_g': 9, "graph_v_i": csv2array('switch_channel_25_9V.csv', True, False, False)}  # insert csv here
    channel_25_7 = {"t_j": 25, 'v_g': 7, "graph_v_i": csv2array('switch_channel_25_7V.csv', True, False, False)}  # insert csv here
    # channel data 175 degree
    channel_175_15 = {"t_j": 175, 'v_g': 15,"graph_v_i": csv2array('switch_channel_175_15V.csv', True, False, False)}  # insert csv here
    channel_175_13 = {"t_j": 175, 'v_g': 13, "graph_v_i": csv2array('switch_channel_175_13V.csv', True, False, False)}  # insert csv here
    channel_175_11 = {"t_j": 175, 'v_g': 11, "graph_v_i": csv2array('switch_channel_175_11V.csv', True, False, False)}  # insert csv here
    channel_175_9 = {"t_j": 175, 'v_g': 9, "graph_v_i": csv2array('switch_channel_175_9V.csv', True, False, False)}  # insert csv here
    channel_175_7 = {"t_j": 175, 'v_g': 7, "graph_v_i": csv2array('switch_channel_175_7V.csv', True, False, False)}  # insert csv here


   # print(csv2array('switch_switching_eon_2.5Ohm_600V_25deg_15V.csv', False))
    print(np.shape(csv2array('switch_switching_eon_2.5Ohm_600V_25deg_15V.csv', False, False, False)))

    #### switching parameters
    e_on_25_600 = {"dataset_type": "graph_i_e",
                   "t_j": 25,
                   'v_g': 15,
                   'v_supply': 600,
                   'r_g': 2.5,
                   "i_e_data": csv2array('switch_switching_eon_2.5Ohm_600V_25deg_15V.csv', False, False, False)}  # insert csv here
    e_on_25_800 = {"dataset_type": "graph_i_e",
                   "t_j": 25,
                   'v_g': 15,
                   'v_supply': 800,
                   'r_g': 2.5,
                   "i_e_data": csv2array('switch_switching_eon_2.5Ohm_800V_25deg_15V.csv', False, False, False)}  # insert csv here
    e_off_25_600 = {"dataset_type": "graph_i_e",
                   "t_j": 25,
                   'v_g': -4,
                   'v_supply': 600,
                   'r_g': 2.5,
                   "i_e_data": csv2array('switch_switching_eoff_2.5Ohm_600V_25deg_-4V.csv', False, False, False)}  # insert csv here
    e_off_25_800 = {"dataset_type": "graph_i_e",
                    "t_j": 25,
                    'v_g': -4,
                    'v_supply': 800,
                    'r_g': 2.5,
                    "i_e_data": csv2array('switch_switching_eoff_2.5Ohm_800V_25deg_-4V.csv', False, False, False)}  # insert csv here

    ### switch foster parameters
    #
    # switch_foster_args = {'r_th_vector': r_th_vector, 'r_th_total': r_th_total, 'c_th_vector': c_th_vector,
    #                'c_th_total': c_th_total, 'tau_vector': tau_vector, 'tau_total': tau_total,
    #                'transient_data': transient_data}
    switch_foster_args = None


    #### Bring the switch_args together
    switch_args = {
        'comment': comment,
        'manufacturer': manufacturer,
        'technology': technology,
        'r_g_int': r_g_int,
        'c_oss': c_oss,
        'c_iss': c_iss,
        'c_rss': c_rss,
        'channel': [channel_m40_7, channel_m40_9, channel_m4_11, channel_m40_13, channel_m40_15, channel_25_15, channel_25_13, channel_25_11, channel_25_9, channel_25_7, channel_175_15, channel_175_13, channel_175_11, channel_175_9, channel_175_7],
        'e_on': [e_on_25_600, e_on_25_800],
        'e_off': [e_off_25_600, e_off_25_800],
        'thermal_foster': switch_foster_args}



    ####################################
    # diode parameters
    ####################################
    comment = 'comment diode'
    manufacturer = 'manufacturer diode'
    technology = 'technology diode'

    #### Channel parameters
    channel_25_0 = {"t_j": 25, 'v_g': 0, "graph_v_i": csv2array('diode_channel_25_0vgs.csv', True, True, False)}  # insert csv here
    channel_25_neg2 = {"t_j": 25, 'v_g': -2, "graph_v_i": csv2array('diode_channel_25_-2vgs.csv', True, True, False)}  # insert csv here
    channel_25_neg4 = {"t_j": 25, 'v_g': -4, "graph_v_i": csv2array('diode_channel_25_-4vgs.csv', True, True, False)}  # insert csv here

    channel_175_0 = {"t_j": 25, 'v_g': 0, "graph_v_i": csv2array('diode_channel_175_0vgs.csv', True, True, False)}  # insert csv here
    channel_175_neg2 = {"t_j": 25, 'v_g': -2, "graph_v_i": csv2array('diode_channel_175_-2vgs.csv', True, True, False)}  # insert csv here
    channel_175_neg4 = {"t_j": 25, 'v_g': -4, "graph_v_i": csv2array('diode_channel_175_-4vgs.csv', True, True, False)}  # insert csv here

    ### diode foster parameters
    diode_foster_args = None

    diode_args = {'comment': comment,
                  'manufacturer': manufacturer,
                  'technology': technology,
                  'channel': [channel_25_0, channel_25_neg2, channel_25_neg4, channel_175_0, channel_175_neg2, channel_175_neg4],
                  'e_rr': [],
                  'thermal_foster': diode_foster_args}


    ####################################

    ####################################
    # ToDo:

    ####################################
    # create transistor object
    ####################################
    # Create transistor object
    return Transistor(transistor_args, switch_args, diode_args)

if __name__ == '__main__':
    current_path = os.getcwd()
    os.chdir('../transistor_database')
    new_path = os.getcwd()
    sys.path.append(new_path)
    os.chdir(current_path)
    from databaseClasses import Transistor
    from databaseClasses import csv2array

    transistor = Template()

    print('---------------------')
    print("transistor metadata")
    print('---------------------')
    print(transistor.name)
    print(transistor.transistor_type)
    print(transistor.author)
    print(transistor.comment)
    print(transistor.manufacturer)
    print(transistor.datasheet_hyperlink)
    print(transistor.datasheet_date)
    print(transistor.datasheet_version)
    print(transistor.housing_area)
    print(transistor.cooling_area)
    print(transistor.housing_type)


    print('---------------------')
    print("switch metadata")
    print('---------------------')
    print(transistor.switch.manufacturer)
    print(transistor.switch.comment)
    print(transistor.switch.technology)



    print('---------------------')
    print("switch data")
    print('---------------------')
    print(transistor.switch.channel[0].graph_v_i)
    print(transistor.switch.channel[0].t_j)

    #transistor.switch.plot_all_channel_data()
    #transistor.switch.plot_channel_data_vge(15)
    #transistor.switch.plot_channel_data_temp(175)

    v_channel, r_channel = transistor.linearize_channel_ui_graph(175, 15, 40, 'switch')  # linearisation at 175 degree, 15V gatevoltage, 40A channel current
    print("v_channel_linearized = {} V".format(v_channel))
    print("r_channel_linearized = {} Ohm".format(r_channel))

    print('---------------------')
    print("diode metadata")
    print('---------------------')
    print(transistor.diode.manufacturer)
    print(transistor.diode.comment)
    print(transistor.diode.technology)

    #print(transistor.c_iss.t_j)
    #print(transistor.c_iss.graph_v_c)

    #print(transistor.e_coss)

    # transistor.switch.plot_energy_data()
    # transistor.diode.plot_energy_data()

    #store_transistor(transistor)
    #load_transistor()
    # ToDo: store transistor in database

    print(transistor.e_coss)