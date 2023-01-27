# Python standard libraries
from enum import Enum

# Local libraries
from transistordatabase.transistor import Transistor
from transistordatabase.mongodb_handling import connect_local_tdb

class OperationMode(Enum):
    JSON_FILES = "json_files"
    SQLITE = "sqlite"
    MONGODB = "mongodb" # Shall be deprecated

class DatabaseManager:
    """This class shall manage the whole transistor database. It represents the whole database as an object and contains
    every needed information.
    Imports/exports as well as the interface to the gui shall be managed by this class

    This manager shall know 2 operation modes:
    1. Database saved as json files
    2. Database saved in a "real" Database (most likely sqlite?)
    3. Database saved like in previously in a mongodb database

    It shall abstract the operation mode from the external users (such as the gui or a possible python code interface which then can easily be implemented)
    """
    operation_mode: OperationMode

    def __init__(self, operation_mode: OperationMode):
        self.set_operation_mode(operation_mode)

    def set_operation_mode(self, operation_mode):
        self.operation_mode = operation_mode

        if self.operation_mode == OperationMode.JSON_FILES:
            pass
        elif self.operation_mode == OperationMode.SQLITE:
            pass
        elif self.operation_mode == OperationMode.MONGODB:
            pass
            
    def save_transistor(transistor: Transistor):
        pass

    def delete_transistor(transistor_id: int):
        pass

    def load_transistor(transistor_id: int):
        pass

    def get_transistor_names_list(self):
        """Returns a list containing every transistor name
        """
        if self.operation_mode == OperationMode.JSON_FILES:
            pass
        elif self.operation_mode == OperationMode.SQLITE:
            pass
        elif self.operation_mode == OperationMode.MONGODB:
            mongodb_collection = connect_local_tdb()
            returned_cursor = mongodb_collection.find()
            name_list = []
            for tran in returned_cursor:
                name_list.append(tran['name'])

            return name_list