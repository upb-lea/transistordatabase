"""
Initial author: Henning Steinhagen
Date of creation: 04.01.2021
Last modified by: Henning
Date of modification: 01.02.2021
Version: 1.0
Compatibility: Python
Other files required: Numpy and ZODB package
Link to file: https://git.uni-paderborn.de/lea-git/lea-git-public/matlab-functions/transistor_database/-/blob/master/transistorDatabase/MatlabExport.py
ToDo: Check transistor name for forbidden symbols
ToDo: implement linearization and update attributes (each attribute has its own TODO)
ToDo: Add input parameters (e.g. for a given temperature set)

Description:
Pulls single transistor from the database and builds an single .mat file in the format of nested structs.
The file will only contain datatypes compatible to Matlab and Octave.

Input parameters: None yet. (ToDo!)
Output parameters: None as only a separately saved file will be created.
Example: Not yet included (ToDo!)
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
"""

import scipy.io as sio
import numpy as np


def compatibilityTest(Transistor, attribute):
    try:
        att = eval(attribute)
        if att is None:
            return np.nan
        else:
            return att

    except AttributeError:
        return np.nan


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
        else:
            i += 1
    return np.nan


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


# Exports transistor in legacy format
def exportTransistorV1(transistorName):
    Transistor = transistorName

    # maximum data for plots and for non-linear data, given by data sheet plots
    # TODO Set max points via variables (Given to the exporter function?)
    Temp_Switch_I_channel_max = 1200
    Temp_Switch_V_channel_max = 3.5
    Switch_I_channel_max = findChannelData(Transistor,'Transistor.switch.channel', 25, 'v_i_data', 'I_max')
    Switch_V_channel_max = findChannelData(Transistor, 'Transistor.switch.channel', 25, 'v_i_data', 'V_max')

    # Junction temperatures for channel losses and switching losses
    # TODO Set temperature via variables (Given to the exporter function?)
    Switch_T_J_channel = [25, 125]
    Switch_T_J_switching = [125, 150]

    # TODO Add linearized data
    Switch_r_channel = np.nan
    Switch_V0_channel = np.nan

    Switch_I_channel = np.linspace(0, Temp_Switch_I_channel_max, Temp_Switch_I_channel_max + 1)
    Switch_I_channel_T_J = [[findChannelData(transistorName, 'Transistor.switch.channel', 25, 'v_i_data', 'I')],
                            [findChannelData(transistorName, 'Transistor.switch.channel', 125, 'v_i_data', 'I')]]

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
    Switch_E_on_125 = findSwitchEnergyData(transistorName, 'Transistor.switch.e_on', 125,
                                           'Fill Attribute', 'Fill identifier')
    Switch_E_on_150 = findSwitchEnergyData(transistorName, 'Transistor.switch.e_on', 150,
                                           'Fill Attribute', 'Fill identifier')
    Switch_E_off_125 = findSwitchEnergyData(transistorName, 'Transistor.switch.e_off', 125,
                                           'Fill Attribute', 'Fill identifier')
    Switch_E_off_150 = findSwitchEnergyData(transistorName, 'Transistor.switch.e_off', 150,
                                           'Fill Attribute', 'Fill identifier')
    Switch_E_on_T_J = [[findSwitchEnergyData(transistorName, 'Transistor.switch.e_on', 125,
                                           'Fill Attribute', 'Fill identifier')],
                       [findSwitchEnergyData(transistorName, 'Transistor.switch.e_on', 150,
                                           'Fill Attribute', 'Fill identifier')]]
    Switch_E_off_T_J = [[findSwitchEnergyData(transistorName, 'Transistor.switch.e_off', 125,
                                             'Fill Attribute', 'Fill identifier')],
                        [findSwitchEnergyData(transistorName, 'Transistor.switch.e_off', 150,
                                             'Fill Attribute', 'Fill identifier')]]

    # TODO replace 'switchEnergy.*' when implemented in databaseClasses.py
    Switch_K_i = compatibilityTest(transistorName, 'Transistor.switch.switchEnergy.k_i')
    Switch_K_v = compatibilityTest(transistorName, 'Transistor.switch.switchEnergy.k_v')
    Switch_G_i = compatibilityTest(transistorName, 'Transistor.switch.switchEnergy.g_i')

    Switch_dict = {'Manufacturer': compatibilityTest(transistorName, 'Transistor.switch.manufacturer'),
                   'I_channel_max': Switch_I_channel_max,
                   'V_channel_max': Switch_V_channel_max,
                   'T_J_channel': Switch_T_J_channel,
                   'T_J_switching': Switch_T_J_switching,
                   'r_channel': Switch_r_channel,
                   'V0_channel': Switch_V0_channel,
                   'I_channel': Switch_I_channel,
                   'V_channel_vec': Switch_V_channel_vec,
                   'V_channel': Switch_V_channel,
                   'I_channel_25': findChannelData(transistorName, 'Transistor.switch.channel', 25, 'v_i_data', 'I'),
                   'I_channel_125': findChannelData(transistorName, 'Transistor.switch.channel', 125, 'v_i_data', 'I'),
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
                   'C_oss': compatibilityTest(transistorName, 'Transistor.switch.c_oss'),
                   'C_iss': compatibilityTest(transistorName, 'Transistor.switch.c_iss'),
                   'C_rss': compatibilityTest(transistorName, 'Transistor.switch.c_rss'),
                   'R_th_total': compatibilityTest(transistorName, 'Transistor.switch.thermal.t_th_total'),
                   'R_th_vector': compatibilityTest(transistorName, 'Transistor.switch.thermal.r_th_vector'),
                   'tau_total': compatibilityTest(transistorName, 'Transistor.switch.thermal.tau_total'),
                   'tau_vector': compatibilityTest(transistorName, 'Transistor.switch.thermal.tau_vector'),
                   'C_th_total': compatibilityTest(transistorName, 'Transistor.switch.thermal.c_th_total'),
                   'C_th_vector': compatibilityTest(transistorName, 'Transistor.switch.thermal.c_th_vector')}


    # maximum data for plots and for non-linear data, given by data sheet plots
    # TODO Set max points via Variable (Given to the exporter function)
    Temp_Diode_I_channel_max = 1200
    Temp_Diode_V_channel_max = 3.5
    Diode_I_channel_max = findChannelData(Transistor, 'Transistor.switch.channel', 25, 'v_i_data', 'I_max')
    Diode_V_channel_max = findChannelData(Transistor, 'Transistor.switch.channel', 25, 'v_i_data', 'V_max')

    # Junction temperatures for channel losses and switching losses
    # TODO Set temperature via Variable (Given to the exporter function?)
    Diode_T_J_channel = [25, 125]
    Diode_T_J_switching = [125, 150]

    # TODO Add function after linearized data is available
    Diode_r_channel = np.nan
    Diode_V0_channel = np.nan

    Diode_I_channel = np.linspace(0, Temp_Diode_I_channel_max, Temp_Diode_I_channel_max + 1)
    Diode_I_channel_T_J = [[findChannelData(transistorName, 'Transistor.diode.channel', 25, 'v_i_data', 'I')],
                           [findChannelData(transistorName, 'Transistor.diode.channel', 125, 'v_i_data', 'I')]]

    # TODO V_Channel Endpoint change to variable?
    Diode_V_channel = np.linspace(0, Temp_Diode_V_channel_max, 20)
    # TODO Add function after linearized data is added
    Diode_V_channel_vec = np.nan

    # TODO replace when implemented in databaseClasses.py
    Diode_T_J_ref = np.nan
    Diode_E_rr_ref = np.nan
    Diode_I_ref = np.nan
    Diode_V_ref = np.nan

    Diode_E_rr_125 = findSwitchEnergyData(transistorName, 'Transistor.diode.e_rr', 125,
                                           'Fill Attribute', 'Fill identifier')
    Diode_E_rr_150 = findSwitchEnergyData(transistorName, 'Transistor.diode.e_rr', 150,
                                           'Fill Attribute', 'Fill identifier')
    Diode_E_rr_T_J = [[findSwitchEnergyData(transistorName, 'Transistor.diode.e_rr', 125,
                                           'Fill Attribute', 'Fill identifier')],
                      [findSwitchEnergyData(transistorName, 'Transistor.diode.e_rr', 150,
                                           'Fill Attribute', 'Fill identifier')]]

    # TODO replace 'switchEnergy.*' when implemented in databaseClasses.py
    Diode_K_i = compatibilityTest(transistorName, 'Transistor.diode.switchEnergy.k_i')
    Diode_K_v = compatibilityTest(transistorName, 'Transistor.diode.switchEnergy.k_v')
    Diode_G_i = compatibilityTest(transistorName, 'Transistor.diode.switchEnergy.g_i')

    Diode_dict = {'Manufacturer': compatibilityTest(transistorName, 'Transistor.diode.manufacturer'),
                  'T_J_channel': Diode_T_J_channel,
                  'T_J_switching': Diode_T_J_switching,
                  'r_channel': Diode_r_channel,
                  'V0_channel': Diode_V0_channel,
                  'I_channel': Diode_I_channel,
                  'V_channel_vec': Diode_V_channel_vec,
                  'V_channel': Diode_V_channel,
                  'I_channel_25': findChannelData(transistorName, 'Transistor.diode.channel', 25, 'v_i_data', 'I'),
                  'I_channel_125': findChannelData(transistorName, 'Transistor.diode.channel', 125, 'v_i_data', 'I'),
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
                  'R_th_total': compatibilityTest(transistorName, 'Transistor.diode.thermal.t_th_total'),
                  'R_th_vector': compatibilityTest(transistorName, 'Transistor.diode.thermal.r_th_vector'),
                  'tau_total': compatibilityTest(transistorName, 'Transistor.diode.thermal.tau_total'),
                  'tau_vector': compatibilityTest(transistorName, 'Transistor.diode.thermal.tau_vector'),
                  'C_th_total': compatibilityTest(transistorName, 'Transistor.diode.thermal.c_th_total'),
                  'C_th_vector': compatibilityTest(transistorName, 'Transistor.diode.thermal.c_th_vector')}

    # TODO add after linearization function was implemented
    Transistor_I_linearize_UI_charts = np.nan

    Transistor_dict = {'Name': compatibilityTest(transistorName, 'Transistor.name'),
                       'R_th_CS': compatibilityTest(transistorName, 'Transistor.r_th_cs'),
                       'R_th_Switch_CS': compatibilityTest(transistorName, 'Transistor.r_th_switch_cs'),
                       'R_th_Diode_CS': compatibilityTest(transistorName, 'Transistor.r_th_diode_cs'),
                       'Manufacturer_Housing': compatibilityTest(transistorName, 'Transistor.meta.housing_type'),
                       'Type': compatibilityTest(transistorName, 'Transistor.transistor_type'),
                       'Template_Version': compatibilityTest(transistorName, 'Transistor.meta.template_version'),
                       'Template_Date': compatibilityTest(transistorName, 'Transistor.meta.template_date'),
                       'Author': compatibilityTest(transistorName, 'Transistor.meta.author'),
                       'Date_of_transistor_creation': compatibilityTest(transistorName, 'Transistor.meta.creation_date'),
                       'Comment': compatibilityTest(transistorName, 'Transistor.meta.comment'),
                       'U_max': compatibilityTest(transistorName, 'Transistor.v_max'),
                       'I_max': compatibilityTest(transistorName, 'Transistor.i_max'),
                       'I_linearize_UI_charts': Transistor_I_linearize_UI_charts,
                       'Switch': Switch_dict,
                       'Diode': Diode_dict}

    sio.savemat(Transistor.name + '.mat', {Transistor.name: Transistor_dict})


