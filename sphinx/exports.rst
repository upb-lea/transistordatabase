Export transistor objects
#########################

Using transistors within pyhton you have already seen. Now we want to take a closer look at exporting the transistors to other programs. These exporters are currently working. Some others are planned for the future.

Export a Virtual datasheet
***************************
This function exports a virtual datasheet to see stored data in the database. Function display the output path of .html-file, which can be opened in your prefered browser.

.. image:: /images/Virtual_Datasheet.png
    :align: center
    :alt: Generated virtual datasheet example

.. code-block::

transistor = tdb.load({'name': 'Fuji_2MBI100XAA120-50'})
transistor.export_datasheet()

Export to GeckoCIRCUITS
***********************
GeckoCIRCUITS is an open source multi platform schematic simulator. Java required. Direct `download link <http://gecko-simulations.com/GeckoCIRCUITS/GeckoCIRCUITS.zip>`_. At the moment you need to know the exporting parameters like gate resistor, gate-voltage and switching voltage. This will be simplified in the near future.
.. code-block::

    transistor = tdb.load({'name': 'Fuji_2MBI100XAA120-50'})
    transistor.export_geckocircuits(600, 15, -4, 2.5, 2.5)

From now on, you can load the model into your GeckoCIRCUITS schematic.

.. image:: /images/Example_Gecko_Exporter.png
    :align: center
    :alt: GeckoExporter usage example

.. hint::
    It is also possible to control GeckoCIRCUITS from python, e.g. to sweep transistors. In this case, linux users should consider to run `this <https://github.com/tinix84/gecko/releases/tag/v1.1>`_ Version of GeckoCIRCUITS instead the above one (port to OpenJDK).

Export to PLECS
***************
For a thermal and loss simulation using PLECS simulation tool, it requires the transistor loss and characteristic curves to be loaded in XML(Version 1.1) file format. More information on how to load the XML data can be found from here. To export the transistor object from your database to plecs required xml file format, following lines need to be executed starting with loading the required datasheet.

.. code-block::

    transistor = tdb.load({'name': 'Fuji_2MBI200XAA065-50'})
    transistor.export_plecs()

Outputs are xml files - one for switch and one for diode (if available), which can be then loaded into your schematic following the instructions as mentioned `here <https://www.plexim.com/support/videos/thermal-modeling-part-1>`_. Note that if channel curves for the default gate-voltage are found missing then the xml files could not be possible to generate and a respective warning message is issued to the user. The user can change the default gate-voltage and switching voltage by providing an extra list argument as follows:

.. code-block::

    transistor = tdb.load({'name': 'Fuji_2MBI200XAA065-50'})
    transistor.export_plecs([15, -15, 15, 0])

Note that all the four parameters (Vg_on, Vg_off) for IGBTs/Mosfets and (Vd_on, Vd_off) for reverse/body diodes are necessary to select the required curves that needs to be exported to switch and diode XMLs respectively.

.. image:: /images/PLECS_thermal_editor.png
    :align: center
    :alt: PLECS thermal exporter usage example

Export to Simulink
******************
For a loss simulation in simulink, there is a IGBT model available, which can be found in this `simulink model <https://de.mathworks.com/help/physmod/sps/ug/loss-calculation-in-a-three-phase-3-level-inverter.html>`_ . Copy the model to you schematic and fill the parameters as shown in the figure. Export a transistor object from your database by using the following command. Example for a Infineon transistor.
.. code-block::

    transistor = tdb.load({'name': 'Infineon_FF200R12KE3'})
    transistor.export_simulink_loss_model()

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

.. image:: /images/Example_Simulink_Exporter.png
    :align: center
    :alt: Simulink exporter usage example

Export to Matlab/Octave
***********************
Python dictionary can be exported to Matlab, see the following example:
.. code-block::

    transistor = tdb.load({'name': 'Fuji_2MBI100XAA120-50'})
    transistor.export_matlab()

A .mat-file is generated, the exporting path will be displayed in the python console. You can load this file into matlab or octave.

.. image:: /images/Matlab.png
    :align: center
    :alt: Matlab .mat exporter usage example
