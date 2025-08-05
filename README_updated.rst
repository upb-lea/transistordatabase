.. sectnum::

###########################
Transistordatabase
###########################

The Transistordatabase is a comprehensive tool developed by LEA from the University Paderborn for working with power electronics transistors. 
When it comes to choosing transistors for electronics development, there's typically trouble with different programs and compatibility issues between tools.
The Transistordatabase solves this problem by providing a unified platform for storing, managing, and exporting transistor data across multiple simulation environments.

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/sphinx/images/Why_transistordatabase.png
    :align: center
    :alt: Why transistor database?

🆕 **New Web Interface Available!** - Access the database through a modern web browser with advanced search, visualization, and export capabilities.

Functionality overview
***********************

Here are some examples on the functionality of the Transistordatabase:

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/sphinx/images/Workflow.png
    :align: center
    :alt: Workflow

* 🌐 **Modern Web Interface**: Browse and manage transistors through an intuitive web application
* 📊 **Advanced Search & Filtering**: Find transistors by electrical properties, manufacturer, type, and custom criteria
* 📈 **Interactive Visualizations**: Plot transistor characteristics with Chart.js integration
* 🧮 **Topology Calculator**: Built-in power converter analysis (Buck, Boost, Buck-Boost)
* 📤 **Multi-Format Export**: Export to MATLAB, Simulink, PLECS, GeckoCIRCUITS, SPICE, and JSON
* 🔍 **Transistor Comparison**: Side-by-side analysis with performance metrics
* 🐍 **Python API**: Programmatic access for automation and optimization routines
* 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
* 🌙 **Dark/Light Theme**: Customizable interface themes
* 🔄 **Real-time Updates**: Live data synchronization between interface and database

.. note::
    Development status: **Beta** - Web interface available with full feature parity to desktop GUI


###########################
Features
###########################

The Transistordatabase now offers **two primary interfaces** plus programmatic access:

🌐 Web Interface (New!)
*******************************

**Modern Vue.js web application with FastAPI backend**

* **🔍 Advanced Search Database**: 
  - Multi-criteria filtering (voltage, current, power, temperature)
  - Manufacturer and type selection
  - Range-based property filtering
  - Quick filter presets
  - Pagination and sorting

* **📤 Professional Export Tools**:
  - MATLAB/Simulink model generation
  - PLECS XML thermal models
  - GeckoCIRCUITS circuit files
  - SPICE netlist generation
  - JSON data export
  - Export history and re-export functionality

* **🧮 Topology Calculator**:
  - Buck converter design and analysis
  - Boost converter optimization
  - Buck-Boost converter calculations
  - Power loss analysis
  - Efficiency optimization
  - Interactive circuit diagrams
  - Transistor recommendations

* **🔍 Comparison Tools**:
  - Side-by-side transistor analysis
  - Performance metric comparison
  - Interactive charts and graphs
  - Export comparison results

* **📊 Database Management**:
  - Real-time statistics
  - Import/export database
  - Data validation
  - Bulk operations

Access the web interface at: ``http://localhost:5174`` (after setup)

🖥️ Desktop GUI (PyQt5)
*******************************

Traditional desktop application with comprehensive transistor management:

* Manage, store and search transistors
* Export transistor models to simulation programs
* Compare transistors (interpolate switch loss data for new gate resistors and temperatures)
* Visual datasheet generation

Here are some screenshots of the desktop GUI:

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/sphinx/images/gui_database.png
    :align: center
    :alt: gui_database

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/sphinx/images/gui_comparison.png
    :align: center
    :alt: gui_comparison

🐍 Python API
*******************************

Programmatic access for custom applications and optimization:

* Automatic converter loss calculations with multiple transistors
* Database search for application-specific transistors
* Functions for closest operating point search
* Transistor/diode conduction behavior linearization
* Output capacitance energy calculation from C_oss curves
* Integration with optimization routines

.. image:: https://raw.githubusercontent.com/upb-lea/transistordatabase/main/sphinx/documentation/workflow_wp.png
    :align: center
    :alt: optimization

🔄 Transistordatabase File Exchange
***********************************

`This <https://github.com/upb-lea/transistordatabase_File_Exchange>`__ repository contains transistors for automatic download to your local database.
The web interface provides seamless integration with the file exchange for easy database updates.


