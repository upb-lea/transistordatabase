# Transistor_Database (TDB)
Import/export and manage transistor data in the transistor database.

Functionality examples
 * digitize transistor datasheet parameters and graphs and save it to the TDB
 * use this data for calculations in python (e.g. some loss calulations for a boost-converter)
 * export this data to matlab for calculations in matlab
 


## Installation
### install the sources
```
cd /Documents/Folder/of/Interest   
git clone git@github.com:upb-lea/Transistor_Database.git
```
### installing TBD using pip
coming soon.

## Usage
### Generate a new transistor, use the template
#### transistor object working
Transistor      
 |     
 +-Metadata      
 |     
 +-Switch     
 |  +-Switch Metadata     
 |  +-Channel Data     
 |  +-Switching Data
 |          
 +-Diode     
    +-Switch Metadata     
    +-Channel Data     
    +-Switching Data     
 



#### reading curves from the datasheet
For reading datasheet curves, use the tool [WebPlotDigitizer](https://automeris.io/WebPlotDigitizer/). There is a online-version available. Also you can download it for Linux, Mac and Windows. WebPlotDigitizer is open source software.

### Load a transistor from the database



## Roadmap
Planned features in 2021
* show a virtual datasheet of a transistor
* exporters to a few programs, e.g. Simulink, GeckoCIRCUITS, PLECs, ...
* save measurement data from double pulse measurements in the transistor database
* compare resistors within the database (e.g. compare measurements wit datasheet values, or compare datasheet values for transistor A with transistor B)
* provide a pip package


## Bug Reports
Please use the issues report button within github to report bugs.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
For contributing, please refer to this [section](Contributing.md).
     
## Authors and acknowledgement
Actual developers
* Manuel Klädtke
* Henning Steinhagen     
      
Developers in the past


## Changelog
Find the changelog [here](CHANGELOG.md)

## License
[GPLv3](https://choosealicense.com/licenses/gpl-3.0/)

## History and project status
This project started in 2020 as a side project and was initially written in matlab. It quickly became clear that the project was no longer a side project. The project should be completely rewritten, because many new complex levels have been added. To place the project in the open source world, the programming language python is used.      
     
In january 2020 a very early alpha status is reached.
