"""
Initial author: Henning Steinhagen
Date of creation: 04.01.2021
Last modified by: Henning
Date of modification: 02.02.2021
Version: 1.0
Compatibility: Python
Other files required: Numpy and SciPy package
Link to file: https://git.uni-paderborn.de/lea-git/lea-git-public/matlab-functions/transistor_database/-/blob/master/transistorDatabase/MatlabExport.py
ToDo: Check transistor name for forbidden symbols
ToDo: implement linearization and update attributes (each attribute has its own TODO)
ToDo: Add input parameters (e.g. for a given temperature set)

Description:
Exports transistor objects for multiple use cases.
(So far Matlab/Octave)

User relevant functions:
export_simulink_v1 : exports .mat file in a format used in older simulations
export_matlab_v1 : exports .mat file in the same format as it is saved in the database

Known Bugs:
Changelog:
VERSION / DATE / NAME: Comment
1.0.0 / 04.01.2021 / Henning Steinhagen: Initial Version
1.0.1 / 08.01.2021 / Henning Steinhagen: Reformatted Code + exportTransistor implementation
1.0.2 / 18.01.2021 / Manuel Klaedtke: Updated names and implemented changes accordingly to the restructuring of
Metadata class and some other attributes
1.1.0 / 24.01.2021 / Henning Steinhagen: Implemented compatibilityCheck
1.2.0 / 25.01.2021 / Henning Steinhagen: Implemented exportTransistorV1 (Legacy format to old .mat Database)
1.2.1 / 01.02.2021 / Henning Steinhagen: Added functionality to exportTransistorV1 and build functions to extract Data
1.3.0 / 02.02.2021 / Henning Steinhagen: Added functionality to export_matlab_v1 + commented code + renamed functions
1.4.0 / 17.02.2021 / Manuel Klädtke: Removed Metadata class and added all its attributes to Transistor class. Updated
export functions accordingly.
"""

import scipy.io as sio
import numpy as np


##########################################################################
# checks attribute for occurrences of None an replace it with n.nan
# Input: transistor object, path to given attribute
# Output: returns attribute value or np.nan
##########################################################################
def compatibilityTest(Transistor, attribute):
    try:
        att = eval(attribute)
        if att is None:
            return np.nan
        else:
            return att

    except AttributeError:
        return np.nan


##########################################################################
# finds attributes in the ChannelData class instance
# Input: transistor object, path to given ChannelData instance,
#        temperature t_j, additional path, Key (e.g. E_on/E_off/E_rr)
# Output: returns SwitchEnergy dataset at given temperature point
##########################################################################
def findChannelData(Transistor, channel, temperature, attribute, identifier):

    ChannelData = eval(channel)

    i = 0
    for x in ChannelData:
        if ChannelData[i].t_j == temperature:
            DataSet = getattr(ChannelData[i], attribute)
            # TODO add interpolLUT function and return instead of raw DataSet for V/I
            if identifier == 'V':
                return DataSet[0]
            elif identifier == 'I':
                return DataSet[1]
            elif identifier == 'V_max':
                return np.max(DataSet[0])
            elif identifier == 'V_min':
                return np.min(DataSet[0])
            elif identifier == 'I_max':
                return np.max(DataSet[1])
            elif identifier == 'I_min':
                return np.min(DataSet[1])
            elif identifier == 0:
                return DataSet
        else:
            i += 1
    return np.nan

##########################################################################
# finds attributes in the SwitchEnergyData class instance
# Input: transistor object, path to given switchEnergyData instance,
#        temperature t_j, additional path, Key (e.g. E_on/E_off/E_rr)
# Output: returns SwitchEnergy dataset at given temperature point
##########################################################################
# TODO Modify identifier when implemented in databaseClasses.py
# TODO Modify which DataSet is used when identifiers are implemented
def findSwitchEnergyData(Transistor, switchEnergyInstance, temperature, attribute, identifier):

    SwitchEnergyData = eval(switchEnergyInstance)
    i = 0

    for x in SwitchEnergyData:
        if SwitchEnergyData[i].t_j == temperature:
            DataSet = getattr(SwitchEnergyData[i], attribute)
            # TODO add interpolLUT function and return instead of raw DataSet
            if identifier == 'E_on':
                return DataSet[0]
            elif identifier == 'E_off':
                return DataSet[1]
            elif identifier == 'E_rr':
                return DataSet[0]
        else:
            i += 1
    return np.nan