############
Installation
############

🌐 Web Interface Setup (Recommended)
************************************

**Prerequisites:**
- Python 3.8+ with pip
- Node.js 16+ with npm

**Quick Start:**

1. **Clone and setup backend:**

.. code-block:: bash

   cd transistordatabase/gui_web/backend
   pip install fastapi uvicorn python-multipart
   python main_simple.py

2. **Setup frontend:**

.. code-block:: bash

   cd ../  # Back to gui_web directory
   npm install
   npm run dev

3. **Access the application:**
   - Web Interface: http://localhost:5174
   - API Documentation: http://localhost:8002/docs

🖥️ Desktop Application
***********************

Windows
-------

**Install Python:**
Install latest Python version: `Link <https://www.python.org/>`__.

**Install PyCharm (optional):**
`Installation file <https://www.jetbrains.com/pycharm/download/download-thanks.html?platform=linux&code=PCC>`_.

**Download and run executable:**
Download exe-file `here <https://groups.uni-paderborn.de/lea/public/downloads/transistordatabase.zip>`_

Linux
-----
Ubuntu:

.. code-block:: bash

   sudo apt install python3 python3-pip

.. note::
    Install PyCharm from Snapstore

🐍 Python Package Installation
*******************************

Install via pip:

.. code-block:: bash

   pip install transistordatabase

Or for development:

.. code-block:: bash

   git clone https://github.com/upb-lea/transistordatabase.git
   cd transistordatabase
   pip install -e .


##########################
Usage
##########################

🌐 Web Interface Usage
**********************

1. **Start the application** (see installation steps above)
2. **Navigate to http://localhost:5174**
3. **Explore the 5-tab interface:**
   - 🔍 **Search Database**: Find and filter transistors
   - ➕ **Create Transistor**: Add new transistor data
   - 📤 **Exporting Tools**: Export to various formats
   - 🔍 **Comparison Tools**: Compare multiple transistors
   - 🧮 **Topology Calculator**: Design power converters

4. **Key Features:**
   - Use advanced filters to find suitable transistors
   - Export data to your preferred simulation tool
   - Calculate optimal operating points
   - Compare transistor performance
   - Switch between light/dark themes

🐍 Python API Usage
*******************

**Minimal example:**

.. code-block:: python

    from transistordatabase.database_manager import DatabaseManager
    import os

    # Path for json files
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")

    # Create DatabaseManager instance
    tdb_json = DatabaseManager()
    tdb_json.set_operation_mode_json(path)

    # Print database contents
    tdb_json.print_tdb()

    # Load a specific transistor
    transistor = tdb_json.load_transistor('CREE_C3M0016120K')
    
    # Use transistor in calculations
    transistor.quickstart_wp()  # Auto-fill working point
    print(f"On-resistance: {transistor.wp.switch_r_channel}")

**Advanced usage with web API:**

.. code-block:: python

    import requests
    
    # Get all transistors via API
    response = requests.get('http://localhost:8002/transistors')
    transistors = response.json()
    
    # Search for specific transistors
    search_params = {
        'manufacturer': 'CREE',
        'min_voltage': 1000,
        'max_current': 100
    }
    filtered = requests.get('http://localhost:8002/transistors/search', params=search_params)

🔧 Generate New Transistors
***************************

**Transistor Object Structure:**
Transistor
├── Metadata
├── Switch
│   ├── Switch Metadata
│   ├── Channel Data
│   └── Switching Data
├── Diode
│   ├── Diode Metadata
│   ├── Channel Data
│   └── Switching Data
└── wp (working point for calculations)

**Reading Datasheet Curves:**
Use `WebPlotDigitizer <https://apps.automeris.io/wpd/>`_ to extract data from datasheets.

**Template Usage:**
See the `template example </template_example/template_example.py>`_ for creating new transistor objects.

Important lists for consistency:
* `Manufacturers <https://github.com/upb-lea/transistordatabase/blob/main/transistordatabase/module_manufacturers.txt>`_
* `Housing Types <https://github.com/upb-lea/transistordatabase/blob/main/transistordatabase/housing_types.txt>`_

📤 Export Capabilities
**********************

**Supported Export Formats:**

