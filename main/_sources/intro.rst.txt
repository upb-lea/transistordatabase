.. sectnum::

############
Introduction
############

Why the transistordatabase?
*****************************

When developing electronics, you need to calculate and simulate your schematic before building up the hardware. When it comes to the point of choosing a transistor, there is typically a lot of trouble with different programs. In typical cases, you use more than one program for your calculation, e.g. a self-written program for a first guess, and a schematic simulator to verify your results. Your colleague is working on another electronics topology, may using two other programs. Both of you have stored a few transistor-files on your computers. But due to other programs and another way of using them in a self-written program, your transistors will never be compatible with your colleagures program. If he want's to use your transistors, he needs to generate them compleatly new from the datasheets to be compatible with his programs. Sharing programs and transistors will result in frustraction. This happens also in the same office (university / company / students).

The transistordatabase counteracts this problem. By a defined file format, you can handle these objects, export it to some propretery simulation software and share it by a .json-file to your colleagues or share it with the world by using the `transistor database file exchange git repository <https://github.com/upb-lea/transistordatabase_File_Exchange>`_.

.. image:: /images/Why_transistordatabase.png
    :width: 500px
    :align: center
    :height: 200px
    :alt: Why transistor database?

Functionality overview
***********************

.. image:: /images/Workflow.png
    :width: 650px
    :align: center
    :height: 350px
    :alt: Workflow

Functionality examples:

    * digitize transistor datasheet parameters and graphs and save it to the TDB
    * use this data for calculations in python (e.g. some loss calulations for a boost-converter)
    * export this data to matlab for calculations in matlab
    * export transistors to GeckoCIRCUITS simulation program
    * export transistors to Simulink simulation program
    * export transistors to PLECS simulation program

.. note::
    Development status: Alpha

.. include:: install.rst

.. include:: usage.rst

.. include:: exports.rst

.. include:: other.rst