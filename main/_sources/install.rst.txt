############
Installation
############

Windows
*******

Install Mongodb
---------------
For the first usage, you need to install mongodb. Install with standard settings. Use the MongoDB community server, as platform, choose windows `Link <https://www.mongodb.com/try/download/community>`_.

Install git
---------------
`Git Installation file <https://git-scm.com/download/win>`_.

Install Pycharm
---------------
`PyCharm Installation file <https://www.jetbrains.com/pycharm/download/download-thanks.html?platform=linux&code=PCC>`_.

Linux
*****
Archlinux / Manjaro

Enable Arch-User-Repository `(AUR) <https://aur.archlinux.org/packages/mongodb-bin/>`_.

.. code-block::

   sudo pacman -Syu mongodb-bin git pycharm

Ubuntu

.. code-block::

   sudo apt install python3 python3-pip git

.. note::
    Install pycharm from Snapstore

All Operating systems: Install the transistor database
******************************************************
Using Pycharm: Navigate to file -> settings -> Project -> Python Interpreter -> '+' -> search for 'transistordatabase' -> 'Install Package'

Complete minimal python example
*******************************
.. code-block::

    # load the python package
    import transistordatabase as tdb

    # update the database from the online git-repository
    tdb.update_from_fileexchange()

    # print the database
    tdb.print_TDB()

    # load a transistor from the database
    transistor_loaded = tdb.load({'name': 'CREE_C3M0016120K'})

    # export a virtual datasheet
    transistor_loaded.export_datasheet()

