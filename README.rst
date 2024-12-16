.. sectnum::

###########################
Transistordatabase
###########################

The Transistordatabase is a tool developed by LEA from the University Paderborn which helps working with choosing transistors for the developement of electronics.
When it comes to the point of choosing a transistor, there is typically a lot of trouble with different programs. Often there are multiple programs for
calculating transistor parameters and a schematic simulator to verify the results.
Now your colleague is working on a different electronics topology and may use different programs. This is a problem because in most cases your transistors will never be
compatible with the ones from your colleague. The Transistordatabase now solves this problem:
Here Transistors can be saved in a database and makes them easy to interchange between platforms. It is possible to export
Transistor data to various simulation software and share it to a colleague using a .json-File.

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/docs/images/Why_transistordatabase.png
    :align: center
    :alt: Why transistor database?


Functionality overview
***********************

Here are some examples on the functionality of the Transistordatabase:

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/docs/images/Workflow.png
    :align: center
    :alt: Workflow

* digitize transistor datasheet parameters and graphs and save it to the TDB (Transistordatabase)
* use this data for calculations in python (e.g. some loss calulations for a boost-converter)
* export this data to matlab for calculations in matlab
* export transistors to GeckoCIRCUITS simulation program
* export transistors to Simulink simulation program
* export transistors to PLECS simulation program

.. note::
    Development status: Alpha


###########################
Features
###########################

There are 3 features implemented in the Transistordatabase. First is the python interface which can be used to manage the Database and
their Transistors. The python interface can also be used to implemement optimization routines.
Then there is a GUI which is mostly used to manage the Database and visualize different properties of the stored Transistors.
As the third feature the Transistordatabase can be updated by an Online-Database. You can choose to work with our Online Repository or create your own if needed. 

Python interface
*******************************

Use the transistor data in you self-written optimization program, see figure:

* Automatic calculate your converter losses with many different transistors
* Search the database for usable transistors for your application
* Functions provided, to search for closest operating point
* Functions provided, to linearize the transistor/diode conduction behaviour
* Functions provided, to calculate the output capacitances Energy from the C_oss-curve 
* Use own loss measurements for above features (coming soon)

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/docs/documentation/workflow_wp.png
    :align: center
    :alt: optimization

GUI
*******************************

* Manage, store and search the transistors
* Export transistor models to programs like GeckoCIRCUITS, PLECS, Matlab/Octave
* Compare transistors (interpolate switch loss data for new gate resistors and temperatures, ...)

Here are some screenshots of the GUI:

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/docs/images/gui_database.png
    :align: center
    :alt: gui_database

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/docs/images/gui_comparison.png
    :align: center
    :alt: gui_comparison

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/docs/images/gui_create_transistor.png
    :align: center
    :alt: gui_create_transistor


Transistordatabase Fileexchange
*******************************

`This <https://github.com/upb-lea/transistordatabase_File_Exchange>`__ repository contains the Transistors currently added to the Transistordatabase.
Every Transistor from this repository can be automatically downloaded to your local Database. Since this only relies on the index.txt containing the links
to each transistor which shall be downloaded it is possible to create your own repository. Next to the Transistor updates there is a list of housing types and
module manufacturers which are supported by the Database which are also set in the Fileexchange respository.

You can publish your own Transistors to this repository by generating a pull request.
If you don't want to create a github account, you can also send the .json file to this :email:`email address <tdb@lea.upb.de>`.


############
Installation
############

Windows
*******

Install Python
--------------
Install latest Python version: `Link <https://www.python.org/>`__.

Install Pycharm (optional)
--------------------------
`Installation file <https://www.jetbrains.com/pycharm/download/download-thanks.html?platform=linux&code=PCC>`_.

Download and run executable
---------------------------
Download exe-file `here <https://groups.uni-paderborn.de/lea/public/downloads/transistordatabase.zip>`_


Linux
*****
Ubuntu

.. code-block::

   sudo apt install python3 python3-pip

.. note::
    Install pycharm from Snapstore

