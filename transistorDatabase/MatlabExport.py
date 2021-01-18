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
"""

import scipy.io as sio
# import ZODB
# import ZODB.FileStorage
# import transaction
# from DatabaseClasses import Transistor, Metadata

# # Datenbank erstellen bzw. zu ihr verbinden.
# storage = ZODB.FileStorage.FileStorage('transistorDatabase.fs')
# db = ZODB.DB(storage)
# connection = db.open()
# root = connection.root
# #
# testTransistor = Transistor()
# testTransistor.meta = Metadata()
# root.transistor1 = testTransistor
# transaction.commit()


def exportTransistor(transistorName):

    Transistor = root.transistorName

    Metadata_dict = {'Author': Transistor.Metadata.author,
                     'Template_version': Transistor.Metadata.template_version,
                     'Template_date': Transistor.Metadata.template_date,
                     'Creation_date': Transistor.Metadata.creation_date,
                     'Last_modified': Transistor.Metadata.last_modified,
                     'Comment': Transistor.Metadata.comment, 'Manufacturer': Transistor.Metadata.manufacturer,
                     'Datasheet_hyperlink': Transistor.Metadata.datasheet_hyperlink,
                     'Datasheet_date': Transistor.Metadata.datasheet_date,
                     'Datasheet_version': Transistor.Metadata.datasheet_version,
                     'Housing_area': Transistor.Metadata.housing_area,
                     'Contact_area': Transistor.Metadata.contact_area, 'Housing_type': Transistor.Metadata.housing_type}

    FosterThermalModel_dict = {'R_th_total': Transistor.FosterThermalModel.r_th_total,
                               'R_th_vector': Transistor.FosterThermalModel.r_th_vector,
                               'C_th_total': Transistor.FosterThermalModel.c_th_total,
                               'C_th_vector': Transistor.FosterThermalModel.c_th_vector,
                               'Tau_total': Transistor.FosterThermalModel.tau_total,
                               'Tau_vector': Transistor.FosterThermalModel.tau_vector,
                               'Transient_data': Transistor.FosterThermalModel.transient_data}

    # ??? Transistor.Switch.meta
    Switch_dict = {'Comment': Transistor.Metadata.comment, 'Manufacturer': Transistor.Metadata.manufacturer,
                   'Technology': Transistor.Metadata.technology,
                   'c_oss': Transistor.Switch.c_oss, 'c_iss': Transistor.Switch.c_iss,
                   'c_rss': Transistor.Switch.c_rss, 'meta': Transistor.Switch.meta,
                   'channel': Transistor.Switch.channel, 'e_on': Transistor.Switch.e_on,
                   'e_off': Transistor.Switch.e_off}

    # ??? Transistor.Diode.meta/thermal
    Diode_dict = {'Comment': Transistor.Metadata.comment, 'Manufacturer': Transistor.Metadata.manufacturer,
                  'Technology': Transistor.Metadata.technology, 'thermal': Transistor.Diode.thermal,
                  'channel': Transistor.Diode.channel, 'e_rr': Transistor.Diode.e_rr}

    ChannelData_dict = {'t_j': Transistor.ChannelData.t_j, 'v_i_data': Transistor.ChannelData.v_i_data}

    SwitchEnergyData_dict = {'dataset_type': Transistor.SwitchEnergyData.dataset_type,
                             't_j': Transistor.SwitchEnergyData.t_j,
                             'v_supply': Transistor.SwitchEnergyData.v_supply,
                             'v_g': Transistor.SwitchEnergyData.v_g,
                             'e_x': Transistor.SwitchEnergyData.e_x, 'r_g': Transistor.SwitchEnergyData.r_g,
                             'i_x': Transistor.SwitchEnergyData.i_x, 'i_e_data': Transistor.SwitchEnergyData.i_e_data,
                             'r_e_data': Transistor.SwitchEnergyData.r_e_data}

    Transistor_dict = {'name': Transistor.name, 'type': Transistor.type,
                       'r_th_cs': Transistor.r_th_cs, 'r_th_switch': Transistor.r_th_switch_cs,
                       'r_th_diode_cs': Transistor.r_th_diode_cs, 'v_max': Transistor.v_max,
                       'i_max': Transistor.i_max, 'i_cont': Transistor.i_cont, 'Metadata': Metadata_dict,
                       'Switch': Switch_dict, 'Switch Energy Data': SwitchEnergyData_dict,
                       'Diode': Diode_dict, 'Channel Data': ChannelData_dict,
                       'Foster Thermal Model': FosterThermalModel_dict}

    sio.savemat('Transistor_test.mat', {'Transistor_test': Transistor_dict})