def exportTransistor(transistorName):
    Transistor = transistorName
    print(compatibilityTest(transistorName, 'Transistor.name'))
    print(compatibilityTest(transistorName, 'Transistor.author'))
    print(compatibilityTest(transistorName, 'Transistor.r_th_cs'))

    Metadata_dict = {'Author': compatibilityTest(transistorName, 'Transistor.meta.author'),
                     'Template_version': compatibilityTest(transistorName, 'Transistor.meta.template_version'),
                     'Template_date': compatibilityTest(transistorName, 'Transistor.meta.template_date'),
                     'Creation_date': compatibilityTest(transistorName, 'Transistor.meta.creation_date'),
                     'Last_modified': compatibilityTest(transistorName, 'Transistor.meta.last_modified'),
                     'Comment': compatibilityTest(transistorName, 'Transistor.meta.comment'),
                     'Manufacturer': compatibilityTest(transistorName, 'Transistor.meta.manufacturer'),
                     'Datasheet_hyperlink': compatibilityTest(transistorName, 'Transistor.meta.datasheet_hyperlink'),
                     'Datasheet_date': compatibilityTest(transistorName, 'Transistor.meta.datasheet_date'),
                     'Datasheet_version': compatibilityTest(transistorName, 'Transistor.meta.datasheet_version'),
                     'Housing_area': compatibilityTest(transistorName, 'Transistor.meta.housing_area'),
                     'Contact_area': compatibilityTest(transistorName, 'Transistor.meta.cooling_area'),
                     #                'Housing_type': compatibilityTest(Transistor.meta.housing_type)
                     }

    FosterThermalModel_dict = {'R_th_total': compatibilityTest(transistorName, 'Transistor.diode.thermal.r_th_total'),
                               'R_th_vector': compatibilityTest(transistorName, 'Transistor.diode.thermal.r_th_vector'),
                               'C_th_total': compatibilityTest(transistorName, 'Transistor.diode.thermal.c_th_total'),
                               'C_th_vector': compatibilityTest(transistorName, 'Transistor.diode.thermal.c_th_vector'),
                               'Tau_total': compatibilityTest(transistorName, 'Transistor.diode.thermal.tau_total'),
                               'Tau_vector': compatibilityTest(transistorName, 'Transistor.diode.thermal.tau_vector'),
                               'Transient_data': compatibilityTest(transistorName,
                                                                   'Transistor.diode.thermal.transient_data')}

    # ??? Transistor.Switch.meta
    Switch_dict = {'Comment': compatibilityTest(transistorName, 'Transistor.meta.comment'),
                   'Manufacturer': compatibilityTest(transistorName, 'Transistor.meta.manufacturer'),
                   'Technology': compatibilityTest(transistorName, 'Transistor.meta.technology'),
                   'c_oss': compatibilityTest(transistorName, 'Transistor.switch.c_oss'),
                   'c_iss': compatibilityTest(transistorName, 'Transistor.switch.c_iss'),
                   'c_rss': compatibilityTest(transistorName, 'Transistor.switch.c_rss'),
                   'channel': compatibilityTest(transistorName, 'Transistor.switch.channel'),
                   'e_on': compatibilityTest(transistorName, 'Transistor.switch.e_on'),
                   'e_off': compatibilityTest(transistorName, 'Transistor.switch.e_off')}

    # ??? Transistor.Diode.meta/thermal
    Diode_dict = {'Comment': compatibilityTest(transistorName, 'Transistor.meta.comment'),
                  'Manufacturer': compatibilityTest(transistorName, 'Transistor.meta.manufacturer'),
                  'Technology': compatibilityTest(transistorName, 'Transistor.meta.technology'),
                  'thermal': compatibilityTest(transistorName, 'Transistor.diode.thermal'),
                  'channel': compatibilityTest(transistorName, 'Transistor.diode.channel'),
                  'e_rr': compatibilityTest(transistorName, 'Transistor.diode.e_rr')}

    ChannelData_dict = {'t_j': compatibilityTest(transistorName, 'Transistor.switch.channel.t_j'),
                        'v_i_data': compatibilityTest(transistorName, 'Transistor.switch.channel.v_i_data')}

    SwitchEnergyData_dict = {
        'dataset_type': compatibilityTest(transistorName, 'Transistor.SwitchEnergyData.dataset_type'),
        't_j': compatibilityTest(transistorName, 'Transistor.SwitchEnergyData.t_j'),
        'v_supply': compatibilityTest(transistorName, 'Transistor.SwitchEnergyData.v_supply'),
        'v_g': compatibilityTest(transistorName, 'Transistor.SwitchEnergyData.v_g'),
        'e_x': compatibilityTest(transistorName, 'Transistor.SwitchEnergyData.e_x'),
        'r_g': compatibilityTest(transistorName, 'Transistor.SwitchEnergyData.r_g'),
        'i_x': compatibilityTest(transistorName, 'Transistor.SwitchEnergyData.i_x'),
        'i_e_data': compatibilityTest(transistorName, 'Transistor.SwitchEnergyData.i_e_data'),
        'r_e_data': compatibilityTest(transistorName, 'Transistor.SwitchEnergyData.r_e_data')}

    Transistor_dict = {'name': compatibilityTest(transistorName, 'Transistor.name'),
                       'type': compatibilityTest(transistorName, 'Transistor.type'),
                       'r_th_cs': compatibilityTest(transistorName, 'Transistor.r_th_cs'),
                       'r_th_switch': compatibilityTest(transistorName, 'Transistor.r_th_switch_cs'),
                       'r_th_diode_cs': compatibilityTest(transistorName, 'Transistor.r_th_diode_cs'),
                       'v_max': compatibilityTest(transistorName, 'Transistor.v_max'),
                       'i_max': compatibilityTest(transistorName, 'Transistor.i_max'),
                       'i_cont': compatibilityTest(transistorName, 'Transistor.i_cont'),
                       'Metadata': Metadata_dict,
                       'Switch': Switch_dict,
                       'Switch Energy Data': SwitchEnergyData_dict,
                       'Diode': Diode_dict,
                       'Channel Data': ChannelData_dict,
                       'Foster Thermal Model': FosterThermalModel_dict}

    sio.savemat('Transistor_test.mat', {'Transistor_test': Transistor_dict})