##########################################################################
# Gather list data (e.g. channel/e_on/e_off/e_rr) and check for 'None'
# Input: transistor object, attribute path to list
# Output: return a matlab compatible list of all attributes
##########################################################################
def buildList(Transistor, attribute):

    if compatibilityTest(Transistor, attribute) is not np.nan:
        ListData = eval(attribute)
        Dataset = np.empty((len(ListData),), dtype=np.object)
        for i in range(len(ListData)):
            for attr, value in vars(ListData[i]).items():
                if value is None:
                    setattr(ListData[i], attr, np.nan)
            Dataset[i] = ListData[i]
    else:
        Dataset = np.nan
    return Dataset


##########################################################################
# Creates .mat file compatible with Simulink models
# Input: transistor object
# Output: None (But creates a separate .mat file)
##########################################################################
def export_simulink_v1(transistorName):
    Transistor = transistorName

    # maximum data for plots and for non-linear data, given by data sheet plots
    # TODO Set max points via variables (Given to the exporter function?)
    Temp_Switch_I_channel_max = 1200
    Temp_Switch_V_channel_max = 3.5
    Switch_I_channel_max = findChannelData(Transistor, 'Transistor.switch.channel', 25, 'graph_v_i', 'I_max')
    Switch_V_channel_max = findChannelData(Transistor, 'Transistor.switch.channel', 25, 'graph_v_i', 'V_max')

    # Junction temperatures for channel losses and switching losses
    # TODO Set temperature via variables (Given to the exporter function?)
    Switch_T_J_channel = [25, 125]
    Switch_T_J_switching = [125, 150]

    # TODO Add linearized data
    Switch_r_channel = np.nan
    Switch_V0_channel = np.nan

    Switch_I_channel = np.linspace(0, Temp_Switch_I_channel_max, Temp_Switch_I_channel_max + 1)
    Switch_I_channel_T_J = [[findChannelData(Transistor, 'Transistor.switch.channel', 25, 'graph_v_i', 'I')],
                            [findChannelData(Transistor, 'Transistor.switch.channel', 125, 'graph_v_i', 'I')]]

    # TODO V_Channel endpoint change to variable?
    Switch_V_channel = np.linspace(0, Temp_Switch_V_channel_max, 20)
    # TODO Add function after linearized data is added
    Switch_V_channel_vec = np.nan

    # TODO replace when implemented in databaseClasses.py
    Switch_T_J_ref = np.nan
    Switch_E_on_ref = np.nan
    Switch_E_off_ref = np.nan
    Switch_I_ref = np.nan
    Switch_V_ref = np.nan
    Switch_R_g_on_ref = np.nan
    Switch_R_g_off_ref = np.nan

    # TODO implement interpolLUT either here in findSwitchEnergyData or in databaseClasses.py
    Switch_E_on_125 = findSwitchEnergyData(Transistor, 'Transistor.switch.e_on', 125,
                                           'Fill Attribute', 'Fill identifier')
    Switch_E_on_150 = findSwitchEnergyData(Transistor, 'Transistor.switch.e_on', 150,
                                           'Fill Attribute', 'Fill identifier')
    Switch_E_off_125 = findSwitchEnergyData(Transistor, 'Transistor.switch.e_off', 125,
                                            'Fill Attribute', 'Fill identifier')
    Switch_E_off_150 = findSwitchEnergyData(Transistor, 'Transistor.switch.e_off', 150,
                                            'Fill Attribute', 'Fill identifier')
    Switch_E_on_T_J = [[findSwitchEnergyData(Transistor, 'Transistor.switch.e_on', 125,
                                             'Fill Attribute', 'Fill identifier')],
                       [findSwitchEnergyData(Transistor, 'Transistor.switch.e_on', 150,
                                             'Fill Attribute', 'Fill identifier')]]
    Switch_E_off_T_J = [[findSwitchEnergyData(Transistor, 'Transistor.switch.e_off', 125,
                                              'Fill Attribute', 'Fill identifier')],
                        [findSwitchEnergyData(Transistor, 'Transistor.switch.e_off', 150,
                                              'Fill Attribute', 'Fill identifier')]]

    # TODO replace 'switchEnergy.*' when implemented in databaseClasses.py
    Switch_K_i = compatibilityTest(Transistor, 'Transistor.switch.switchEnergy.k_i')
    Switch_K_v = compatibilityTest(Transistor, 'Transistor.switch.switchEnergy.k_v')
    Switch_G_i = compatibilityTest(Transistor, 'Transistor.switch.switchEnergy.g_i')

    Switch_dict = {'Manufacturer': compatibilityTest(Transistor, 'Transistor.switch.manufacturer'),
                   'I_channel_max': Switch_I_channel_max,
                   'V_channel_max': Switch_V_channel_max,
                   'T_J_channel': Switch_T_J_channel,
                   'T_J_switching': Switch_T_J_switching,
                   'r_channel': Switch_r_channel,
                   'V0_channel': Switch_V0_channel,
                   'I_channel': Switch_I_channel,
                   'V_channel_vec': Switch_V_channel_vec,
                   'V_channel': Switch_V_channel,
                   'I_channel_25': findChannelData(Transistor, 'Transistor.switch.channel', 25, 'graph_v_i', 'I'),
                   'I_channel_125': findChannelData(Transistor, 'Transistor.switch.channel', 125, 'graph_v_i', 'I'),
                   'I_channel_T_J': Switch_I_channel_T_J,
                   'T_J_ref': Switch_T_J_ref,
                   'E_on_ref': Switch_E_on_ref,
                   'E_off_ref': Switch_E_off_ref,
                   'I_ref': Switch_I_ref,
                   'V_ref': Switch_V_ref,
                   'R_g_on_ref': Switch_R_g_on_ref,
                   'R_g_off_ref': Switch_R_g_off_ref,
                   'K_i': Switch_K_i,
                   'K_v': Switch_K_v,
                   'G_i': Switch_G_i,
                   'E_on_125': Switch_E_on_125,
                   'E_on_150': Switch_E_on_150,
                   'E_off_125': Switch_E_off_125,
                   'E_off_150': Switch_E_off_150,
                   'E_on_T_J': Switch_E_on_T_J,
                   'E_off_T_J': Switch_E_off_T_J,
                   'C_oss': compatibilityTest(Transistor, 'Transistor.switch.c_oss'),
                   'C_iss': compatibilityTest(Transistor, 'Transistor.switch.c_iss'),
                   'C_rss': compatibilityTest(Transistor, 'Transistor.switch.c_rss'),
                   'R_th_total': compatibilityTest(Transistor, 'Transistor.switch.thermal_foster.t_th_total'),
                   'R_th_vector': compatibilityTest(Transistor, 'Transistor.switch.thermal_foster.r_th_vector'),
                   'tau_total': compatibilityTest(Transistor, 'Transistor.switch.thermal_foster.tau_total'),
                   'tau_vector': compatibilityTest(Transistor, 'Transistor.switch.thermal_foster.tau_vector'),
                   'C_th_total': compatibilityTest(Transistor, 'Transistor.switch.thermal_foster.c_th_total'),
                   'C_th_vector': compatibilityTest(Transistor, 'Transistor.switch.thermal_foster.c_th_vector')}


    # maximum data for plots and for non-linear data, given by data sheet plots
    # TODO Set max points via Variable (Given to the exporter function)
    Temp_Diode_I_channel_max = 1200
    Temp_Diode_V_channel_max = 3.5
    Diode_I_channel_max = findChannelData(Transistor, 'Transistor.switch.channel', 25, 'graph_v_i', 'I_max')
    Diode_V_channel_max = findChannelData(Transistor, 'Transistor.switch.channel', 25, 'graph_v_i', 'V_max')

    # Junction temperatures for channel losses and switching losses
    # TODO Set temperature via Variable (Given to the exporter function?)
    Diode_T_J_channel = [25, 125]
    Diode_T_J_switching = [125, 150]

    # TODO Add function after linearized data is available
    Diode_r_channel = np.nan
    Diode_V0_channel = np.nan

    Diode_I_channel = np.linspace(0, Temp_Diode_I_channel_max, Temp_Diode_I_channel_max + 1)
    Diode_I_channel_T_J = [[findChannelData(Transistor, 'Transistor.diode.channel', 25, 'graph_v_i', 'I')],
                           [findChannelData(Transistor, 'Transistor.diode.channel', 125, 'graph_v_i', 'I')]]

    # TODO V_Channel Endpoint change to variable?
    Diode_V_channel = np.linspace(0, Temp_Diode_V_channel_max, 20)
    # TODO Add function after linearized data is added
    Diode_V_channel_vec = np.nan

    # TODO replace when implemented in databaseClasses.py
    Diode_T_J_ref = np.nan
    Diode_E_rr_ref = np.nan
    Diode_I_ref = np.nan
    Diode_V_ref = np.nan

    Diode_E_rr_125 = findSwitchEnergyData(Transistor, 'Transistor.diode.e_rr', 125,
                                          'Fill Attribute', 'Fill identifier')
    Diode_E_rr_150 = findSwitchEnergyData(Transistor, 'Transistor.diode.e_rr', 150,
                                          'Fill Attribute', 'Fill identifier')
    Diode_E_rr_T_J = [[findSwitchEnergyData(Transistor, 'Transistor.diode.e_rr', 125,
                                            'Fill Attribute', 'Fill identifier')],
                      [findSwitchEnergyData(Transistor, 'Transistor.diode.e_rr', 150,
                                            'Fill Attribute', 'Fill identifier')]]

    # TODO replace 'switchEnergy.*' when implemented in databaseClasses.py
    Diode_K_i = compatibilityTest(Transistor, 'Transistor.diode.switchEnergy.k_i')
    Diode_K_v = compatibilityTest(Transistor, 'Transistor.diode.switchEnergy.k_v')
    Diode_G_i = compatibilityTest(Transistor, 'Transistor.diode.switchEnergy.g_i')

    Diode_dict = {'Manufacturer': compatibilityTest(Transistor, 'Transistor.diode.manufacturer'),
                  'T_J_channel': Diode_T_J_channel,
                  'T_J_switching': Diode_T_J_switching,
                  'r_channel': Diode_r_channel,
                  'V0_channel': Diode_V0_channel,
                  'I_channel': Diode_I_channel,
                  'V_channel_vec': Diode_V_channel_vec,
                  'V_channel': Diode_V_channel,
                  'I_channel_25': findChannelData(Transistor, 'Transistor.diode.channel', 25, 'graph_v_i', 'I'),
                  'I_channel_125': findChannelData(Transistor, 'Transistor.diode.channel', 125, 'graph_v_i', 'I'),
                  'I_channel_T_J':  Diode_I_channel_T_J,
                  'T_J_ref': Diode_T_J_ref,
                  'E_rr_ref': Diode_E_rr_ref,
                  'I_ref': Diode_I_ref,
                  'V_ref': Diode_V_ref,
                  'K_i': Diode_K_i,
                  'K_v': Diode_K_v,
                  'G_i': Diode_G_i,
                  'E_rr_125': Diode_E_rr_125,
                  'E_rr_150': Diode_E_rr_150,
                  'E_rr_T_J': Diode_E_rr_T_J,
                  'R_th_total': compatibilityTest(Transistor, 'Transistor.diode.thermal_foster.t_th_total'),
                  'R_th_vector': compatibilityTest(Transistor, 'Transistor.diode.thermal_foster.r_th_vector'),
                  'tau_total': compatibilityTest(Transistor, 'Transistor.diode.thermal_foster.tau_total'),
                  'tau_vector': compatibilityTest(Transistor, 'Transistor.diode.thermal_foster.tau_vector'),
                  'C_th_total': compatibilityTest(Transistor, 'Transistor.diode.thermal_foster.c_th_total'),
                  'C_th_vector': compatibilityTest(Transistor, 'Transistor.diode.thermal_foster.c_th_vector')}

    # TODO add after linearization function was implemented
    Transistor_I_linearize_UI_charts = np.nan

    Transistor_dict = {'Name': compatibilityTest(Transistor, 'Transistor.name'),
                       'R_th_CS': compatibilityTest(Transistor, 'Transistor.r_th_cs'),
                       'R_th_Switch_CS': compatibilityTest(Transistor, 'Transistor.r_th_switch_cs'),
                       'R_th_Diode_CS': compatibilityTest(Transistor, 'Transistor.r_th_diode_cs'),
                       'Manufacturer_Housing': compatibilityTest(Transistor, 'Transistor.housing_type'),
                       'Type': compatibilityTest(Transistor, 'Transistor.transistor_type'),
                       'Template_Version': compatibilityTest(Transistor, 'Transistor.template_version'),
                       'Template_Date': compatibilityTest(Transistor, 'Transistor.template_date'),
                       'Author': compatibilityTest(Transistor, 'Transistor.author'),
                       'Date_of_transistor_creation': compatibilityTest(Transistor, 'Transistor.creation_date'),
                       'Comment': compatibilityTest(Transistor, 'Transistor.comment'),
                       'U_max': compatibilityTest(Transistor, 'Transistor.v_max'),
                       'I_max': compatibilityTest(Transistor, 'Transistor.i_max'),
                       'I_linearize_UI_charts': Transistor_I_linearize_UI_charts,
                       'Switch': Switch_dict,
                       'Diode': Diode_dict}

    sio.savemat(Transistor.name + '_S1.mat', {Transistor.name: Transistor_dict})


