"""
Initial author: Manuel Klaedtke
Date of creation: 21.12.2020
Last modified by: Manuel Klaedtke
Date of modification: 08.01.2021
Version: 1.0
Compatibility: Python
Other files required: Numpy and ZODB package
Link to file: https://git.uni-paderborn.de/lea-git/lea-git-public/matlab-functions/transistor_database/-/blob/master/transistorDatabase/DatabaseClasses.py
Syntax: Constructor arguments need to be given as valid dictionaries.
See method isvalid_dict for specifications of validity for different types of dictionaries.
ToDo: Add functions that help users specifying these dictionaries in a valid way.

Description:
Classes of the transistor database. Contains properties of the transistor that are specifically grouped within
different objects. This file does not (yet) include methods (ToDo!).

Input parameters: None. Might change with different constructor options and methods.
Output parameters: An object of the respective class. (Also outputs of the respective class methods (ToDo!))
Example: Not yet included (ToDo!)
Known Bugs:
Changelog:
VERSION / DATE / NAME: Comment
1.0.0 / 21.12.2020 / Manuel Klaedtke: Initial Version
1.0.1 / 07.01.2021 / Manuel Klaedtke: Renamed parameters previously called "type" to be more specific.
Changed structure of the ChannelData class.
1.0.2 / 07.01.2021 / Manuel Klaedtke: Nested classes as inner class of Transistor.
Added constructors for all classes. Can handle "proper" creation and missing values now. Added error messages if wrong
parameters were supplied.
1.0.3 / 08.01.2021 / Manuel Klaedtke: Added validity checks for Channel- and SwitchEnergyData arguments.
SwitchEnergyData now has very strict definitions for which dataset_type can be used.
1.0.4 / 18.01.2021 / Manuel Klaedtke: Restructured Metadata class. Renamed attributes and deleted v_max and i_max from
ChannelData class.
1.0.5 / 18.01.2021 / Manuel Klaedtke: Added additional validity checks and errors if mandatory arguments are missing or
not correctly specified. Added new attributes 'i_cont' and 'housing_type'
"""
import persistent
import datetime
import numpy as np
from typing import List


