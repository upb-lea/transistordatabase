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

def example_json_database():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tdb_example")
    tdb_json = DatabaseManager()
    tdb_json.set_operation_mode_json(path)
    tdb_json.print_tdb()

if __name__ == "__main__":
    #extract_from_mongodb_to_json()
    example_json_database()

