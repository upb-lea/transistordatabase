# transistordatabase (TDB)
Import/export and manage transistor data in the transistor database.
## Why the transistordatabase
When developing electronics, you need to calculate and simulate your schematic before building up the hardware. When it comes to the point of choosing a transistor, there is typically a lot of trouble with different programs. In typical cases, you use more than one program for your calculation, e.g. a self-written program for a first guess, and a schematic simulator to verify your results. Your colleague is working on another electronics topology, may using two other programs. Both of you have stored a few transistor-files on your computers. But due to other programs and another way of using them in a self-written program, your transistors will never be compatible with your colleagures program. If he want's to use your transistors, he needs to generate them compleatly new from the datasheets to be compatible with his programs. Sharing programs and transistors will result in frustraction. This happens also in the same office (university / company / students).

The transistordatabase counteracts this problem. By a defined file format, you can handle these objects, export it to some propretery simulation software and share it by a .json-file to your colleagues or share it with the world by using the [transistor database file exchange git repository](https://github.com/upb-lea/transistordatabase_File_Exchange).

![](https://raw.githubusercontent.com/upb-lea/transistordatabase/main/documentation/Why_transistordatabase.png)

## Functionality overview
![](https://raw.githubusercontent.com/upb-lea/transistordatabase/main/documentation/Workflow.png)

Functionality examples:
 * digitize transistor datasheet parameters and graphs and save it to the TDB
 * use this data for calculations in python (e.g. some loss calulations for a boost-converter)
 * export this data to matlab for calculations in matlab
 * export transistors to GeckoCIRCUITS simulation program
 * export transistors to Simulink simulation program
 * export transistors to PLECS simulation program

Note: Development status: Alpha

# 1. Installation
## 1.1 Windows
### 1.1.1 Install Mongodb
For the first usage, you need to install mongodb.
Windows
Use the MongoDB community server, as platform, choose windows. [Link](https://www.mongodb.com/try/download/community)

### 1.1.2 Install git
[Installation file](https://git-scm.com/download/win)

### 1.1.3 Install Pycharm
[Installation file](https://www.jetbrains.com/pycharm/download/download-thanks.html?platform=linux&code=PCC)

## 1.2 Linux
Archlinux / Manjaro    
Enable Arch-User-Repository ([AUR](https://aur.archlinux.org/packages/mongodb-bin/)):
```
sudo pacman -Syu mongodb-bin git pycharm

```

Ubuntu
```
sudo apt install python3 python3-pip git
```
Note: Install pycharm from Snapstore

## 1.3 All Operating systems: Install the transitor database
Using Pycharm: Navigate to file -> settings -> Project -> Python Interpreter -> add: transistordatabase  

## 1.4 Complete minimal python example
```
# load the python package
import transistordatabase as tdb
# update the database from the online git-repository
tdb.update_from_fileexchange()
# print the database
tdb.print_TDB()
# load a transistor from the database
transistor_loaded = tdb.load({'name': 'CREE_C3M0016120K'})
# quick start fill in .wp.-storage for further calculations in your program
transistor_loaded.quickstart_wp()
```

# 2 transistordatabase's usage
Import transistordatabase to your python program
```
import transistordatabase as tdb
```


## 2.1 Generate a new transistor


### 2.1.1 transistor object basics
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
 |  +-Diode Metadata     
 |  +-Channel Data     
 |  +-Switching Data   
 |       
 +-wp (temporary storage for further calculations)

### 2.1.2 reading curves from the datasheet
For reading datasheet curves, use the tool [WebPlotDigitizer](https://automeris.io/WebPlotDigitizer/). There is a online-version available. Also you can download it for Linux, Mac and Windows. WebPlotDigitizer is open source software.
### 2.1.3 Use the template to generate a new transistor object
After digizing the curves, you can use a template to generate a new transistor object and store it to the database. For this, see the [template](/template_example/template_example.py)

Some hints to fill the template:
 * Fuji housing overview https://www.fujielectric.com/products/semiconductor/model/igbt/2pack.html



## 2.2 Update and load and share transistors
### 2.2.1 Update transistors from file exchange
There is a file exchange to share transistor objects. The repository can be found [here](https://github.com/upb-lea/transistordatabase_File_Exchange). To update your local transistordatabase type in to your python code
```
tdb.update_from_fileexchange()
```
After this, you can find new or updated transistor files in your local transistordatabase.
### 2.2.2 Search the database
Print all transistors inside the database
```
tdb.print_TDB()
```
If you want to store the transistor list, this function returns the names in a variable. Next option is the usage of filters, e.g. print the housing type and the hyperlink to the datasheet. All database entries can be used as filter.
```
tdb.print_TDB(['housing_type','datasheet_hyperlink'])
```

### 2.2.3 Load a transistor from the database
```
transistor_loaded = tdb.load({'name': 'CREE_C3M0016120K'})
```
### 2.2.4 Share your transistors with the world
Use your local generated transistor, load it into your workspace and export it, e.g.
```
transistor_loaded = load({'name': 'CREE_C3M0016120K'})
transistor_loaded.export_json()
```
You can upload this file to the [transistor database file exchange git repository](https://github.com/upb-lea/transistordatabase_File_Exchange) by generating a pull request.
## 2.3 Use Transistor.wp. for usage in your programs
There is a subclass .wp. you can fill for further program calculations.
### 2.3.1 Full-automated example: Use the quickstart method to fill in the wp-class.
There is a search function, that chooses the closes operating point. In the full-automated method, there are some predefined values
- Chooses transistor.switch.t_j_max - 25°C as operating temperature to start search
- Chooses transistor.i_abs_max/2 as operating current to start search
- Chooses v_g = 15V as gate voltage to start search
```
transistor_loaded.quickstart_wp()
```
### 2.3.2 Half-automated example: fill in the wp-class by a search-method to find the closes working point to your methods
Insert a working point of interest. The algorithm will find the closest working point and fills out the Transistor.wp.-class
```
transistor.update_wp(125, 15, 50)
```
### 2.3.3 Non-automated example: fill in the wp-class manually
Look for all operationg points manually. This will result in an error in case of no match.

```
transistor_loaded.wp.e_oss = transistor_loaded.calc_v_eoss()
transistor_loaded.wp.q_oss = transistor_loaded.calc_v_qoss()

# switch, linearize channel and search for losscurves
transistor_loaded.wp.switch_v_channel, transistor_loaded.wp.switch_r_channel = transistor_loaded.calc_lin_channel(25, 15, 150, 'switch')
transistor_loaded.wp.e_on = transistor_loaded.get_object_i_e('e_on', 25, 15, 600, 2.5).graph_i_e
transistor_loaded.wp.e_off = transistor_loaded.get_object_i_e('e_off', 25, -4, 600, 2.5).graph_i_e

# diode, linearize channel and search for losscurves
transistor_loaded.wp.diode_v_channel, transistor_loaded.wp.diode_r_channel = transistor_loaded.calc_lin_channel(25, -4, 150, 'diode')
```
## 2.4 Calculations with transistor objects
### 2.4.1 Parallel transistors
To parallel transistors use the function.
 * In case of no parameter paralleling is for 2 transistors
 * in case of parameter, paralleling is for x transistors. Example here is for three transistors.
```
transistor = load({'name': 'Infineon_FF200R12KE3'})
parallel_transistorobject = transistor.parallel_transistors(3)
```
After this, you can work with the transistor object as usual, e.g. fill in the .wp-workspace or export the devicice to Matlab, Simulink or GeckoCIRCUITS.


## 2.5 Export transistor objects to other programs
Using transistors within pyhton you have already seen. Now we want to take a closer look at exporting the transistors to other programs.
These exporters are currently working. Some others are planned for the future.
### 2.5.1 Export to GeckoCIRCUITS
GeckoCIRCUITS is an open source multi platform schematic simulator. Java required. Direct [download link](http://gecko-simulations.com/GeckoCIRCUITS/GeckoCIRCUITS.zip).
At the moment you need to know the exporting parameters like gate resistor, gate-voltage and switching voltage. This will be simplified in the near future.
```
transistor = tdb.load({'name': 'Fuji_2MBI100XAA120-50'})
tdb.export_geckocircuits(transistor, 600, 15, -4, 2.5, 2.5)
```
From now on, you can load the model into your GeckoCIRCUITS schematic.
![](https://raw.githubusercontent.com/upb-lea/transistordatabase/main/documentation/Example_Gecko_Exporter.png)
Hint: it is also possible to control GeckoCIRCUITS from python, e.g. to sweep transistors. In this case, linux users should consider to run [this](https://github.com/tinix84/gecko/releases/tag/v1.1) Version of GeckoCIRCUITS instead the above one (port to OpenJDK).

### 2.5.2 Export to Matlab
Python dictionary can be exported to Matlab, see the following example:
```
transistor = tdb.load({'name': 'Fuji_2MBI100XAA120-50'})
tdb.export_to_matlab(transistor)
```
A .mat-file is generated, the exporting path will be displayed in the python console. You can load this file into matlab.

### 2.5.3 Export to Simulink
For a loss simulation in simulink, there is a IGBT model available, which can be found in this [simulink model](https://de.mathworks.com/help/physmod/sps/ug/loss-calculation-in-a-three-phase-3-level-inverter.html). Copy the model to you schematic and fill the parameters as shown in the figure. Export a transistor object from your database by using the following command. Example for a Infineon transistor.
```
transistor = tdb.load({'name': 'Infineon_FF200R12KE3'})
tdb.export_simulink_loss_model(transistor)
```
Output is a .mat-file, you can load in your matlab program to simulate. Now, you are able to sweep transistors within your simulation. E.g. some matlab-code:
```
load Infineon_FF200R12KE3_Simulink_lossmodel.mat;
load Infineon_FF300R12KE3_Simulink_lossmodel.mat;
load Fuji_2MBI200XBE120-50_Simulink_lossmodel.mat;
load Fuji_2MBI300XBE120-50_Simulink_lossmodel.mat;
Transistor_array = [Infineon_FF200R12KE3 Infineon_FF300R12KE3 Fuji_2MBI200XBE120-50 Fuji_2MBI300XBE120-50];
for i_Transistor = 1:length(Transistor_array)
    Transistor = Transistor_array(i_Transistor);
    out = sim('YourSimulinkSimulationHere');
```
![](https://raw.githubusercontent.com/upb-lea/transistordatabase/main/documentation/Example_Simulink_Exporter.png)

### 2.5.4 Export to PLECS
For a thermal and loss simulation using PLECS simulation tool, it requires the transistor loss and characteristic curves to be loaded in XML(Version 1.1) file format. More information on how to load the XML data can be found from [here](https://www.plexim.com/support/videos/thermal-modeling-part-1). To export the transistor object from your database to plecs required xml file format, following lines need to be executed starting with loading the required datasheet.
```
transistor = tdb.load({'name': 'Fuji_2MBI200XAA065-50'})
tdb.export_plecs(transistor)
```
Outputs are xml files - one for switch and one for diode (if available), which can be then loaded into your schematic following the instructions as mentioned [here](https://www.plexim.com/support/videos/thermal-modeling-part-1). Note that if channel curves for the default gate-voltage are found missing then the xml files could not be possible to generate and a respective warning message is issued to the user. The user can change the default gate-voltage and switching voltage by providing  an extra list argument as follows:
```
transistor = tdb.load({'name': 'Fuji_2MBI200XAA065-50'})
tdb.export_plecs(transistor, [15, -15, 15, 0])       
```
Note that all the four parameters (Vg_on, Vg_off) for IGBTs/Mosfets and (Vd_on, Vd_off) for reverse/body diodes are necessary to select the required curves that needs to be exported to switch and diode XMLs respectively.
![](https://raw.githubusercontent.com/upb-lea/transistordatabase/main/documentation/PLECS_thermal_editor.png)

# 3. Roadmap
Planned features in 2021
* show a virtual datasheet of a transistor
* exporters to a few programs, e.g. Simulink, GeckoCIRCUITS, PLECs, ...
* save measurement data from double pulse measurements in the transistor database
* compare resistors within the database (e.g. compare measurements wit datasheet values, or compare datasheet values for transistor A with transistor B)
* provide a pip package

# 4. Organisation
## 4.1 Bug Reports
Please use the issues report button within github to report bugs.

## 4.2 Changelog
Find the changelog [here](CHANGELOG.md)

## 4.3 Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
For contributing, please refer to this [section](Contributing.md).

## 4.4 Authors and acknowledgement
Actual developers
* Nikolas Förster
* Henning Steinhagen   
* Mohan Nagella 

Project leading
* Nikolas Förster
* Philipp Rehlaender

Developers in the past
* Manuel Klädtke

## 4.5 License
[GPLv3](https://choosealicense.com/licenses/gpl-3.0/)

## 4.6 History and project status
This project started in 2020 as a side project and was initially written in matlab. It quickly became clear that the project was no longer a side project. The project should be completely rewritten, because many new complex levels have been added. To place the project in the open source world, the programming language python is used.      

In january 2021 a very early alpha status is reached. First pip package is provided in may 2021.
