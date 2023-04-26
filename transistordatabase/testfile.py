from transistordatabase.transistor import Transistor as tdb
from transistordatabase.database_manager import DatabaseManager
import numpy as np
import pandas as pd
import csv
import matplotlib.pyplot as plt
import os
# update the database from the online git-repository
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tdb_example_downloaded")
db = DatabaseManager()
db.set_operation_mode_json(path)
db.update_from_fileexchange(True)

# print the database
#tdb.print_tdb()

# load a transistor from the database
transistor_loaded = db.load_transistor('GaNSystems_GS66506T')
#transistor_loaded.raw_measurement_data_plots()
transistor_loaded.export_datasheet()