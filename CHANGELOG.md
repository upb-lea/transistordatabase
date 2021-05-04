# Changelogt_ob_par
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Save Transistor-object in an object database created with [ZODB](http://www.zodb.org/en/latest/)
- Mandatory attributes and restricted types/values to guarantee only valid and functional Transistors can be added to
  the database
- Matlab-Exporter for later use with [Simscape Electrical](https://www.mathworks.com/products/simscape-electrical.html)
  , [PLECS](https://plexim.com/) or just general calculation/plots

[Unreleased]: https://github.com/upb-lea/Transistor_Database/compare/0.2.0...HEAD
[0.2.0]: https://github.com/upb-lea/Transistor_Database/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/upb-lea/Transistor_Database/compare/0.1.0...0.1.0
