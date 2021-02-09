# imports
from databaseClasses import Transistor
from databaseClasses import csv2array
import numpy as np
import datetime

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
    name = 'CREE_C3M0016120K'
    transistor_type = 'SiC-MOSFET'
    v_max = 1200
    i_max = 250
    i_cont = 115

    # Create argument dictionaries
    transistor_args = {'name': name, 'transistor_type': transistor_type, 'v_max': v_max,
                       'i_max': i_max, 'i_cont': i_cont}
    ####################################
    # metadata parameters
    ####################################
    # ToDo: use SI-based things. No mJ, no mJ, ...

    author = 'Nikolas Foerster'
    comment = ''
    manufacturer = 'Wolfspeed'
    datasheet_hyperlink = 'https://www.wolfspeed.com/downloads/dl/file/id/1483/product/0/c3m0016120k.pdf'
    datasheet_date = '2019-04'
    datasheet_version = "unknown"
    housing_area = 367e-6
    cooling_area = 160e-6
    housing_type = 'TO247'

    metadata_args = {'author': author, 'comment': comment, 'manufacturer': manufacturer,
                     'datasheet_hyperlink': datasheet_hyperlink, 'datasheet_date': datasheet_date,
                     'datasheet_version': datasheet_version, 'housing_area': housing_area,
                     'cooling_area': cooling_area, 'housing_type': housing_type}



    ####################################
    # switch parameters
    ####################################

    channel_25 = {"t_j": 25, "v_i_data": csv2array('switch_channel_25_vg15.csv', True)}  # insert csv here
    channel_175 = {"t_j": 175, "v_i_data": csv2array('switch_channel_175_vg15.csv', True)}  # insert csv here

    # switching behaviour
    dataset_type = "single" # Mandatory
    t_j = 125  # Unit: °C  # Mandatory
    v_supply = 800  # Unit: V  # Mandatory
    v_g = 15  # Unit: V  # Mandatory

    # turn on
    e_on = 15e-3  # Unit: J
    r_g_on = 2.5   # Unit: Ohm
    i_on =  100 # Unit: A

    # turn off
    e_off = 25e-3  # Unit: J
    r_g_off = 5   # Unit: Ohm
    i_off = 100  # Unit: A

    e_on_25 = {'dataset_type': dataset_type, 't_j': t_j, 'v_supply': v_supply, 'v_g': v_g, 'e_x': e_on, 'r_g': r_g_on, 'i_x': i_on}
    e_off_25 = {'dataset_type': dataset_type, 't_j': t_j, 'v_supply': v_supply, 'v_g': v_g, 'e_x': e_off, 'r_g': r_g_off, 'i_x': i_off}



    # Metadata
    comment = "SiC switch"  # Optional
    manufacturer = "CREE"  # Optional
    technology = "unknown" # Semiconductor technology. e.g. IGBT3/IGBT4/IGBT7  # Optional

    # Constant Capacitances
    c_oss = 5   # Unit: pF  # Optional
    c_iss = 3  # Unit: pF  # Optional
    c_rss = 4    # Unit: pF  # Optional

    switch_args = {
        'comment': comment,
        'manufacturer': manufacturer,
        'technology': technology,
        'c_oss': c_oss,
        'c_iss': c_iss,
        'c_rss': c_rss,
        'channel': [channel_25, channel_175],
        'e_on': [e_on_25, e_on_25],
        'e_off': [e_off_25, e_off_25]}

    ####################################
    # switch foster parameters
    ####################################
    #
    # foster_args = {'r_th_vector': r_th_vector, 'r_th_total': r_th_total, 'c_th_vector': c_th_vector,
    #                'c_th_total': c_th_total, 'tau_vector': tau_vector, 'tau_total': tau_total,
    #                'transient_data': transient_data}
    foster_args = None

    ####################################
    # diode parameters
    ####################################



    diode_args = {'comment': comment, 'manufacturer': manufacturer, 'technology': technology,
                  'channel': [], 'e_rr': []}


    ####################################
    # diode foster parameters
    ####################################
    # ToDo:

    ####################################
    # create transistor object
    ####################################
    # Create transistor object
    return Transistor(transistor_args, metadata_args, foster_args, switch_args, diode_args)

if __name__ == '__main__':
    transistor = Template()

    print(transistor.name)
    print(transistor.switch.manufacturer)
    print(transistor.switch.channel[0].v_i_data)

    # ToDo: store transistor in database