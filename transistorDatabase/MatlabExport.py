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


def compatibilityTest (attribute):
    if attribute is None:
        return np.nan
    else:
        return attribute

#Exports transistor in legacy format
def exportTransistorV1(transistorName):

    Transistor = transistorName

    zzz = 0

    Switch_dict = {'Manufacturer': zzz,
                   'I_channel_max': zzz,
                   'V_channel_max': zzz,
                   'T_J_channel': zzz,
                   'T_J_switching': zzz,
                   'r_channel': zzz,
                   'V0_channel': zzz,
                   'I_channel': zzz,
                   'V_channel_vec': zzz,
                   'V_channel': zzz,
                   'I_channel_25': zzz,
                   'I_channel_125': zzz,
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
                   'C_oss': zzz,
                   'C_iss': zzz,
                   'C_rss': zzz,
                   'R_th_total': zzz,
                   'R_th_vector': zzz,
                   'tau_total': zzz,
                   'tau_vector': zzz,
                   'C_th_total': zzz,
                   'C_th_vector': zzz}

    Diode_dict = {'Manufacturer': zzz,
                   'T_J_channel': zzz,
                   'T_J_switching': zzz,
                   'r_channel': zzz,
                   'V0_channel': zzz,
                   'I_channel': zzz,
                   'V_channel_vec': zzz,
                   'V_channel': zzz,
                   'I_channel_25': zzz,
                   'I_channel_125': zzz,
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
                   'R_th_total': zzz,
                   'R_th_vector': zzz,
                   'tau_total': zzz,
                   'tau_vector': zzz,
                   'C_th_vector': zzz}

    Transistor_dict = {'Name': zzz,
                       'R_th_CS': zzz,
                       'R_th_Switch_CS': zzz,
                       'R_th_Diode_CS': zzz,
                       'Manufacturer_Housing': zzz,
                       'Type': zzz,
                       'Template_Version': zzz,
                       'Template_Date': zzz,
                       'Author': zzz,
                       'Date_of_transitor_creation': zzz,
                       'Comment': zzz,
                       'U_max': zzz,
                       'I_max': zzz,
                       'I_linearize_UI_charts': zzz,
                       'Switch': Switch_dict,
                       'Diode': Diode_dict}

    sio.savemat('Transistor_test.mat', {'Transistor_test': Transistor_dict})



def exportTransistor(transistorName):

    Transistor = transistorName

    Metadata_dict = {'Author': compatibilityTest(Transistor.Metadata.author),
                     'Template_version': compatibilityTest(Transistor.Metadata.template_version),
                     'Template_date': compatibilityTest(Transistor.Metadata.template_date),
                     'Creation_date': compatibilityTest(Transistor.Metadata.creation_date),
                     'Last_modified': compatibilityTest(Transistor.Metadata.last_modified),
                     'Comment': compatibilityTest(Transistor.Metadata.comment),
                     'Manufacturer': compatibilityTest(Transistor.Metadata.manufacturer),
                     'Datasheet_hyperlink': compatibilityTest(Transistor.Metadata.datasheet_hyperlink),
                     'Datasheet_date': compatibilityTest(Transistor.Metadata.datasheet_date),
                     'Datasheet_version': compatibilityTest(Transistor.Metadata.datasheet_version),
                     'Housing_area': compatibilityTest(Transistor.Metadata.housing_area),
                     'Contact_area': compatibilityTest(Transistor.Metadata.contact_area),
                     'Housing_type': compatibilityTest(Transistor.Metadata.housing_type)}

    FosterThermalModel_dict = {'R_th_total': compatibilityTest(Transistor.FosterThermalModel.r_th_total),
                               'R_th_vector': compatibilityTest(Transistor.FosterThermalModel.r_th_vector),
                               'C_th_total': compatibilityTest(Transistor.FosterThermalModel.c_th_total),
                               'C_th_vector': compatibilityTest(Transistor.FosterThermalModel.c_th_vector),
                               'Tau_total': compatibilityTest(Transistor.FosterThermalModel.tau_total),
                               'Tau_vector': compatibilityTest(Transistor.FosterThermalModel.tau_vector),
                               'Transient_data': compatibilityTest(Transistor.FosterThermalModel.transient_data)}

    # ??? Transistor.Switch.meta
    Switch_dict = {'Comment': compatibilityTest(Transistor.Metadata.comment),
                   'Manufacturer': compatibilityTest(Transistor.Metadata.manufacturer),
                   'Technology': compatibilityTest(Transistor.Metadata.technology),
                   'c_oss': compatibilityTest(Transistor.Switch.c_oss),
                   'c_iss': compatibilityTest(Transistor.Switch.c_iss),
                   'c_rss': compatibilityTest(Transistor.Switch.c_rss),
                   'meta': compatibilityTest(Transistor.Switch.meta),
                   'channel': compatibilityTest(Transistor.Switch.channel),
                   'e_on': compatibilityTest(Transistor.Switch.e_on),
                   'e_off': compatibilityTest(Transistor.Switch.e_off)}

    # ??? Transistor.Diode.meta/thermal
    Diode_dict = {'Comment': compatibilityTest(Transistor.Metadata.comment),
                  'Manufacturer': compatibilityTest(Transistor.Metadata.manufacturer),
                  'Technology': compatibilityTest(Transistor.Metadata.technology),
                  'thermal': compatibilityTest(Transistor.Diode.thermal),
                  'channel': compatibilityTest(Transistor.Diode.channel),
                  'e_rr': compatibilityTest(Transistor.Diode.e_rr)}

    ChannelData_dict = {'t_j': compatibilityTest(Transistor.ChannelData.t_j),
                        'v_i_data': compatibilityTest(Transistor.ChannelData.v_i_data)}

    SwitchEnergyData_dict = {'dataset_type': compatibilityTest(Transistor.SwitchEnergyData.dataset_type),
                             't_j': compatibilityTest(Transistor.SwitchEnergyData.t_j),
                             'v_supply': compatibilityTest(Transistor.SwitchEnergyData.v_supply),
                             'v_g': compatibilityTest(Transistor.SwitchEnergyData.v_g),
                             'e_x': compatibilityTest(Transistor.SwitchEnergyData.e_x),
                             'r_g': compatibilityTest(Transistor.SwitchEnergyData.r_g),
                             'i_x': compatibilityTest(Transistor.SwitchEnergyData.i_x),
                             'i_e_data': compatibilityTest(Transistor.SwitchEnergyData.i_e_data),
                             'r_e_data': compatibilityTest(Transistor.SwitchEnergyData.r_e_data)}

    Transistor_dict = {'name': compatibilityTest(Transistor.name),
                       'type': compatibilityTest(Transistor.type),
                       'r_th_cs': compatibilityTest(Transistor.r_th_cs),
                       'r_th_switch': compatibilityTest(Transistor.r_th_switch_cs),
                       'r_th_diode_cs': compatibilityTest(Transistor.r_th_diode_cs),
                       'v_max': compatibilityTest(Transistor.v_max),
                       'i_max': compatibilityTest(Transistor.i_max),
                       'i_cont': compatibilityTest(Transistor.i_cont),
                       'Metadata': Metadata_dict,
                       'Switch': Switch_dict,
                       'Switch Energy Data': SwitchEnergyData_dict,
                       'Diode': Diode_dict,
                       'Channel Data': ChannelData_dict,
                       'Foster Thermal Model': FosterThermalModel_dict}

    sio.savemat('Transistor_test.mat', {'Transistor_test': Transistor_dict})
