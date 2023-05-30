from transistordatabase.transistor import Transistor as tdb
from transistordatabase.database_manager import DatabaseManager
import numpy as np
import pandas as pd
import csv
import matplotlib.pyplot as plt
import os
from pathlib import Path
import os,json
import time

file_list = list(Path("C:/Users/sarim/OneDrive/Desktop/project2/transistordatabase/transistordatabase/tdb_example_downloaded").glob("*.json"))
#print(file_list)


# update the database from the online git-repository
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tdb_example_downloaded")
db = DatabaseManager()
db.set_operation_mode_json(path)
db.update_from_fileexchange(True)

# print the database
#tdb.print_tdb()
transistor_loaded = db.load_transistor("ROHMSemiconductor_SCT3120AW7")
#transistor_loaded.raw_measurement_data_plots()
transistor_loaded.export_datasheet()

# load a transistor from the database
##print(file_list)
json_file_name = []
""" for i in file_list:
    print("Here",Path(i).stem)
    json_file_name.append(Path(i).stem)
for j in json_file_name:
    print(j)
    transistor_loaded = db.load_transistor(j)
    #transistor_loaded.raw_measurement_data_plots()
    transistor_loaded.export_datasheet()
    time.sleep(1) """