All Operating systems: Install the transistor database
******************************************************
Inside pycharm, create a new project. Select 'new environment using' -> 'Virtualenv'. |br|
As a base interpreter, select 'C:\Users\xxxxxx\AppData\Local\Programs\Python\Python39\Python.exe'. Click on create. |br|
Navigate to file -> settings -> Project -> Python Interpreter -> '+' -> search for 'transistordatabase' -> 'Install Package' |br|


##########################
Complete documentation
##########################
The complete documentation can be found `here <https://upb-lea.github.io/transistordatabase/main/transistordatabase.html>`__.


##########################
Usage
##########################

Minimal python example
*******************************

.. code-block::

    from transistordatabase.database_manager import DatabaseManager

    # Path for json files
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tdb_example")

    # Create DatabaseManager instance and set it to json format
    tdb_json = DatabaseManager()
    tdb_json.set_operation_mode_json(path)

    # Print database
    tdb_json.print_tdb()

    # load a transistor from the database
    transistor_loaded = tdb_json.load_transistor('CREE_C3M0016120K')

In addition to that in `this file <https://github.com/upb-lea/transistordatabase/blob/main/transistordatabase/housing_types.txt>`_ there are
more simple examples.


Generate a new transistor
*************************

Transistor object basics
------------------------
Transistor |br|
| |br|
+-Metadata |br|
| |br|
+-Switch |br|
| +-Switch Metadata |br|
| +-Channel Data |br|
| +-Switching Data |br|
| |br|
+-Diode |br|
| +-Diode Metadata |br|
| +-Channel Data |br|
| +-Switching Data |br|
| |br|
+-wp (temporary storage for further calculations) |br|

Reading curves from the datasheet
---------------------------------
For reading datasheet curves, use the tool `WebPlotDigitizer <https://apps.automeris.io/wpd/>`_. There is a online-version available. Also you can download it for Linux, Mac and Windows. WebPlotDigitizer is open source software.

Channel data for switch and diode always needs to be positive. Some Manufacturers give diode data in the 3rd quadrant. Here is an example how to set the axes and export the data inside WebPlotDigitizer:

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/docs/images/Diode_channel_data_negative.png
    :align: center
    :alt: diode channel data negative

Use the template to generate a new transistor object
----------------------------------------------------

After digitizing the curves, you can use a template to generate a new transistor object and store it to the database. For this, see the  `template </template_example/template_example.py>`_.

Some values need to follow some rules, e.g. due to different spelling versions, the manufacturers name or housing types must be written as in the lists below. Some general hints to fill the template:

    * `List of manufacturers <https://github.com/upb-lea/transistordatabase/blob/main/transistordatabase/module_manufacturers.txt>`_
    * `List of housing types <https://github.com/upb-lea/transistordatabase/blob/main/transistordatabase/housing_types.txt>`_
    * `Fuji housing overview <https://www.fujielectric.com/products/semiconductor/model/igbt/2pack.html>`_

In many cases, two capacity curves are specified in the data sheets. One curve for the full voltage range, and one with zoom to a small voltage range. To represent the stored curves in the best possible way, both curves can be read in and then merged.

.. code-block::

    c_rss_normal = csv2array('transistor_c_rss.csv', first_x_to_0=True)
    c_rss_detail = csv2array('transistor_c_rss_detail.csv', first_x_to_0=True)

    transistor_args = {
                   ...
                   'c_rss': {"t_j": 25, "graph_v_c": c_rss_merged},
				   ...
                   }




Usage of Transistor.wp. in your programs
*********************************************
There is a subclass .wp where you can fill for further program calculations.

Full-automated example
----------------------
**Use the quickstart method to fill in the wp-class**

There is a search function, that chooses the closes operating point. In the full-automated method, there are some predefined values

    * Chooses transistor.switch.t_j_max - 25°C as operating temperature to start search
    * Chooses transistor.i_abs_max/2 as operating current to start search
    * Chooses v_g = 15V as gate voltage to start search

.. code-block::

   transistor_loaded.quickstart_wp()

