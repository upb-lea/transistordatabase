##########################
transistordatabase's usage
##########################

Import transistordatabase to your python program

.. code-block::

    import transistordatabase as tdb

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
For reading datasheet curves, use the tool `WebPlotDigitizer <https://git-scm.com/download/win>`_. There is a online-version available. Also you can download it for Linux, Mac and Windows. WebPlotDigitizer is open source software.

Channel data for switch and diode always needs to be positive. Some Manufacturers give diode data in the 3rd quadrant. Here is an example how to set the axes and export the data inside WebPlotDigitizer:

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/sphinx/images/Diode_channel_data_negative.png
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

Update and load and share transistors
*************************************

Update transistors from file exchange
-------------------------------------
There is a file exchange to share transistor objects. The repository can be found `here <https://github.com/upb-lea/transistordatabase_File_Exchange>`__. To update your local transistordatabase type in to your python code

.. code-block::

    tdb.update_from_fileexchange()

After this, you can find new or updated transistor files in your local transistordatabase.

Search the database
-------------------
Print all transistors inside the database

.. code-block::

    tdb.print_TDB()

If you want to store the transistor list, this function returns the names in a variable. Next option is the usage of filters, e.g. print the housing type and the hyperlink to the datasheet. All database entries can be used as filter.

.. code-block::

    tdb.print_TDB(['housing_type','datasheet_hyperlink'])

Load a transistor from the database
-----------------------------------

.. code-block::

    transistor_loaded = tdb.load({'name': 'CREE_C3M0016120K'})

Share your transistors with the world
-------------------------------------
Use your local generated transistor, load it into your workspace and export it, e.g.

.. code-block::

    transistor_loaded = load({'name': 'CREE_C3M0016120K'})
    transistor_loaded.export_json()

You can upload this file to the `transistor database file exchange git repository <https://github.com/upb-lea/transistordatabase_File_Exchange>`_  by generating a pull request.

if you don't want to create a github account, you can also send the .json file to this `email address <mailto:tdb@lea.upb.de>.`_.

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

   transistor.update_wp(125, 15, 50)

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

    transistor = load({'name': 'Infineon_FF200R12KE3'})
    parallel_transistorobject = transistor.parallel_transistors(3)

After this, you can work with the transistor object as usual, e.g. fill in the .wp-workspace or export the device to Matlab, Simulink or GeckoCIRCUITS.






.. |br| raw:: html

      <br>