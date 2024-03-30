"""This shall be an example file to test the new refactored class structure."""
# Python standard libraries
import os

# Local libraries
from transistordatabase.database_manager import DatabaseManager

def extract_from_mongodb_to_json():
    """Extract transistors from the mongo-database to single json-files."""
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
    """Add transistors from json files to the mongo-db database."""
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
    """Show the json database operation mode (recommended)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tdb_example")
    tdb_json = DatabaseManager()
    tdb_json.set_operation_mode_json(path)
    tdb_json.print_tdb()

def example_mongodb_database():
    """Show the mongo-db operation mode (optional, not recommended)."""
    tdb_mongodb = DatabaseManager()
    tdb_mongodb.set_operation_mode_mongodb()
    tdb_mongodb.print_tdb()

def example_update_from_online_database():
    """Update the local database from the online database."""
    # handle the path to the DatabaseManager(path), to handle a custom database folder to the manager.
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tdb_example_downloaded")
    db = DatabaseManager()
    db.set_operation_mode_json(path)
    db.update_from_fileexchange(True)

    # Compare local database to exchange database:
    # diff_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diff.json")
    # db.compare_with_fileexchange(index_url, diff_file)


if __name__ == "__main__":
    # extract_from_mongodb_to_json()
    # example_json_database()
    # example_mongodb_database()
    # insert_mongodb_from_json()
    example_update_from_online_database()