Half-automated example
----------------------
**Fill in the wp-class by a search-method to find the closes working point to your methods**

Insert a working point of interest. The algorithm will find the closest working point and fills out the Transistor.wp.-class
.. code-block::

   transistor_loaded.update_wp(125, 15, 50)

Non-automated example
---------------------
**Fill in the wp-class manually**

Look for all operating points manually. This will result in an error in case of no match.
.. code-block::

    transistor_loaded.wp.e_oss = transistor_loaded.calc_v_eoss()
    transistor_loaded.wp.q_oss = transistor_loaded.calc_v_qoss()

    # switch, linearize channel and search for losscurves
    transistor_loaded.wp.switch_v_channel, transistor_loaded.wp.switch_r_channel = transistor_loaded.calc_lin_channel(25, 15, 150, 'switch')
    transistor_loaded.wp.e_on = transistor_loaded.get_object_i_e('e_on', 25, 15, 600, 2.5).graph_i_e
    transistor_loaded.wp.e_off = transistor_loaded.get_object_i_e('e_off', 25, -4, 600, 2.5).graph_i_e

    # diode, linearize channel and search for losscurves
    transistor_loaded.wp.diode_v_channel, transistor_loaded.wp.diode_r_channel = transistor_loaded.calc_lin_channel(25, -4, 150, 'diode')

Calculations with transistor objects
************************************

Parallel transistors
--------------------
To parallel transistors use the function.

  * In case of no parameter paralleling is for 2 transistors
  * In case of parameter, paralleling is for x transistors. Example here is for three transistors.

.. code-block::

    parallel_transistorobject = tdb_json.parallel_transistors(transistor_loaded, 3)

After this, you can work with the transistor object as usual, e.g. fill in the .wp-workspace or export the device to Matlab, Simulink or GeckoCIRCUITS.

#########################
Export transistor objects
#########################

Using transistors within pyhton you have already seen. Now we want to take a closer look at exporting the transistors to other programs. These exporters are currently working. Some others are planned for the future.

Export a Virtual datasheet
***************************
This function exports a virtual datasheet to see stored data in the database. Function display the output path of .html-file, which can be opened in your preferred browser.

.. code-block::

    # Windows users: export datasheet
    transistor_loaded.export_datasheet()

    # Linux users: export datasheet as html
    # look for CREE_C3M0016120K.html in your current working directory
    html_str = transistor_loaded.export_datasheet(build_collection=True)
    Html_file = open(f"{transistor_loaded.name}.html", "w")
    Html_file.write(html_str)
    Html_file.close()

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/docs/images/Virtual_Datasheet.png
    :align: center
    :alt: Generated virtual datasheet example

Export to GeckoCIRCUITS
***********************
GeckoCIRCUITS is an open source multi platform schematic simulator. Java required. Direct `download link <http://gecko-simulations.com/GeckoCIRCUITS/GeckoCIRCUITS.zip>`_.
At the moment you need to know the exporting parameters like gate resistor, gate-voltage and switching voltage. This will be simplified in the near future.

.. code-block::

    transistor_loaded.export_geckocircuits(True, 600, 15, -4, 2.5, 2.5)

From now on, you can load the model into your GeckoCIRCUITS schematic.

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/docs/images/Example_Gecko_Exporter.png
    :align: center
    :alt: GeckoExporter usage example

.. hint::
    It is also possible to control GeckoCIRCUITS from python, e.g. to sweep transistors. In this case, linux users should consider to run `this <https://github.com/tinix84/gecko/releases/tag/v1.1>`_ Version of GeckoCIRCUITS instead the above one (port to OpenJDK).

Export to PLECS
***************
For a thermal and loss simulation using PLECS simulation tool, it requires the transistor loss and characteristic curves to be loaded in XML(Version 1.1) file format. More information on how to load the XML data can be found from here. To export the transistor object from your database to plecs required xml file format, following lines need to be executed starting with loading the required datasheet.

.. code-block::

    transistor_loaded.export_plecs()

