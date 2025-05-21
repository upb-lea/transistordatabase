.. contents:: **Table of Contents**
    :depth: 1
    :local:

Drawings
********

For drawings (e.g. in readme-files), we recommend to use the program `Inkscape <https://inkscape.org/>`_. It is open source software and runs on Linux, Mac and Windows. If you want to draw electric circuits, we recommend this library on `github <https://github.com/upb-lea/Inkscape_electric_Symbols>`_.


Install the transistordatabase as a pip-package in developer mode
*****************************************************************

To develop code that will later be delivered as pip-package it is useful to install the code in developer mode. Note about the '.' point!

.. code-block::

    cd /source/of/transistordatabase-git/
    pip install -e .

The code in the installed pip-packet (corresponds to the linked git reposistory) is now changed in realtime.

.. note::

    When using the Pycharm Python Console, the kernel must be restarted for changes!


Set up a virtual environment
----------------------------

In lot of cases it is useful to set up a virtual environment and use this for coding of for testing.

.. code-block::

    # set up virtual environment once
    python3 -m venv /home/userxy/venv_tdb
    # attach to this virtual environment, everytime you need it
    source /home/userxy/venv_tdb/bin/activate


Write Code
**********


Code Structure
--------------
* functions/methods: 'lower_snake_case<https://en.wikipedia.org/wiki/Snake_case>'__.
* Classes: 'CamelCase<https://en.wikipedia.org/wiki/Camel_case>'__.

Folder and File Structure
-------------------------
* folder and function names lower case
* classes should go into _classes.py
* functions should go into _functions.py

Packages and Dependencies
-------------------------
In general, external packages should be involved as little as possible.
* for transistordatabase, use 'pathlib' instead of 'os'
* for femmt, use 'os' instead of 'pathlib'
* use pytest instead of unittest


Use type hints
--------------
Type Hints are used 
* for all function/classes handover parameters and function return values
* Function/Classes internal parameters do not need type-hints
* Find a type hint cheat sheet `here <https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html>`__.


Sphinx documentation using docstrings
-------------------------------------
* documentation necessary for all functions, classes and methods
* include typehints and explanations for every parameter
* include an example
* include a graphic
* Find a rst and sphinx cheat sheet `here <https://sphinx-tutorial.readthedocs.io/cheatsheet/>`__.

.. code-block::

    def print_tdb(filters: Optional[List[str]] = None, collection_name: str = "local") -> List[str]:
	"""
	Print all transistorelements stored in the local database

	:param filters: filters for searching the database, e.g. 'name' or 'type'
	:type filters: List[str]
	:param collection_name: Choose database name in local mongodb client. Default name is "collection"
	:type collection_name: str

	:return: Return a list with all transistor objects fitting to the search-filter
	:rtype: list

	:Example:

	>>> import transistordatabase as tdb
	>>> tdb.print_tdb()
	"""

unittesting with pytest
-----------------------
* separate functions should be tested completely

update the changelog
--------------------
Write in what changes for the end user of the package. This is for example
* important change in a parameter passing of a function
* Bugfixes, if possible with link to the issue



Install and setup pytest
************************

A good developer always writes test cases after he/she develop a new feature or add a new function
to the existing ones. The test cases determine if different features within a system are performing as expected and can also help reveal errors or defects within the system.
Unit testing methodology is adopted in this work and is achieved using ``pytest`` framework.

Configuring Pycharm
-------------------

Add pytest package from Python Package tool window or by running the following command in terminal.

.. code-block::

    pip install pytest

.. note::
    
    To ensure all pytest-specific features are available, set the test runner manually:
    press ``Ctrl+Alt+S`` to open the IDE settings and select Tools | Python Integrated Tools,
    and then select pytest from the Default test runner list.

Writing a test case
-------------------

* Navigate to method or class for which you want to create the test case and perform a right click.

* From the context menu, choose Go To | Test

* PyCharm shows the list of available tests

* To add one select Create New Test

* Pycharm navigates to test_databaseclasses.py and adds the testscase for the choosen method with a prefix ``'test'``

* While writing tests make use of my_transistor fixture to generate transistor object. Modifying this fixture is **not recommended** as it can affect other test cases

More information on how to write test cases using pytest can be inferred from `here <https://www.jetbrains.com/help/pycharm/pytest.html>`__.

.. note::

    The test case name should be either of ``test_methodname`` or ``methodname_test`` format for pycharm to associate the test case
    with respective method that needs to be tested.


Install and setup Sphinx
************************

Documentation is generated by Sphinx, and Sphinx reads the docstrings inside the code. Make sure to keep the docstrings up-to-date when making a change!
Sphinx uses autodoc extension which generates documentation automatically by reading the docstrings.
The docstrings can be written in rst file format whereas other formats like google docstrings are also available.