class Transistor(persistent.Persistent):
    """Groups data of all other classes for a single transistor. Methods are specified in such a way that only
    user-interaction with this class is necessary (ToDo!)
    Documentation on how to add or extract a transistor-object to/from the database can be found in (ToDo!)
    """
    name: str  # Name of the transistor. Choose as specific as possible. # Mandatory
    transistor_type: str  # Mandatory
    # These are documented in their respective class definitions
    switch: "Switch"
    diode: "Diode"
    meta: "Metadata"
    # Thermal data. See git for equivalent thermal circuit diagram.
    r_th_cs: [float, int, None]  # Unit: K/W  # Optional
    r_th_switch_cs: [float, int, None]  # Unit: K/W  # Optional
    r_th_diode_cs: [float, int, None]  # Unit: K/W  # Optional
    # Absolute maximum ratings
    v_max: [float, int]  # Unit: V  # Mandatory
    i_max: [float, int]  # Unit: A  # Mandatory
    # Rated operation region
    i_cont: [float, int, None]  # Unit: A  # e.g. Fuji: I_c, Semikron: I_c,nom # ToDo: Is this mandatory?

    def __init__(self, transistor_args, metadata_args, foster_args, switch_args, diode_args):
        if self.isvalid_dict(transistor_args, 'Transistor'):
            self.name = transistor_args.get('name')
            self.transistor_type = transistor_args.get('transistor_type')
            self.r_th_cs = transistor_args.get('r_th_cs')
            self.r_th_switch_cs = transistor_args.get('r_th_switch')
            self.r_th_diode_cs = transistor_args.get('r_th_diode_cs')
            self.v_max = transistor_args.get('v_max')
            self.i_max = transistor_args.get('i_max')
        else:
            raise TypeError("'transistor_args' must be a dictionary containing at least the following"
                            "keys: 'name', 'transistor_type', 'v_max', 'i_max'")
        if self.isvalid_dict(metadata_args, 'Metadata'):
            self.meta = self.Metadata(metadata_args)
        else:
            raise TypeError("'metadata_args' must be a dictionary containing at least the following"
                            "keys: 'author', 'manufacturer', 'housing_area', 'cooling_area', 'housing_type'")
        self.diode = self.Diode(diode_args, foster_args)
        self.switch = self.Switch(switch_args, foster_args)

    @staticmethod
    def isvalid_dict(dataset_dict, dict_type):
        """This method checks input argument dictionaries for their validity. It is checked whether all mandatory keys
        are present, have the right type and permitted values (e.g. 'MOSFET' or 'IGBT' for 'transistor_type')."""
        # ToDo: Add check for mandatory attributes.
        # ToDo: Add structure for Errors. e.g.: xx has wrong type, xx has wrong type, etc.
        if not isinstance(dataset_dict, dict):
            return False
        elif dict_type == 'ChannelData':
            # Determine necessary keys.
            check_keys = {'t_j', 'v_i_data'}
            # Check if all necessary keys are contained in the dict.
            if dataset_dict.keys() >= check_keys:
                return True
            else:
                return False  # ToDo: Should this raise an error or just not create the object? Or raise warning?
                # ToDo: My idea: Just a warning but count how many dictionaries were invalid.
        elif dict_type == 'SwitchEnergyData':
            if dataset_dict.contains('dataset_type'):
                # Determine necessary keys.
                if dataset_dict.get('dataset_type') == 'single':
                    check_keys = {'t_j', 'v_supply', 'v_g', 'e_x', 'r_g', 'i_x'}
                elif dataset_dict.get('dataset_type') == 'graph_r_e':
                    check_keys = {'t_j', 'v_supply', 'v_g', 'r_e_data', 'i_x'}
                elif dataset_dict.get('dataset_type') == 'graph_i_e':
                    check_keys = {'t_j', 'v_supply', 'v_g', 'i_e_data', 'r_g'}
                else:
                    raise ValueError("Wrong dataset_type for creation of SwitchEnergyData object. Must be 'single', "
                                     "'r_e' or 'i_e'. Check SwitchEnergyData class for further information.")
                # Check if all necessary keys are contained in the dict.
                if dataset_dict.keys() >= check_keys:
                    return True
                else:
                    return False  # ToDo: Should this raise an error or just not create the object? Or raise warning?
        elif dict_type == 'Transistor':
            check_keys = {'name', 'transistor_type', 'v_max', 'i_max'}
            if dataset_dict.keys() < check_keys:
                raise KeyError("Dictionary 'transistor_args' does not contain all keys necessary for Transistor object "
                               "creation. Mandatory keys: 'name', 'transistor_type', 'v_max', 'i_max'")
            elif dataset_dict.get('transistor_type') not in ['MOSFET', 'IGBT']:
                raise ValueError("'transistor_type' must be either 'MOSFET' or 'IGBT'")
            else:
                return True
        elif dict_type == 'Metadata':
            check_keys = {'author', 'manufacturer', 'housing_area', 'cooling_area', 'housing_type'}
            if dataset_dict.keys() < check_keys:
                raise KeyError("Dictionary 'metadata_args' does not contain all keys necessary for Metadata object "
                               "creation. Mandatory keys: 'author', 'manufacturer', 'housing_area', 'cooling_area', "
                               "'housing_type'")
            else:
                return True  # ToDo: Add check for 'housing_type' to be from list of specific strings.

    class Metadata:
        """Contains metadata of the transistor/switch/diode. Only used to not bloat the other classes. The attributes
        ending on _date are set automatically each time a relevant change to other attributes is made (ToDo!)"""
        # User-specific data
        author: str  # Mandatory
        comment: [str, None]  # Optional
        # Date and template data. Should not be changed manually.
        # ToDo: Add methods to automatically determine dates and template_version on construction or update.
        template_version: str  # Mandatory/Automatic
        template_date: "datetime.date"  # Mandatory/Automatic
        creation_date: "datetime.date"  # Mandatory/Automatic
        last_modified: "datetime.date"  # Mandatory/Automatic
        # Manufacturer- and part-specific data
        manufacturer: str  # Mandatory
        datasheet_hyperlink: [str, None]  # Make sure this link is valid.  # Optional
        datasheet_date: ["datetime.date", None]  # Should not be changed manually.  # Optional
        datasheet_version: [str, None]  # Optional
        housing_area: float  # Unit: mm^2  # Mandatory
        cooling_area: float  # Unit: mm^2  # Mandatory
        housing_type: str  # e.g. TO-220, etc. # Mandatory. Must be from a list of specific strings.
        # ToDo: Specify list of strings.

        def __init__(self, metadata_args):
            # Validity of metadata_args is checked in the constructor of Transistor class and thus does not need to be
            # checked again here.
            self.author = metadata_args.get('author')
            self.technology = metadata_args.get('meta_type')
            self.template_version = metadata_args.get('template_version')
            self.template_date = metadata_args.get('template_date')
            self.creation_date = metadata_args.get('creation_date')
            self.last_modified = metadata_args.get('ast_modified')
            self.comment = metadata_args.get('comment')
            self.manufacturer = metadata_args.get('manufacturer')
            self.datasheet_hyperlink = metadata_args.get('datasheet_hyperlink')
            self.datasheet_date = metadata_args.get('datasheet_date')
            self.datasheet_version = metadata_args.get('datasheet_version')
            self.housing_area = metadata_args.get('housing_area')
            self.cooling_area = metadata_args.get('cooling_area')

    class FosterThermalModel:
        """Contains data to specify parameters of the Foster thermal model. This model describes the transient
        temperature behavior as a thermal RC-network. The necessary parameters can be estimated by curve-fitting
        transient temperature data supplied in transient_data or by manually specifying the individual 2 out of 3 of the
         parameters R, C, and tau."""
        # ToDo: Add function to estimate parameters from transient data.
        # ToDo: Add function to automatically calculate missing parameters from given ones.
        # Thermal resistances of RC-network (array).
        r_th_vector: ["np.ndarray[np.float64]", None]  # Unit: K/W  # Optional
        # Sum of thermal resistances of n-pole RC-network (scalar).
        r_th_total: ["np.ndarray[np.float64]", None]  # Unit: K/W  # Optional
        # Thermal capacitances of n-pole RC-network (array).
        c_th_vector: ["np.ndarray[np.float64]", None]  # Unit: J/K  # Optional
        # Sum of thermal capacitances of n-pole low pass as (scalar).
        c_th_total: ["np.ndarray[np.float64]", None]  # Unit: J/K  # Optional
        # Thermal time constants of n-pole RC-network (array).
        tau_vector: ["np.ndarray[np.float64]", None]  # Unit: s  # Optional
        # Sum of thermal time constants of n-pole RC-network (scalar).
        tau_total: ["np.ndarray[np.float64]", None]  # Unit: s  # Optional
        # Transient data for extraction of the thermal parameters specified above.
        # Represented as a 2xm Matrix where row 1 is the time and row 2 the temperature.
        transient_data: ["np.ndarray[np.float64]", None]  # Units: Row 1: s; Row 2: K/W  # Optional

        def __init__(self, args):
            if isinstance(args, dict):
                self.r_th_total = args.get('r_th_total')
                self.r_th_vector = args.get('r_th_vector')
                self.c_th_total = args.get('c_th_total')
                self.c_th_vector = args.get('c_th_vector')
                self.tau_total = args.get('tau_total')
                self.tau_vector = args.get('tau_vector')
                self.transient_data = args.get('transient_data')
            elif args is None:
                self.r_th_total = None
                self.r_th_vector = None
                self.c_th_total = None
                self.c_th_vector = None
                self.tau_total = None
                self.tau_vector = None
                self.transient_data = None
            else:
                raise TypeError('The arguments for object creation need to be given as a dictionary or not at all '
                                '(None)')

    class Switch:
        """Contains data associated with the switchting-characteristics of a MOSFET or IGBT. Can contain multiple
        channel-, e_on- and e_off-datasets. """
        # Metadata
        comment: [str, None]  # Optional
        manufacturer: [str, None]  # Optional
        technology: [str, None]  # Semiconductor technology. e.g. IGBT3/IGBT4/IGBT7  # Optional
        # These are documented in their respective class definitions.
        thermal: "FosterThermalModel"  # Transient thermal model.  # Optional
        channel: List["ChannelData"]  # Switch channel voltage and current data.
        e_on: List["SwitchEnergyData"]  # Switch on energy data.
        e_off: List["SwitchEnergyData"]  # Switch of energy data.
        # Constant Capacitances
        c_oss: [float, None]  # Unit: pF  # Optional
        c_iss: [float, None]  # Unit: pF  # Optional
        c_rss: [float, None]  # Unit: pF  # Optional

        def __init__(self, switch_args, foster_args):
            self.thermal = Transistor.FosterThermalModel(foster_args)
            if isinstance(switch_args, dict):
                self.c_oss = switch_args.get('c_oss')
                self.c_iss = switch_args.get('c_iss')
                self.c_rss = switch_args.get('c_rss')
                self.comment = switch_args.get('comment')
                self.manufacturer = switch_args.get('manufacturer')
                self.technology = switch_args.get('technology')
                # This currently accepts dictionaries and lists of dictionaries. Validity is only checked by keys and
                # not their values.
                self.channel = []  # Default case: Empty list
                if isinstance(switch_args.get('channel'), list):
                    # Loop through list and check each dict for validity. Only create ChannelData objects from valid
                    # dicts
                    for dataset in switch_args.get('channel'):
                        if Transistor.isvalid_dict(dataset, 'ChannelData'):
                            self.channel.append(Transistor.ChannelData(dataset))
                elif Transistor.isvalid_dict(switch_args.get('channel'), 'ChannelData'):
                    # Only create ChannelData objects from valid dicts
                    self.channel.append(Transistor.ChannelData(switch_args.get('channel')))

                self.e_on = []  # Default case: Empty list
                if isinstance(switch_args.get('e_on'), list):
                    # Loop through list and check each dict for validity. Only create SwitchEnergyData objects from
                    # valid dicts
                    for dataset in switch_args.get('e_on'):
                        if Transistor.isvalid_dict(dataset, 'SwitchEnergyData'):
                            self.e_on.append(Transistor.SwitchEnergyData(dataset))
                elif Transistor.isvalid_dict(switch_args.get('e_on'), 'SwitchEnergyData'):
                    # Only create SwitchEnergyData objects from valid dicts
                    self.e_on.append(Transistor.SwitchEnergyData(switch_args.get('e_on')))

                self.e_off = []  # Default case: Empty list
                if isinstance(switch_args.get('e_off'), list):
                    for dataset in switch_args.get('e_off'):
                        if Transistor.isvalid_dict(dataset, 'SwitchEnergyData'):
                            self.e_off.append(Transistor.SwitchEnergyData(dataset))
                elif Transistor.isvalid_dict(switch_args.get('e_off'), 'SwitchEnergyData'):
                    self.e_off.append(Transistor.SwitchEnergyData(switch_args.get('e_off')))

            elif switch_args is None:
                self.c_oss = None
                self.c_iss = None
                self.c_rss = None
                self.comment = None
                self.manufacturer = None
                self.technology = None
                self.channel = []
                self.e_on = []
                self.e_off = []
            else:
                raise TypeError('The arguments for object creation need to be given as a dictionary or not at all '
                                '(None)')

    class Diode:
        """Contains data associated with the (reverse) diode-characteristics of a MOSFET or IGBT. Can contain multiple
        channel- and e_rr- datasets."""
        # Metadata
        comment: [str, None]  # Optional
        manufacturer: [str, None]  # Optional
        technology: [str, None]  # Semiconductor technology. e.g. IGBT3/IGBT4/IGBT7  # Optional
        # These are documented in their respective class definitions.
        thermal: ["FosterThermalModel", None]  # Transient thermal model.
        channel: List["ChannelData"]  # Diode forward voltage and forward current data.
        e_rr: List["SwitchEnergyData"]  # Reverse recovery energy data.

        def __init__(self, diode_args, foster_args):
            self.thermal = Transistor.FosterThermalModel(foster_args)
            if isinstance(diode_args, dict):
                self.comment = diode_args.get('comment')
                self.manufacturer = diode_args.get('manufacturer')
                self.technology = diode_args.get('technology')
                # This currently accepts dictionaries and lists of dictionaries. Validity is only checked by keys and
                # not their values.
                self.channel = []  # Default case: Empty list
                if isinstance(diode_args.get('channel'), list):
                    # Loop through list and check each dict for validity. Only create ChannelData objects from valid
                    # dicts
                    for dataset in diode_args.get('channel'):
                        if Transistor.isvalid_dict(dataset, 'ChannelData'):
                            self.channel.append(Transistor.ChannelData(dataset))
                elif Transistor.isvalid_dict(diode_args.get('channel'), 'ChannelData'):
                    # Only create ChannelData objects from valid dicts
                    self.channel.append(Transistor.ChannelData(diode_args.get('channel')))

                self.e_rr = []  # Default case: Empty list
                if isinstance(diode_args.get('e_rr'), list):
                    # Loop through list and check each dict for validity. Only create SwitchEnergyData objects from
                    # valid dicts
                    for dataset in diode_args.get('e_rr'):
                        if Transistor.isvalid_dict(dataset, 'SwitchEnergyData'):
                            self.e_rr.append(Transistor.SwitchEnergyData(dataset))
                elif Transistor.isvalid_dict(diode_args.get('e_rr'), 'SwitchEnergyData'):
                    # Only create SwitchEnergyData objects from valid dicts
                    self.e_rr.append(Transistor.SwitchEnergyData(diode_args.get('e_rr')))

            elif diode_args is None:
                self.comment = None
                self.manufacturer = None
                self.technology = None
                self.channel = []
                self.e_rr = []
            else:
                raise TypeError('The arguments for Diode-object creation need to be given as a dictionary or not at all'
                                ' (None)')

    class ChannelData:
        """Contains channel V-I data for either switch or diode. Data is given for only one junction temperature t_j.
        For different temperatures: Create additional ChannelData-objects and store them as a list in the respective
        Diode- or Switch-object.
        This data can be used to linearize the transistor at a specific operating point (ToDo!)"""

        # # Test condition: Must be given as scalar. Create additional objects for different temperatures.
        t_j: float  # Mandatory
        # Dataset: Represented as a 2xm Matrix where row 1 is the voltage and row 2 the current.
        v_i_data: "np.ndarray[np.float64]"  # Units: Row 1: V; Row 2: A  # Mandatory

        def __init__(self, args):
            if isinstance(args, dict):
                self.t_j = args.get('t_j')
                self.v_i_data = args.get('v_i_data')

            else:
                raise TypeError('The arguments for ChannelData-object creation need to be given as a dictionary.')

    class SwitchEnergyData:
        """Contains switching energy data for either switch or diode. The type of Energy (E_on, E_off or E_rr) is
        already implicitly specified by how the respective objects of this class are used in a Diode- or Switch-object.
        For each set (e.g. every curve in the datasheet) of switching energy data a separate object should be created.
        This also includes the reference values in a datasheet given without a graph. (Those are considered as data sets
        with just a single data point.)
        Data sets with more than one point are given as i_e_data with an r_g parameter or as r_e_data with an i_x
        parameter.
        Unused parameters or datasets should be left empty.
        Which of these cases (single point, E vs I dataset, E vs R dataset) is valid for the current object also needs
        to be specified by the dataset_type-property."""

        # Type of the dataset:
        # single: e_x, r_g, i_x are scalars. Given e.g. by a table in the datasheet.
        # graph_r_e: r_e is a 2-dim numpy array with two rows. i_x is a scalar. Given e.g. by an E vs R graph.
        # graph_i_e: i_e is a 2-dim numpy array with two rows. r_g is a scalar. Given e.g. by an E vs I graph.
        dataset_type: str  # Mandatory
        # Test conditions. These must be given as scalars. Create additional objects for e.g. different temperatures.
        t_j: float  # Unit: °C  # Mandatory
        v_supply: float  # Unit: V  # Mandatory
        v_g: float  # Unit: V  # Mandatory
        # Scalar dataset-parameters. Some of these can be 'None' depending on the dataset_type.
        e_x: [float, None]  # Unit: mJ
        r_g: [float, None]  # Unit: Ohm
        i_x: [float, None]  # Unit: A
        # Dataset. Only one of these is allowed. The other should be 'None'.
        i_e_data: ["np.ndarray[np.float64]", None]  # Units: Row 1: A; Row 2: mJ
        r_e_data: ["np.ndarray[np.float64]", None]  # Units: Row 1: Ohm; Row 2: mJ
        # ToDo: Add MOSFET capacitance. Discuss with Philipp.
        # ToDo: Add additional class for linearized switching loss model with capacitances. (See infineon application
        #  note.)
        # ToDo: Option 1: Look up table like it's currently implemented.
        # ToDo: Option 2: https://application-notes.digchip.com/070/70-41484.pdf
        # ToDO: Option 3: K_i, K_v, G_i. Add as empty class with pass.

        def __init__(self, args):
            # Validity of args is checked in the constructor of Diode/Switch class and thus does not need to be
            # checked again here.
            # ToDo: Always check dataset_type and determine which arguments should be ignored.
            self.dataset_type = args.get('dataset_type')
            self.v_supply = args.get('v_supply')
            self.v_g = args.get('v_switch')
            self.t_j = args.get('t_j')
            self.e_x = args.get('e_x')
            self.r_g = args.get('r_g')
            self.i_x = args.get('i_x')
            self.i_e_data = args.get('i_e_data')
            self.r_e_data = args.get('r_e_data')