* **MATLAB/Simulink**: .mat files for loss modeling
* **PLECS**: XML thermal models for power simulation
* **GeckoCIRCUITS**: Circuit simulation files
* **SPICE**: Netlist generation for circuit analysis
* **JSON**: Raw data export for custom applications
* **Virtual Datasheet**: HTML documentation

**Export via Web Interface:**
1. Navigate to "Exporting Tools" tab
2. Select transistors and format
3. Configure export options
4. Download generated files

**Export via Python:**

.. code-block:: python

    # Load transistor
    transistor = tdb.load_transistor('CREE_C3M0016120K')
    
    # Export to different formats
    transistor.export_plecs()                    # PLECS XML
    transistor.export_simulink_loss_model()      # Simulink .mat
    transistor.export_geckocircuits(True, 600, 15, -4, 2.5, 2.5)  # GeckoCIRCUITS
    transistor.export_matlab()                   # MATLAB .mat
    transistor.export_datasheet()               # Virtual datasheet

🧮 Topology Calculator Usage
****************************

The web interface includes a built-in topology calculator for common power converter designs:

**Supported Topologies:**
- Buck Converter (Step-down)
- Boost Converter (Step-up)  
- Buck-Boost Converter (Inverting)

**Features:**
- Input parameter specification (voltage, current, frequency)
- Automatic component calculations
- Power loss analysis
- Efficiency optimization
- Transistor recommendations from database
- Interactive circuit diagrams
- Results visualization with charts

**Usage:**
1. Navigate to "Topology Calculator" tab
2. Select converter topology
3. Enter design parameters
4. Run calculations
5. Review recommendations and analysis


##########################
API Documentation
##########################

🌐 REST API Endpoints
*********************

The FastAPI backend provides comprehensive REST endpoints:

**Base URL:** ``http://localhost:8002``

**Key Endpoints:**
- ``GET /transistors`` - List all transistors
- ``GET /transistors/{id}`` - Get specific transistor
- ``POST /transistors/search`` - Advanced search
- ``POST /transistors/upload`` - Upload transistor data
- ``GET /transistors/export/{format}`` - Export transistors
- ``POST /topology/calculate`` - Converter calculations

**Interactive Documentation:**
Visit ``http://localhost:8002/docs`` for Swagger UI with live API testing.


##########################
Complete Documentation
##########################

The complete documentation can be found `here <https://upb-lea.github.io/transistordatabase/main/transistordatabase.html>`__.


#######
Others
#######

🚀 Roadmap
**********

**2024-2025 Focus:**
- ✅ Modern web interface with Vue.js/FastAPI
- ✅ Advanced search and filtering capabilities  
- ✅ Multi-format export tools
- ✅ Topology calculator integration
- ✅ Responsive design and dark/light themes
- 🔄 Enhanced self-measured data integration
- 🔄 Machine learning-based transistor recommendations
- 🔄 Cloud deployment and collaborative features
- 🔄 Mobile app development
- 🔄 Advanced optimization algorithms

🐛 Bug Reports & Contributing
****************************

**Bug Reports:**
Please use the GitHub issues: https://github.com/upb-lea/transistordatabase/issues

**Contributing:**
Pull requests welcome! See `Contributing Guide <https://github.com/upb-lea/transistordatabase/blob/main/Contributing.rst>`_.

**Changelog:**
Find the changelog `here <https://github.com/upb-lea/transistordatabase/blob/main/CHANGELOG.md>`__.

📞 Contact & Community
**********************

- **GitHub**: https://github.com/upb-lea/transistordatabase
- **Email**: tdb@lea.upb.de
- **Documentation**: https://upb-lea.github.io/transistordatabase/
- **File Exchange**: https://github.com/upb-lea/transistordatabase_File_Exchange

🏛️ About
********

**History:**
Started in 2020 as a MATLAB project, evolved to Python for open-source accessibility. 
- 2021: First Python alpha and pip package
- 2022: Desktop GUI with PyQt5
- 2024: Modern web interface with Vue.js/FastAPI
- 2025: Advanced topology calculator and comparison tools

**License:**
Licensed under `GPLv3 <https://choosealicense.com/licenses/gpl-3.0/>`_

**University Partnership:**
Developed by the Power Electronics and Electrical Drives Group (LEA) at the University of Paderborn, Germany.


.. |br| raw:: html

      <br>