Find a rst and sphinx cheat sheet `here <https://sphinx-tutorial.readthedocs.io/cheatsheet/>`__.

Step 1: Use `sphinx-quickstart <https://www.sphinx-doc.org/en/master/man/sphinx-quickstart.html>`_ feature of sphinx which will setup the required files.

Step 2: Configure the conf.py file with necessary extensions.

Step 3: Create the necessary .rst files like _introduction, installation, transistordatabase and add the tree structure in index.rst.

Step 4: Point to folder where Makefile exists and execute command **"make html"** to generate documentation. The generated HTML files will be placed under build\html folder.

For generating multiversion documentation, py module ``sphinx-multiversion`` is used and added as extension in conf.py.
Further steps about configuring the project to enable multiversioning documentation can be found `here <https://holzhaus.github.io/sphinx-multiversion/master/quickstart.html>`__.

Install Sphinx for this repository. It is useful, to install this inside a virtual environment.

.. code-block::

    python3 -m pip install sphinx sphinx-multiversion sphinx_rtd_theme sphinxcontrib-email



Release Workflow
****************

Update version strings
----------------------

Version strings need to be updated in
 * setup.py
 * docs/conf.py
 * __init__.py
 * Changelog.md

Make sure that new functions/methods/classes are included to the documentation
------------------------------------------------------------------------------

The text file docs/transistordatabase.rst contains all functions that will be shown in the documentation build by sphinx. Make sure that this list ist up-to-date when releasing a new version.

Build a local test-documentation
--------------------------------

First, generate the sphinx documentation for the current version to see if this runs without any errors.
Go to /docs and runs

.. code-block::

    make html

Make sure the html-generation works without errors and visit the generated file inside /spinx/build/html/index.html

.. code-block::

    make clean

Next, generate the sphinx-multiversion documentation for all available versions and see if this runs without any errors.

.. code-block::

    sphinx-multiversion sphinx docs/build/html

Make sure the html-generation works without errors and visit the generated file inside /docs/build/html/main/index.html

.. note::

    Maybe there is a bug in some older versions, because this workflow was introduced only with the passing of time and thus non-error free builds exist in older versions.

Generate requirements.txt
-------------------------

File 'requirements.txt' is auto generated by pipreqs. To install pipreqs, do the following

.. code-block::

    pip install pipreqs

Generate the 'requirements.txt'-file

.. code-block::

    pipreqs /home/project/location/transistor_database

Further information can be found `here <https://pypi.org/project/pipreqs/>`__.

Generate pip-package by using setup.py
--------------------------------------

Some useful links
 * `classifiers <https://pypi.org/classifiers/>`_.

Run setup.py as the following from your operating system command line

.. code-block::

    python3 setup.py bdist_wheel

Please find the generated pip package inside the /dist-folder. |br|

Test the pip package from local installation before uploading.

.. code-block::

    python3 -m pip install transistordatabase-x.x.x-py3-none-any.whl

Upload pip package to pypi
--------------------------

Run this from your operating system command line

.. code-block::

    twine upload --repository pypi dist/*

create a git release and upload it to github
--------------------------------------------

Easiest way is to use `GPGit <https://github.com/NicoHood/GPGit>`_. This tool helps you in all steps. Example to generate the 0.1.3-release and upload it to github:

.. code-block::

    gpgit 0.1.3

generate sphinx documentation on github pages
---------------------------------------------

.. code-block::

    # make sure to clean up old build data
    cd docs/
    make clean
    cd ..
    sphinx-multiversion sphinx docs/build/html
    # write the new documentation to github-pages
    git checkout gh-pages
    # now, copy the files from docs/build/html to the gh-pages repository
    git add #newChangesHere
    git commit -m "update docu"
    git push
    # change back to the main branch
    git checkout main
    # clean up old build data
    cd docs
    make clean

.. |br| raw:: html

      <br>

generate executable file with all dependencies to run the GUI
-------------------------------------------------------------


* Step 1: install auto-py-to-exe via the "pip install auto-py-to-exe" command (https://pypi.org/project/auto-py-to-exe/)
* Step 2: run auto-py-to-exe and select the follwing files: 
    - Script Location: "...transistordatabase/transistordatabase/gui/gui.py"
    - choose 'One File' and 'Window Based (hide the console)'
    - Add Files: all files in the directory "...transistordatabase/transistordatabase/gui" (except gui.py) that are associated with the GUI
    - Add Files: "housing_types.txt" and "module manufacturers.txt" in the directory "...transistordatabase/transistordatabase"
    - Add Directory: "...transistordatabase/transistordatabase"
* Step 3: Click the button "CONVERT .PY TO .EXE" (all other settings can be left at default)

If an error message occurs when trying to run "gui.exe" that a certain python package is missing install the package via the "pip install" command and try to generate the .exe again (you may need to restart auto-py-to-exe since it will not work otherwise sometimes)