##########################################################################
# Creates .mat file with raw transistor data
# Input: transistor object
# Output: None (But creates a separate .mat file)
##########################################################################
def export_matlab_v1(transistorName):
    Transistor = transistorName

    Diode_Foster_dict = {'R_th_total': compatibilityTest(Transistor, 'Transistor.diode.thermal_foster.r_th_total'),
                         'R_th_vector': compatibilityTest(Transistor, 'Transistor.diode.thermal_foster.r_th_vector'),
                         'C_th_total': compatibilityTest(Transistor, 'Transistor.diode.thermal_foster.c_th_total'),
                         'C_th_vector': compatibilityTest(Transistor, 'Transistor.diode.thermal_foster.c_th_vector'),
                         'Tau_total': compatibilityTest(Transistor, 'Transistor.diode.thermal_foster.tau_total'),
                         'Tau_vector': compatibilityTest(Transistor, 'Transistor.diode.thermal_foster.tau_vector'),
                         'Transient_data': compatibilityTest(Transistor, 'Transistor.diode.thermal_foster.transient_data')}

    Switch_Foster_dict = {'R_th_total': compatibilityTest(Transistor, 'Transistor.switch.thermal_foster.r_th_total'),
                          'R_th_vector': compatibilityTest(Transistor, 'Transistor.switch.thermal_foster.r_th_vector'),
                          'C_th_total': compatibilityTest(Transistor, 'Transistor.switch.thermal_foster.c_th_total'),
                          'C_th_vector': compatibilityTest(Transistor, 'Transistor.switch.thermal_foster.c_th_vector'),
                          'Tau_total': compatibilityTest(Transistor, 'Transistor.switch.thermal_foster.tau_total'),
                          'Tau_vector': compatibilityTest(Transistor, 'Transistor.switch.thermal_foster.tau_vector'),
                          'Transient_data': compatibilityTest(Transistor, 'Transistor.switch.thermal_foster.transient_data')}

    Switch_dict = {'Comment': compatibilityTest(Transistor, 'Transistor.comment'),
                   'Manufacturer': compatibilityTest(Transistor, 'Transistor.manufacturer'),
                   'Technology': compatibilityTest(Transistor, 'Transistor.technology'),
                   'c_oss': compatibilityTest(Transistor, 'Transistor.switch.c_oss'),
                   'c_iss': compatibilityTest(Transistor, 'Transistor.switch.c_iss'),
                   'c_rss': compatibilityTest(Transistor, 'Transistor.switch.c_rss'),
                   'channel': buildList(Transistor, 'Transistor.switch.channel'),
                   'e_on': buildList(Transistor, 'Transistor.switch.e_on'),
                   'e_off': buildList(Transistor, 'Transistor.switch.e_off'),
                   'Foster Thermal Model': Switch_Foster_dict}

    Diode_dict = {'Comment': compatibilityTest(Transistor, 'Transistor.comment'),
                  'Manufacturer': compatibilityTest(Transistor, 'Transistor.manufacturer'),
                  'Technology': compatibilityTest(Transistor, 'Transistor.technology'),
                  'channel': buildList(Transistor, 'Transistor.diode.channel'),
                  'e_rr': buildList(Transistor, 'Transistor.diode.e_rr'),
                  'Foster Thermal Model': Diode_Foster_dict}

    Transistor_dict = {'name': compatibilityTest(Transistor, 'Transistor.name'),
                       'type': compatibilityTest(Transistor, 'Transistor.type'),
                       'Author': compatibilityTest(Transistor, 'Transistor.author'),
                       'Template_version': compatibilityTest(Transistor, 'Transistor.template_version'),
                       'Template_date': compatibilityTest(Transistor, 'Transistor.template_date'),
                       'Creation_date': compatibilityTest(Transistor, 'Transistor.creation_date'),
                       'Last_modified': compatibilityTest(Transistor, 'Transistor.last_modified'),
                       'Comment': compatibilityTest(Transistor, 'Transistor.comment'),
                       'Manufacturer': compatibilityTest(Transistor, 'Transistor.manufacturer'),
                       'Datasheet_hyperlink': compatibilityTest(Transistor, 'Transistor.datasheet_hyperlink'),
                       'Datasheet_date': compatibilityTest(Transistor, 'Transistor.datasheet_date'),
                       'Datasheet_version': compatibilityTest(Transistor, 'Transistor.datasheet_version'),
                       'Housing_area': compatibilityTest(Transistor, 'Transistor.housing_area'),
                       'Contact_area': compatibilityTest(Transistor, 'Transistor.cooling_area'),
                       'Housing_type': compatibilityTest(Transistor, 'Transistor.housing_type'),
                       'r_th_cs': compatibilityTest(Transistor, 'Transistor.r_th_cs'),
                       'r_th_switch': compatibilityTest(Transistor, 'Transistor.r_th_switch_cs'),
                       'r_th_diode_cs': compatibilityTest(Transistor, 'Transistor.r_th_diode_cs'),
                       'v_max': compatibilityTest(Transistor, 'Transistor.v_max'),
                       'i_max': compatibilityTest(Transistor, 'Transistor.i_max'),
                       'i_cont': compatibilityTest(Transistor, 'Transistor.i_cont'),
                       'Switch': Switch_dict,
                       'Diode': Diode_dict}

    sio.savemat(Transistor.name + '_M1.mat', {Transistor.name: Transistor_dict})