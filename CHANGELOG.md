# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased] - Date
### Updated
- Add marging for non-linear capacitance file export for GeckoCIRCUITS


## [0.5.1] - 2024-06-22
### Fixed
- Documentation pipeline issue

## [0.5.0] - 2024-06-22
### Added
- Non-linear capacitance file export for GeckoCIRCUITS
- Introduction of database manager. See the template_example.py for API changes.
### Fixed
- Fix some GUI data does not accept float or negative values
- Fix reading GUI graph_r_e curves 
### Changed
- API has changed according to the introduction of the database manager. See the template_example.py for API changes. 

## [0.4.1] - 2022-07-18
### Added
- General: Option to delete transistors from local database
- General: Gecko Exporter for GaN-Transistors: mirror 1. quadrant forward characteristic to 3rd quadrant
- GUI: Add options to display virtual and original datasheet for selected transistor
- #90: Add email-workflow to add new transistor to the transistordatabase file exchange (TDB-FE)
- Add log(x), log(y) for adding/viewing plots

### Fixed
- Fix PDF preview not working due to a workaround
- #93: GUI Manufacturer parameters for switch and diode must be optional
- Fix GUI measurement integration method when integrating own measurement.
- Fix some GUI data does not accept float or negative values
- Fix some wrong labels: Units in C-curves

## [0.4.0] - 2022-06-20
### Added
- NEW: Graphical User Interface: Download exe-file, - or run the file "gui.py" within the directory ".../transistordatabase/transistordatabase/gui" to start the GUI

### Fixed
- #82: update_from_fileexchange() leads to failure in case of no internet connection
- #84: Process is still running when closing main window
- #85: Ignore missing-data messages at GUI startup
- #87: Database not visible in exe-file
       
## [0.3.3] - 2022-03-20
### Changed
- do not re-assign r_th and c_th values when loading/creating a transistor object (do not run calc_thermal_params())
- Workaround for brocken export_datasheet(): temporary only html-files available instead of pdf-files

## [0.3.2] - 2022-02-02
### Added
- Add Rohm to manufacturer list
### Changes
- Method 'print_TDB()' changes to 'print_tdb()'
- export_dataheet() can handle with measurement data

## [0.3.1] - 2021-12-15
### Bugfixes
- #68: Improved user warning in case of no mongodb installed
- #70: Save .json-files in multiple lines, to avoid that a small change is very difficult to see in version control
- #71, #72: fix get_object_i/r_e_simplified

## [0.3.0] - 2021-12-09
### Added
- NEW: Option to add own measurements to the database
- Add function export_all_datasheets()
- #61: Add Keys to add R_DS,ON vs. junction temperature
- #62: Add Keys for Gate Charge Curve
- #63: Add Keys for Safe-Operating-Area

### Updated
- #59: simplify the usage of tdb.load('transistorname') instead of tdb.load({'name': 'transistorname'})

### Bugfixes
- #51: Mutable List in export_plecs
- #58: Fix some units displayed in virtual datasheet
- #66: Cannot get the corresponding datasheet according to the procedures in the tutorial
- #67: Problem when exporting all transistors from the database to virtual datasheet


## [0.2.14] - 2021-11-02
### Added
- Helper function 'collect_i_e_and_r_e_combination' to find and associate i_e and r_e based SwitchEnergyData objects for usage in gecko exporter
- Helper function 'check_keys' to validate the arguments provided to gecko exporter 
- constants.py: dictates the default gate voltages for switch and diodes types based on the module type
- #50: Introduce new transitsor keys: r_g_on_recommended and r_g_off_recommended

### Updated
- Docstrings
- updated calc_thermal_params function to normalize the limit selections for curve fitting
- update to module manufacturers list and housing type list
- #27: Update gecko exporter according to latest working
- remodelled gecko exporter with added feature to find the nearest neighbours to the given v_supply, v_g, r_g if the exact curves doestn't exists
- remodelled gecko exporter with added feature to re-estimate the loss curves at given gate resistor
- Added case to handle gecko exporter request to find nearest neighbours in find_next_gate_voltage method
- update find_next_gate_voltage method to include the check_specific_curves parameter which now skips the curves while finding out nearest neighbours

