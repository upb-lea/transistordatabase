"""
This shall be an example file to test the new refactored class structure
"""
# Python standard libraries
import os

# Local libraries
from transistordatabase.transistor import Transistor
from transistordatabase.database_manager import DatabaseManager

if __name__ == "__main__":
    tdb = DatabaseManager()
    tdb.set_operation_mode_mongodb()
    transistor_names = tdb.get_transistor_names_list()
    
    transistors = []
    for transistor in transistor_names:
        transistors.append(tdb.load_transistor(transistor[1]))

    cwd = os.path.dirname(os.path.abspath(__file__))
    tdb_json = DatabaseManager()
    tdb_json.set_operation_mode_json(os.path.join(cwd, "tdb_example"))
    
    for transistor in transistors:
        transistor.id = id(Transistor)
        tdb_json.save_transistor(transistor)


