"""
Initial author: Henning Steinhagen
Date of creation: 04.01.2021
Last modified by: Henning
Date of modification: 08.01.2021
Version: 1.0
Compatibility: Python
Other files required: Numpy and ZODB package
Link to file: https://git.uni-paderborn.de/lea-git/lea-git-public/matlab-functions/transistor_database/-/blob/master/transistorDatabase/MatlabExport.py
ToDo: Create Metadata cases.
ToDo: Load an object from the DB.
ToDo: Change Filename

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


# Exports transistor in legacy format
def exportTransistorV1(transistorName):
    Transistor = transistorName

    zzz = np.nan

    Switch_dict = {'Manufacturer': compatibilityTest(transistorName, 'Transistor.switch.manufacturer'),
                   'I_channel_max': zzz,
                   'V_channel_max': zzz,
                   'T_J_channel': zzz,
                   'T_J_switching': zzz,
                   'r_channel': zzz,
                   'V0_channel': zzz,
                   'I_channel': zzz,
                   'V_channel_vec': zzz,
                   'V_channel': zzz,
                   'I_channel_25': findChannelData(transistorName, 'Transistor.switch.channel', 25, 'v_i_data', 'I'),
                   'I_channel_125': findChannelData(transistorName, 'Transistor.switch.channel', 125, 'v_i_data', 'I'),
                   'I_channel_T_J': zzz,
                   'T_J_ref': zzz,
                   'E_on_ref': zzz,
                   'E_off_ref': zzz,
                   'I_ref': zzz,
                   'V_ref': zzz,
                   'R_g_on_ref': zzz,
                   'R_g_off_ref': zzz,
                   'K_i': zzz,
                   'K_v': zzz,
                   'G_i': zzz,
                   'E_on_125': zzz,
                   'E_on_150': zzz,
                   'E_off_125': zzz,
                   'E_off_150': zzz,
                   'E_on_T_J': zzz,
                   'E_off_T_J': zzz,
                   'C_oss': compatibilityTest(transistorName, 'Transistor.switch.c_oss'),
                   'C_iss': compatibilityTest(transistorName, 'Transistor.switch.c_iss'),
                   'C_rss': compatibilityTest(transistorName, 'Transistor.switch.c_rss'),
                   'R_th_total': compatibilityTest(transistorName, 'Transistor.switch.thermal.t_th_total'),
                   'R_th_vector': compatibilityTest(transistorName, 'Transistor.switch.thermal.r_th_vector'),
                   'tau_total': compatibilityTest(transistorName, 'Transistor.switch.thermal.tau_total'),
                   'tau_vector': compatibilityTest(transistorName, 'Transistor.switch.thermal.tau_vector'),
                   'C_th_total': compatibilityTest(transistorName, 'Transistor.switch.thermal.c_th_total'),
                   'C_th_vector': compatibilityTest(transistorName, 'Transistor.switch.thermal.c_th_vector')}

    Diode_dict = {'Manufacturer': compatibilityTest(transistorName, 'Transistor.diode.manufacturer'),
                  'T_J_channel': zzz,
                  'T_J_switching': zzz,
                  'r_channel': zzz,
                  'V0_channel': zzz,
                  'I_channel': zzz,
                  'V_channel_vec': zzz,
                  'V_channel': zzz,
                  'I_channel_25': findChannelData(transistorName, 'Transistor.diode.channel', 25, 'v_i_data', 'I'),
                  'I_channel_125': findChannelData(transistorName, 'Transistor.diode.channel', 125, 'v_i_data', 'I'),
                  'I_channel_T_J': zzz,
                  'T_J_ref': zzz,
                  'E_rr_ref': zzz,
                  'I_ref': zzz,
                  'V_ref': zzz,
                  'K_i': zzz,
                  'K_v': zzz,
                  'G_i': zzz,
                  'E_rr_125': zzz,
                  'E_rr_150': zzz,
                  'E_rr_T_J': zzz,
                  'R_th_total': compatibilityTest(transistorName, 'Transistor.diode.thermal.t_th_total'),
                  'R_th_vector': compatibilityTest(transistorName, 'Transistor.diode.thermal.r_th_vector'),
                  'tau_total': compatibilityTest(transistorName, 'Transistor.diode.thermal.tau_total'),
                  'tau_vector': compatibilityTest(transistorName, 'Transistor.diode.thermal.tau_vector'),
                  'C_th_total': compatibilityTest(transistorName, 'Transistor.diode.thermal.c_th_total'),
                  'C_th_vector': compatibilityTest(transistorName, 'Transistor.diode.thermal.c_th_vector')}

    Transistor_dict = {'Name': compatibilityTest(transistorName, 'Transistor.name'),
                       'R_th_CS': zzz,
                       'R_th_Switch_CS': zzz,
                       'R_th_Diode_CS': zzz,
                       'Manufacturer_Housing': compatibilityTest(transistorName, 'Transistor.meta.housing_type'),
                       'Type': compatibilityTest(transistorName, 'Transistor.transistor_type'),
                       'Template_Version': compatibilityTest(transistorName, 'Transistor.meta.template_version'),
                       'Template_Date': compatibilityTest(transistorName, 'Transistor.meta.template_date'),
                       'Author': compatibilityTest(transistorName, 'Transistor.meta.author'),
                       'Date_of_transistor_creation': compatibilityTest(transistorName, 'Transistor.meta.creation_date'),
                       'Comment': compatibilityTest(transistorName, 'Transistor.meta.comment'),
                       'U_max': compatibilityTest(transistorName, 'Transistor.v_max'),
                       'I_max': compatibilityTest(transistorName, 'Transistor.i_max'),
                       'I_linearize_UI_charts': zzz,
                       'Switch': Switch_dict,
                       'Diode': Diode_dict}

    sio.savemat('Transistor_test.mat', {'Transistor_test': Transistor_dict})


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
