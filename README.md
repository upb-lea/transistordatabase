# transistordatabase (TDB)
Import/export and manage transistor data in the transistor database.

![](https://raw.githubusercontent.com/upb-lea/transistordatabase/main/documentation/Workflow.png)

Functionality examples:
 * digitize transistor datasheet parameters and graphs and save it to the TDB
 * use this data for calculations in python (e.g. some loss calulations for a boost-converter)
 * export this data to matlab for calculations in matlab
 * export transistors to GeckoCIRCUITS simulation program

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
 |  +-Switch Metadata     
 |  +-Channel Data     
 |  +-Switching Data     
 +-wp (temporary storage for further calculations)

### 2.1.2 reading curves from the datasheet
For reading datasheet curves, use the tool [WebPlotDigitizer](https://automeris.io/WebPlotDigitizer/). There is a online-version available. Also you can download it for Linux, Mac and Windows. WebPlotDigitizer is open source software.
### 2.1.3 Use the template to generate a new transistor object
After digizing the curves, you can use a template to generate a new transistor object and store it to the database. For this, see the [template](/template_example/template_example.py)

Some hints to fill the template:
 * Fuji housing overview https://www.fujielectric.com/products/semiconductor/model/igbt/2pack.html



## 2.2 Update transistors from file exchange
There is a file exchange to share transistor objects. The repository can be found [here](https://github.com/upb-lea/transistordatabase_File_Exchange). To update your local transistordatabase type in to your python code
```
tdb.update_from_fileexchange()
```
After this, you can find new or updated transistor files in your local transistordatabase.
## 2.3 Load a transistor from the database
```
transistor_loaded = tdb.load({'name': 'CREE_C3M0016120K'})
```
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
### 2.3.2 Non-automated example: fill in the wp-class manually
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
* Manuel Klädtke
* Henning Steinhagen    

Project leading
* Nikolas Förster
* Philipp Rehlaender

Developers in the past

## 4.5 License
[GPLv3](https://choosealicense.com/licenses/gpl-3.0/)

## 4.6 History and project status
This project started in 2020 as a side project and was initially written in matlab. It quickly became clear that the project was no longer a side project. The project should be completely rewritten, because many new complex levels have been added. To place the project in the open source world, the programming language python is used.      

In january 2021 a very early alpha status is reached. First pip package is provided in may 2021.