Outputs are xml files - one for switch and one for diode (if available), which can be then loaded into your schematic following the instructions as mentioned `here <https://www.plexim.com/support/videos/thermal-modeling-part-1>`__. Note that if channel curves for the default gate-voltage are found missing then the xml files could not be possible to generate and a respective warning message is issued to the user. The user can change the default gate-voltage and switching voltage by providing an extra list argument as follows:

.. code-block::

    transistor_loaded.export_plecs([15, -15, 15, 0])

Note that all the four parameters (Vg_on, Vg_off) for IGBTs/Mosfets and (Vd_on, Vd_off) for reverse/body diodes are necessary to select the required curves that needs to be exported to switch and diode XMLs respectively.

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/docs/images/PLECS_thermal_editor.png
    :align: center
    :alt: PLECS thermal exporter usage example

Export to Simulink
******************
For a loss simulation in simulink, there is a IGBT model available, which can be found in this `simulink model <https://de.mathworks.com/help/physmod/sps/ug/loss-calculation-in-a-three-phase-3-level-inverter.html>`_ . Copy the model to you schematic and fill the parameters as shown in the figure. Export a transistor object from your database by using the following command. Example for a Infineon transistor.
.. code-block::

    transistor_loaded = db.load_transistor('Infineon_FF200R12KE3')
    transistor_loaded.export_simulink_loss_model()

Output is a .mat-file, you can load in your matlab program to simulate. Now, you are able to sweep transistors within your simulation. E.g. some matlab-code:

.. code-block::

    load Infineon_FF200R12KE3_Simulink_lossmodel.mat;
    load Infineon_FF300R12KE3_Simulink_lossmodel.mat;
    load Fuji_2MBI200XBE120-50_Simulink_lossmodel.mat;
    load Fuji_2MBI300XBE120-50_Simulink_lossmodel.mat;
    Transistor_array = [Infineon_FF200R12KE3 Infineon_FF300R12KE3 Fuji_2MBI200XBE120-50 Fuji_2MBI300XBE120-50];
    for i_Transistor = 1:length(Transistor_array)
        Transistor = Transistor_array(i_Transistor);
        out = sim('YourSimulinkSimulationHere');

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/docs/images/Example_Simulink_Exporter.png
    :align: center
    :alt: Simulink exporter usage example

Export to Matlab/Octave
***********************
Python dictionary can be exported to Matlab, see the following example:

.. code-block::

    transistor_loaded = db.load_transistor('Fuji_2MBI100XAA120-50')
    transistor_loaded.export_matlab()

A .mat-file is generated, the exporting path will be displayed in the python console. You can load this file into matlab or octave.

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/docs/images/Matlab.png
    :align: center
    :alt: Matlab .mat exporter usage example


#######
Others
#######

For developers
***********************

Currently the transistordatabase does not only support a json format but also a mongodb database.
Therefore mongodb needs to be installed:
Install with standard settings. Use the MongoDB community server, as platform, choose windows `Link <https://www.mongodb.com/try/download/community>`__.

Roadmap
*******
Planned features in 2024

* Focus on adding self-measured data to the database
* Working with self-measured data in exporters
* Usability improvements
* Stable software

Organisation
************
Bug Reports
-----------
Please use the issues report button within github to report bugs.

Changelog
---------
Find the changelog `here <https://github.com/upb-lea/transistordatabase/blob/main/CHANGELOG.md>`__.

Contributing
------------
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. For contributing, please refer to this `section <https://github.com/upb-lea/transistordatabase/blob/main/Contributing.rst>`_.

About
*****
History and project status
--------------------------
This project started in 2020 as a side project and was initially written in matlab. It quickly became clear that the project was no longer a side project. The project should be completely rewritten, because many new complex levels have been added. To place the project in the open source world, the programming language python is used.

In January 2021 a very early alpha status was reached. First pip package was provided in may 2021. First GUI is provided in June 2022.

License
-------
Licensed under `GPLv3 <https://choosealicense.com/licenses/gpl-3.0/>`_



.. |br| raw:: html

      <br>
