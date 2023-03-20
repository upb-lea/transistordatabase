"""
This shall be an example file to test the new refactored class structure
"""
# Python standard libraries
import os

# Local libraries
from transistordatabase.transistor import Transistor
from transistordatabase.database_manager import DatabaseManager

def extract_from_mongodb_to_json():
    tdb = DatabaseManager()
    tdb.set_operation_mode_mongodb()
    transistor_names = tdb.get_transistor_names_list()
    
    transistors = []
    for transistor in transistor_names:
        transistors.append(tdb.load_transistor(transistor))

    cwd = os.path.dirname(os.path.abspath(__file__))
    tdb_json = DatabaseManager()
    tdb_json.set_operation_mode_json(os.path.join(cwd, "tdb_example"))
    
    for transistor in transistors:
        tdb_json.save_transistor(transistor, overwrite=False)

def insert_mongodb_from_json():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tdb_example")
    tdb_json = DatabaseManager()
    tdb_json.set_operation_mode_json(path)
    transistor_names = tdb_json.get_transistor_names_list()

    transistors = []
    for transistor in transistor_names:
        transistors.append(tdb_json.load_transistor(transistor))

    tdb_mongodb = DatabaseManager()
    tdb_mongodb.set_operation_mode_mongodb()
    for transistor in transistors:
        tdb_mongodb.save_transistor(transistor)

def example_json_database():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tdb_example")
    tdb_json = DatabaseManager()
    tdb_json.set_operation_mode_json(path)
    tdb_json.print_tdb()

def example_mongodb_database():
    tdb_mongodb = DatabaseManager()
    tdb_mongodb.set_operation_mode_mongodb()
    tdb_mongodb.print_tdb()

def example_update_from_online_database():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tdb_example_downloaded")
    index_url = r"https://raw.githubusercontent.com/upb-lea/transistordatabase_File_Exchange/main/index.txt"
    module_manufacturers_url = r"https://raw.githubusercontent.com/upb-lea/transistordatabase_File_Exchange/main/module_manufacturers.txt"
    housing_types_url = r"https://raw.githubusercontent.com/upb-lea/transistordatabase_File_Exchange/main/housing_types.txt"
    db = DatabaseManager()
    db.set_operation_mode_json(path)
    db.update_from_fileexchange(index_url, True, module_manufacturers_url, housing_types_url)

if __name__ == "__main__":
    #extract_from_mongodb_to_json()
    #example_json_database()
    #example_mongodb_database()
    #insert_mongodb_from_json()
    example_update_from_online_database()