### Bugfixes
- fix #48: export_datasheet fails when exporting a SiC-MOSFET
- fix #49: Print housing_list and manufacturer_list in case of not maching housings/manufacturers when creating a transistor

## [0.2.13] - 2021-09-30
### Added
- #37: Function to calculate thermal parameters from given thermal curve
- scipy curve fitting method is utilized to extract thermal parameters

### Updated
- Docstrings
- added calc_thermal_params function call to init block of transistor object to calculate the missing thermal parameters

### Bugfixes
- #19: Problems in Windows when removing cloned repo

## [0.2.12] - 2021-09-15
### Added
- Transistor method 'compare_channel_linearized()' to compare channel data with linearized data 
- Sphinx documentation, see [here](https://upb-lea.github.io/transistordatabase/transistordatabase.html)

### Updated
- Docstrings

### Bugfixes
- #44: Choose another linearisation default current for quickstart_wp()
- #48: Crash when exporting virtual datasheet

## [0.2.11] - 2021-08-07
### Added
- #40 Read two curves for parasitic capacitance

### Small Improvements
- #35 Add Datasheet Hyperlink to Simulink loss model exporter
- #34, #36 Display all exported file folders clickable
- Datasheet link (.export_datasheet()) is also clickable and opens the browser to display the datasheet
- #38 Update template with new examples
- Small changes on datasheet displaying

### Bugfixes
- fix #43: Problem when paralleling transistors with no r-th-curve given
- fix #39: Problem when exporting datasheet with not r_th_vector and tau_vector variables


## [0.2.10] - 2021-07-27
### Added
- #14 Virtual datasheet for IGBT and MOSFET types which collects all the plot and data of transistor switch and diode and presents a HTMl file. Use 'transistor.export_datasheet()'
### Bugfixes
- fix #32: incorrect template paths in PLECS exporter

## [0.2.9] - 2021-07-14
### Bugfixes
- fix #30: Bad package dependency in setup.py

## [0.2.8] - 2021-07-14
### Added 
- #25 Allows only positive channel data to be stored or created for both switch and diode types, added mirror_xy_data attribute in csv2array function to do so. 
- #28 Integrated calculating curve characteristics at different r_g values into simuliunk exporter and added exception handlers
- #29 Code cleanup and added recheck functionality for plecs exporter to find new gate voltage 
- #29 Added plecs exporter for MOSFET and IGBT modules (outputs separate switch type and diode type xmls)

### Changed
- #22 Moved exporter functions to transistor classes and removed exportFunctions.py

## [0.2.7] - 2021-06-28
### Added
- Module manufacturers, fix compatibility problem in 0.2.6


## [0.2.6] - 2021-06-27
### Bugfixes
- #3, #8 : fixes to avoid typo errors in manufacturer and housing types along with comment line additions
### Added
- method 'parallel_transistors()' to parallel transistors object of same type 
### Changed
- rewrite export_to_matlab() function
### Removed
- remove dependency from matlab-pip-package

## [0.2.5] - 2021-06-10
## Added
- export_simulink_loss_model using new functions to search transistor elements (incl. fix #17)

### Removed
- export_simulink_v1 (outdated)


## [0.2.4] - 2021-05-28
### Added
- #13: GeckoCircuits Exporter exports mirrowed conducting characterisitc for negative currents
### Bugfixes
- #11, #12: Path displays when export to gecko (.scl) or to .json

## [0.2.3] - 2021-05-21
### Added
- Simple calculation method for mosfet gate resistor (Paper PCIM 2006: D.Kübrich 'Invetsigation of Turn-Off Behaviour under the Assumption of Linear Capacitances')
### Bugfix
- bug #7: was not fully fixed. Fixed now.
- bug #9: in case of no err-data, fill working point with object instead of list

## [0.2.2] - 2021-05-11
### Added
- print_TDB() returns a list with transistor names
- add some CREE power module housing types

### Bugfix
- fix #6: Avoid KeyError when using devices without err-losscurves
- fix #7: wrong fill of wp.xxx_r_channel/xxx_v_channel when using transistor.update_wp() or transistor.quickstart_wp()

## [0.2.1] - 2021-05-06
### Bugfix
- Problem when reading .csv-files generated by english-language systems

## [0.2.0] - 2021-05-04
### Added
- Example template to generate a transistor object
- transistor method: linearize_switch_ui_graph
- transistor.switch methods: print_all_channel_data, print_channel_data_vge, print_channel_data_temp
- New class LinearizedModel: Contains data for a linearized Switch/Diode depending on given operating point.
- New class to store c_iss, c_oss, c_rss in Transistor.
- New Transistor attribute: e_coss
- Documentation drawing
- Exporter: GeckoCIRCUITS
- calc_object_i_e to calculate loss loss curves for other gate resistors/voltage levels
- New class 'wp' to store local calculation parameters to use in your program
- automatically fill 'wp' objects when using functions like find_approx_wp()
- added a quick start to fill in 'wp' values quick and easy
- New housing types
- .json exporter

### Removed
- Removed Metadata class. Added its attributes to Transistor class instead
### Changed
- Restructured foster thermal model argument handover
- Rename package to transistordatabase (instead of transistor_database) due to pip package rules
- csv2array callable with options
- move some functionality out of transistor class (tdb.Transistor. -> tdb.)

## [0.1.0] - 2021-02-04
### Added
- Construct a Transistor-object and save relevant data in its attributes and subclasses
- Class structure documented in a class UML diagram
- Save Transistor-object in an object database created with mongodb
- Mandatory attributes and restricted types/values to guarantee only valid and functional Transistors can be added to
  the database
- Matlab-Exporter

[Unreleased]: https://github.com/upb-lea/transistordatabase/compare/0.5.1...HEAD
[0.5.1]: https://github.com/upb-lea/transistordatabase/compare/0.5.0...0.5.1
[0.5.0]: https://github.com/upb-lea/transistordatabase/compare/0.4.1...0.5.0
[0.4.1]: https://github.com/upb-lea/transistordatabase/compare/0.4.0...0.4.1
[0.4.0]: https://github.com/upb-lea/transistordatabase/compare/0.3.3...0.4.0
[0.3.3]: https://github.com/upb-lea/transistordatabase/compare/0.3.2...0.3.3
[0.3.2]: https://github.com/upb-lea/transistordatabase/compare/0.3.1...0.3.2
[0.3.1]: https://github.com/upb-lea/transistordatabase/compare/0.3.0...0.3.1
[0.3.0]: https://github.com/upb-lea/transistordatabase/compare/0.2.14...0.3.0
[0.2.14]: https://github.com/upb-lea/transistordatabase/compare/0.2.13...0.2.14
[0.2.13]: https://github.com/upb-lea/transistordatabase/compare/0.2.12...0.2.13
[0.2.12]: https://github.com/upb-lea/transistordatabase/compare/0.2.11...0.2.12
[0.2.11]: https://github.com/upb-lea/transistordatabase/compare/0.2.10...0.2.11
[0.2.10]: https://github.com/upb-lea/transistordatabase/compare/0.2.9...0.2.10
[0.2.9]: https://github.com/upb-lea/transistordatabase/compare/0.2.8...0.2.9
[0.2.8]: https://github.com/upb-lea/transistordatabase/compare/0.2.7...0.2.8
[0.2.7]: https://github.com/upb-lea/transistordatabase/compare/0.2.6...0.2.7
[0.2.6]: https://github.com/upb-lea/transistordatabase/compare/0.2.5...0.2.6
[0.2.5]: https://github.com/upb-lea/transistordatabase/compare/0.2.4...0.2.5
[0.2.4]: https://github.com/upb-lea/transistordatabase/compare/0.2.3...0.2.4
[0.2.3]: https://github.com/upb-lea/transistordatabase/compare/0.2.2...0.2.3
[0.2.2]: https://github.com/upb-lea/transistordatabase/compare/0.2.1...0.2.2
[0.2.1]: https://github.com/upb-lea/transistordatabase/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/upb-lea/transistordatabase/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/upb-lea/transistordatabase/compare/0.1.0...0.1.0

