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
1.4.1 / 1.6.2021 / Nikolas Förster: remove export_simulink_v1 and replace by export_simulink_loss_model
"""

import scipy.io as sio
import numpy as np
import os
import matlab
import datetime

def compatibilityTest(Transistor, attribute):
    """
    checks attribute for occurrences of None an replace it with np.nan
    :param Transistor: transistor object
    :param attribute: path to given attribute
    :return: attribute value or np.nan
    """
    try:
        att = eval(attribute)
        if att is None:
            return np.nan
        else:
            return att

    except AttributeError:
        return np.nan


def findChannelData(Transistor, channel, temperature, attribute, identifier):
    """
    finds attributes in the ChannelData class instance
    Input: transistor object, path to given ChannelData instance,
           temperature t_j, additional path, Key (e.g. E_on/E_off/E_rr)
    :param Transistor: transistor object
    :param channel: path to given ChannelDatainstance
    :param temperature: junction temperature
    :param attribute:
    :param identifier:
    :return: SwitchEnergy dataset at given temperature point
    """

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


def findSwitchEnergyData(Transistor, switchEnergyInstance, temperature, attribute, identifier):
    """
    finds attributes in the SwitchEnergyData class instance
    # TODO Modify identifier when implemented in databaseClasses.py
    # TODO Modify which DataSet is used when identifiers are implemented
    :param Transistor: transistor object
    :param switchEnergyInstance: path to given switchEnergyData instance
    :param temperature: temperature t_j
    :param attribute: additional path
    :param identifier: Key (e.g. E_on/E_off/E_rr)
    :return: SwitchEnergy dataset at given temperature point
    """

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



def buildList(Transistor, attribute):
    """
    Gather list data (e.g. channel/e_on/e_off/e_rr) and check for 'None'
    :param Transistor: transistor object
    :param attribute: attribute path to list
    :return: matlab compatible list of all attributes
    """

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

def export_simulink_loss_model(transistor):
    """
    Exports a simulation model for simulink inverter loss models, see https://de.mathworks.com/help/physmod/sps/ug/loss-calculation-in-a-three-phase-3-level-inverter.html
    #ToDo: C_th is fixed at the moment to 1e-6 for switch an diode. Needs to be calculated from ohter data
    Notes:
     - temperature next to 25 and 150 degree at 15V gate voltage will be used for channel and switching loss
     - in case of just one temperature curve, the upper temperature will increased (+1K) to bring a small temperature change in the curves. Otherwise the model will not work
     - only necessary data from tdb will be exported to simulink
     - Simulink model need switching energy loss in 'mJ'
     - in case of no complete curve (e.g. not starting from zero), this tool will interpolate the curve
    :param transistor: transistor object
    :return: .mat file for import in matlab/simulink
    """
    # Notes on exporting the file:
    # values need to be exported as np.double(), otherwise the Simulink-model can not interpolate the data (but displaying the curves is working...)


    t_j_lower = 25
    t_j_upper = 150
    v_g = 15

    ### switch
    switch_channel_object_lower, eon_object_lower, eoff_object_lower = transistor.switch.find_approx_wp(t_j_lower, v_g, normalize_t_to_v=10, SwitchEnergyData_dataset_type="graph_i_e")
    switch_channel_object_upper, eon_object_upper, eoff_object_upper = transistor.switch.find_approx_wp(t_j_upper, v_g, normalize_t_to_v=10, SwitchEnergyData_dataset_type="graph_i_e")

    # all elements need the same current vector size
    i_interp = np.linspace(0, transistor.i_abs_max, 10)

    switch_channel_lower_interp = np.interp(i_interp, switch_channel_object_lower.graph_v_i[1], switch_channel_object_lower.graph_v_i[0])
    switch_channel_upper_interp = np.interp(i_interp, switch_channel_object_upper.graph_v_i[1], switch_channel_object_upper.graph_v_i[0])
    switch_channel_array = np.array([switch_channel_lower_interp, switch_channel_upper_interp])

    e_on_lower_interp = np.interp(i_interp, eon_object_lower.graph_i_e[0], eon_object_lower.graph_i_e[1])
    e_on_upper_interp = np.interp(i_interp, eon_object_upper.graph_i_e[0], eon_object_upper.graph_i_e[1])
    e_on_array = np.array([e_on_lower_interp, e_on_upper_interp])

    e_off_lower_interp = np.interp(i_interp, eoff_object_lower.graph_i_e[0], eoff_object_lower.graph_i_e[1])
    e_off_upper_interp = np.interp(i_interp, eoff_object_upper.graph_i_e[0], eoff_object_upper.graph_i_e[1])
    e_off_array = np.array([e_off_lower_interp, e_off_upper_interp])

    # Simulink-power-electronic loss model can not handle curves in case of the temperatures are the same
    temp_t_j_switch_channel_upper = switch_channel_object_upper.t_j + 1 if switch_channel_object_lower.t_j == switch_channel_object_upper.t_j else switch_channel_object_upper.t_j
    temp_t_j_eon_upper = eon_object_upper.t_j + 1 if eon_object_lower.t_j == eon_object_upper.t_j else eon_object_upper.t_j
    temp_t_j_eoff_upper = eoff_object_upper.t_j + 1 if eoff_object_lower.t_j == eoff_object_upper.t_j else eoff_object_upper.t_j

    switch_dict = {'T_j_channel': np.double([switch_channel_object_lower.t_j, temp_t_j_switch_channel_upper]),
                   'T_j_ref_on': np.double([eon_object_lower.t_j, temp_t_j_eon_upper]),
                   'T_j_ref_off': np.double([eoff_object_lower.t_j, temp_t_j_eoff_upper]),
                   'R_th_total': compatibilityTest(transistor, 'Transistor.switch.thermal_foster.r_th_total') if transistor.switch.thermal_foster.r_th_total != 0 else 1e-6,
                   'C_th_total': np.double(1e-6),
                   'V_ref_on': np.double(eon_object_upper.v_supply),
                   'V_ref_off': np.double(eon_object_upper.v_supply),
                   'Eon': np.double(e_on_array * 1000),
                   'Eoff': np.double(e_off_array * 1000),
                   'v_channel': np.double(switch_channel_array),
                   'i_vec': np.double(i_interp),
                   }
    ### diode
    diode_channel_object_lower, err_object_lower = transistor.diode.find_approx_wp(t_j_lower, v_g)
    diode_channel_object_upper, err_object_upper = transistor.diode.find_approx_wp(t_j_upper, v_g)
    diode_channel_lower_interp = np.interp(i_interp, diode_channel_object_lower.graph_v_i[1], diode_channel_object_lower.graph_v_i[0])
    diode_channel_upper_interp = np.interp(i_interp, diode_channel_object_upper.graph_v_i[1], diode_channel_object_upper.graph_v_i[0])
    diode_channel_array = np.array([diode_channel_lower_interp, diode_channel_upper_interp])

    e_rr_lower_interp = np.interp(i_interp, err_object_lower.graph_i_e[0], err_object_lower.graph_i_e[1])
    e_rr_upper_interp = np.interp(i_interp, err_object_upper.graph_i_e[0], err_object_upper.graph_i_e[1])
    err_array = np.array([e_rr_lower_interp, e_rr_upper_interp])

    # Simulink-power-electronic loss model can not handle curves in case of the temperatures are the same
    temp_t_j_switch_channel_upper = diode_channel_object_upper.t_j + 1 if diode_channel_object_lower.t_j == diode_channel_object_upper.t_j else diode_channel_object_upper.t_j
    temp_t_j_err_upper = err_object_upper.t_j + 1 if err_object_lower.t_j == err_object_upper.t_j else err_object_upper.t_j

    diode_dict = {
        'T_j_channel': np.double([diode_channel_object_lower.t_j, temp_t_j_switch_channel_upper]),
        'T_j_ref_rr': np.double([err_object_lower.t_j, temp_t_j_err_upper]),
        'R_th_total': compatibilityTest(transistor, 'Transistor.diode.thermal_foster.r_th_total') if transistor.diode.thermal_foster.r_th_total != 0 else 1e-6,
        'C_th_total': np.double(1e-6),
        'V_ref_rr': np.double(err_object_lower.v_supply),
        'v_channel': np.double(diode_channel_array),
        'i_vec': np.double(i_interp),
        'Err': np.double(err_array * 1000)

    }

    transistor_dict = {'Name': compatibilityTest(transistor, 'Transistor.name'),
                       'R_th_CS': compatibilityTest(transistor, 'Transistor.r_th_cs')  if transistor.r_th_cs != 0 else 1e-6,
                       'R_th_Switch_CS': compatibilityTest(transistor, 'Transistor.r_th_switch_cs') if transistor.r_th_switch_cs != 0 else 1e-6,
                       'R_th_Diode_CS': compatibilityTest(transistor, 'Transistor.r_th_diode_cs') if transistor.r_th_diode_cs != 0 else 1e-6,
                       'Switch': switch_dict,
                       'Diode': diode_dict,
                       'file_generated': f"{datetime.datetime.today()}",
                       'file_generated_by': "https://github.com/upb-lea/transistordatabase",
                       }

    sio.savemat(transistor.name + '_Simulink_lossmodel.mat', {transistor.name: transistor_dict})
    print(f"Export files {transistor.name}_Simulink_lossmodel.mat to {os.getcwd()}")


def export_matlab_v1(transistorName):
    """
    Creates .mat file with raw transistor data
    :param transistorName: transistor object
    :return: creates a separate .mat file
    """
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


def export_geckocircuits(Transistor, v_supply, v_g_on, v_g_off, r_g_on, r_g_off):
    """
    Export transistor data to GeckoCIRCUITS

    :param Transistor: choose the transistor to export
    :param v_supply: supply voltage for turn-on/off losses
    :param v_g_on: gate turn-on voltage
    :param v_g_off: gate turn-off voltage
    :param r_g_on: gate resistor for turn-on
    :param r_g_off: gate resistor for turn-off
    :return: two output files: 'Transistor.name'_Switch.scl and 'Transistor.name'_Diode.scl for geckoCIRCUITS import
    """

    # programming notes
    # exporting the diode:
    # diode off losses:
    # diode on losses: these on losses must be generated, even if they are zero
    # diode channel: it is not allowed to use more than one current that is zero (otherwise geckocircuits can not calculate the losses)

    amount_v_g_switch_cond = 0
    amount_v_g_switch_sw = 0
    amount_v_g_diode_cond  = 0
    amount_v_g_diode_sw = 0

    # set numpy print options to inf, due to geckocircuits requests the data in one single line
    np.set_printoptions(linewidth=np.inf)

    ########################
    # export file for switch
    ########################
    file_switch = open(Transistor.name + "_Switch.scl","w")

    #### switch channel data
    # count number of arrays with gate v_g == v_g_export
    for n_channel in np.array(range(0, len(Transistor.switch.channel))):
        if Transistor.switch.channel[n_channel].v_g == v_g_on:
            amount_v_g_switch_cond +=1

    file_switch.write("anzMesskurvenPvCOND " + str(amount_v_g_switch_cond) + "\n")
    for n_channel in np.array(range(0, len(Transistor.switch.channel))):
        if Transistor.switch.channel[n_channel].v_g == v_g_on:

            voltage = Transistor.switch.channel[n_channel].graph_v_i[0]
            current = Transistor.switch.channel[n_channel].graph_v_i[1]

            # gecko can not work in case of to currents are zero
            # so find the second current that is zero and replace it by a very small current
            for i in range(len(current)):
                if i > 0 and current[i] == 0:
                    current[i] = 0.001
            if Transistor.type.lower() == 'mosfet' or Transistor.type.lower() == 'sic-mosfet':
                # Note: Loss calculation in GeckoCIRCUITs will fail in case of reverse conducting
                # Forward characteristic will be copied to backward-characteristic
                voltage_reverse = voltage.copy()
                voltage_reverse = voltage_reverse[voltage_reverse != 0]
                voltage_reverse = np.flip(voltage_reverse)
                voltage_reverse = [-x for x in voltage_reverse]
                voltage = np.append(voltage_reverse, voltage)

                current_reverse = current.copy()
                current_reverse = current_reverse[current_reverse != 0]
                current_reverse = np.flip(current_reverse)
                current_reverse = [-x for x in current_reverse]
                current = np.append(current_reverse, current)

            print_current = np.array2string(current, formatter={'float_kind':lambda x: "%.3f" % x})
            print_current = print_current[1:-1]
            print_voltage = np.array2string(voltage, formatter={'float_kind':lambda x: "%.3f" % x})
            print_voltage = print_voltage[1:-1]

            # for every loss curve, write
            file_switch.write("<LeitverlusteMesskurve>\n")
            file_switch.write(f"data[][] 2 {len(current)} {print_voltage} {print_current}")
            file_switch.write(f"\ntj {Transistor.switch.channel[n_channel].t_j}\n")
            file_switch.write("<\LeitverlusteMesskurve>\n")

    #### switch switching loss
    # check for availability of switching loss curves
    # count number of arrays with gate v_g == v_g_export
    for n_on in np.array(range(0, len(Transistor.switch.e_on))):
        if Transistor.switch.e_on[n_on].v_g == v_g_on and Transistor.switch.e_on[n_on].r_g == r_g_on and\
            Transistor.switch.e_on[n_on].v_supply == v_supply:
            amount_v_g_switch_sw +=1

    file_switch.write(f"anzMesskurvenPvSWITCH {amount_v_g_switch_sw}\n")

    for n_on in np.array(range(0, len(Transistor.switch.e_on))):
        if Transistor.switch.e_on[n_on].v_g == v_g_on and Transistor.switch.e_on[n_on].r_g == r_g_on and\
            Transistor.switch.e_on[n_on].v_supply == v_supply:

            on_current = Transistor.switch.e_on[n_on].graph_i_e[0]
            on_energy = Transistor.switch.e_on[n_on].graph_i_e[1]

            # search for off loss curves
            for n_off in np.array(range(0, len(Transistor.switch.e_off))):
                if Transistor.switch.e_off[n_off].v_g == v_g_off and Transistor.switch.e_off[n_off].r_g == r_g_off and \
                        Transistor.switch.e_off[n_off].v_supply == v_supply:
                    # set off current and off energy
                    off_current = Transistor.switch.e_off[n_off].graph_i_e[0]
                    off_energy = Transistor.switch.e_off[n_off].graph_i_e[1]

            interp_current = np.linspace(0, on_current[-1], 10)
            interp_on_energy = np.interp(interp_current, on_current, on_energy)
            interp_off_energy = np.interp(interp_current, off_current, off_energy)

            print_current = np.array2string(interp_current, formatter={'float_kind':lambda x: "%.2f" % x})
            print_current = print_current[1:-1]
            print_on_energy = np.array2string(interp_on_energy, formatter={'float_kind':lambda x: "%.8f" % x})
            print_on_energy = print_on_energy[1:-1]

            print_off_energy = np.array2string(interp_off_energy, formatter={'float_kind':lambda x: "%.8f" % x})
            print_off_energy = print_off_energy[1:-1]

            # for every loss curve, write
            file_switch.write("<SchaltverlusteMesskurve>\n")
            file_switch.write(f"data[][] 3 {len(interp_current)} {print_current} {print_on_energy} {print_off_energy}")
            file_switch.write(f"\ntj {Transistor.switch.e_on[n_on].t_j}\n")
            file_switch.write(f"uBlock {Transistor.switch.e_on[n_on].v_supply}\n")
            file_switch.write("<\SchaltverlusteMesskurve>\n")

    file_switch.close()

    ########################
    # export file for diode
    ########################

    file_diode = open(Transistor.name + "_Diode.scl","w")
    #### diode channel data
    # count number of arrays for conducting behaviour
    # in case of gan-transistor, search for v_g_off
    # in case of mosfet or igbt use all available data
    for n_channel in np.array(range(0, len(Transistor.diode.channel))):
        if (Transistor.diode.channel[n_channel].v_g == v_g_off and Transistor.type.lower() == 'gan-transistor') or Transistor.type == 'MOSFET' or Transistor.type == 'IGBT':
            amount_v_g_diode_cond +=1

    file_diode.write("anzMesskurvenPvCOND " + str(amount_v_g_diode_cond) + "\n")
    # export conducting behaviour
    for n_channel in np.array(range(0, len(Transistor.diode.channel))):
        # if v_g_diode is given, search for it. Else, use all data in Transistor.diode.channel
        # in case of gan-transistor, search for v_g_off
        # in case of mosfet or igbt use all available data
        if (Transistor.diode.channel[n_channel].v_g == v_g_off and Transistor.type.lower() == 'gan-transistor') or Transistor.type == 'MOSFET' or Transistor.type == 'IGBT':

            voltage = np.abs(Transistor.diode.channel[n_channel].graph_v_i[0])
            current = np.abs(Transistor.diode.channel[n_channel].graph_v_i[1])

            # gecko can not work in case of to currents are zero
            # so find the second current that is zero and replace it by a very small current
            for i in range(len(current)):
                if i > 0 and current[i] == 0:
                    current[i] = 0.001

            print_current = np.array2string(current, formatter={'float_kind':lambda x: "%.3f" % x})
            print_current = print_current[1:-1]
            print_voltage = np.array2string(voltage, formatter={'float_kind':lambda x: "%.3f" % x})
            print_voltage = print_voltage[1:-1]

            # for every loss curve, write
            file_diode.write("<LeitverlusteMesskurve>\n")
            file_diode.write(f"data[][] 2 {len(current)} {print_voltage} {print_current}")
            file_diode.write(f"\ntj {Transistor.diode.channel[n_channel].t_j}\n")
            file_diode.write("<\LeitverlusteMesskurve>\n")

    #### diode err loss
    # check for availability of switching loss curves
    # in case of no switching losses available, set curves to zero.
    # if switching losses will not set to zero, geckoCIRCUITS will use inital values
    if len(Transistor.diode.e_rr) == 0:
        file_diode.write(f"anzMesskurvenPvSWITCH 1\n")
        file_diode.write("<SchaltverlusteMesskurve>\n")
        file_diode.write(f"data[][] 3 2 0 10 0 0 0 0")
        file_diode.write(f"\ntj 125\n")
        file_diode.write(f"uBlock 400\n")
        file_diode.write("<\SchaltverlusteMesskurve>\n")

    # in case of available data
    #
    else:
        # check for curves with the gate voltage
        # count number of arrays with gate v_g == v_g_export
        for n_rr in np.array(range(0, len(Transistor.diode.e_rr))):
            if Transistor.diode.e_rr[n_rr].v_g == v_g_on and Transistor.diode.e_rr[n_rr].r_g == r_g_on and\
                Transistor.diode.e_rr[n_rr].v_supply == v_supply:
                amount_v_g_diode_sw +=1

        # in case of no given v_g for diode (e.g. for igbts)
        if amount_v_g_diode_sw == 0:
            for n_rr in np.array(range(0, len(Transistor.diode.e_rr))):
                if len(Transistor.diode.e_rr[n_rr].v_g) == 0 and Transistor.diode.e_rr[n_rr].r_g == r_g_on and \
                        Transistor.diode.e_rr[n_rr].v_supply == v_supply:
                    amount_v_g_diode_sw += 1

            file_diode.write(f"anzMesskurvenPvSWITCH {amount_v_g_diode_sw}\n")

            for n_rr in np.array(range(0, len(Transistor.diode.e_rr))):
                if len(Transistor.diode.e_rr[n_rr].v_g) == 0 and Transistor.diode.e_rr[n_rr].r_g == r_g_on and \
                        Transistor.diode.e_rr[n_rr].v_supply == v_supply:
                    rr_current = Transistor.diode.e_rr[n_rr].graph_i_e[0]
                    rr_energy = Transistor.diode.e_rr[n_rr].graph_i_e[1]

                    # forward recovery losses set to zero
                    fr_energy = np.zeros(len(rr_current))

                    print_fr_energy = np.array2string(fr_energy, formatter={'float_kind': lambda x: "%.8f" % x})
                    print_fr_energy = print_fr_energy[1:-1]

                    print_current = np.array2string(rr_current, formatter={'float_kind': lambda x: "%.2f" % x})
                    print_current = print_current[1:-1]
                    print_rr_energy = np.array2string(rr_energy, formatter={'float_kind': lambda x: "%.8f" % x})
                    print_rr_energy = print_rr_energy[1:-1]

                    # for every loss curve, write
                    file_diode.write("<SchaltverlusteMesskurve>\n")
                    file_diode.write(f"data[][] 3 {len(rr_current)} {print_current} {print_fr_energy} {print_rr_energy}")
                    file_diode.write(f"\ntj {Transistor.diode.e_rr[n_rr].t_j}\n")
                    file_diode.write(f"uBlock {Transistor.diode.e_rr[n_rr].v_supply}\n")
                    file_diode.write("<\SchaltverlusteMesskurve>\n")

        # in case of devices wich include a gate voltage (e.g. GaN-transistors)
        else:

            file_diode.write(f"anzMesskurvenPvSWITCH {amount_v_g_diode_sw}\n")

            for n_rr in np.array(range(0, len(Transistor.diode.e_rr))):
                if Transistor.diode.e_rr[n_rr].v_g == v_g_on and Transistor.diode.e_rr[n_rr].r_g == r_g_on and\
                    Transistor.diode.e_rr[n_rr].v_supply == v_supply:

                    rr_current = Transistor.diode.e_rr[n_rr].graph_i_e[0]
                    rr_energy = Transistor.diode.e_rr[n_rr].graph_i_e[1]
                    # forward recovery losses set to zero
                    fr_energy = np.zeros(len(rr_current))
                    print_fr_energy = np.array2string(fr_energy, formatter={'float_kind': lambda x: "%.8f" % x})
                    print_fr_energy = print_fr_energy[1:-1]
                    print_current = np.array2string(rr_current, formatter={'float_kind':lambda x: "%.2f" % x})
                    print_current = print_current[1:-1]
                    print_rr_energy = np.array2string(rr_energy, formatter={'float_kind':lambda x: "%.8f" % x})
                    print_rr_energy = print_rr_energy[1:-1]

                    # for every loss curve, write
                    file_diode.write("<SchaltverlusteMesskurve>\n")
                    file_diode.write(f"data[][] 3 {len(rr_current)} {print_current} {print_fr_energy} {print_rr_energy}")
                    file_diode.write(f"\ntj {Transistor.diode.e_rr[n_rr].t_j}\n")
                    file_diode.write(f"uBlock {Transistor.diode.e_rr[n_rr].v_supply}\n")
                    file_diode.write("<\SchaltverlusteMesskurve>\n")

    file_diode.close()
    print(f"Export files {Transistor.name}_Switch.scl and {Transistor.name}_Diode.scl to {os.getcwd()}")
    #set print options back to default
    np.set_printoptions(linewidth=75)