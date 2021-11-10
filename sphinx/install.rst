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
If you already have git installed, make sure you are using the latest version.

.. note::
    During installation, you will be asked 'Which editor would you like Git to use?'. Default is 'Vim', but it is one of the most complex one for beginners. Switch to 'Notepad++', 'Nano' or another one.

Install Python
--------------
Install latest Python version: `Link <https://www.python.org/>`_.

Install Pycharm
---------------
`Installation file <https://www.jetbrains.com/pycharm/download/download-thanks.html?platform=linux&code=PCC>`_.

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
Inside pycharm, create a new project. Select 'new environment using' -> 'Virtualenv'.
As a base interpreter, select 'C:\Users\xxxxxx\AppData\Local\Programs\Python\Python39\Python.exe'. Click on create.
Navigate to file -> settings -> Project -> Python Interpreter -> '+' -> search for 'transistordatabase' -> 'Install Package'


Complete minimal python example
*******************************
Copy this example to a new pycharm project.
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

On the output line, you should see a message which links to the datasheet file. Click on it to view the datasheet in your browser. If this works, you have set up the transistor database correctly.
