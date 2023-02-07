# Python standard libraries
from enum import Enum
from typing import List, Tuple
import numpy as np
import os
import json
import re
import uuid

# Local libraries
from transistordatabase.transistor import Transistor
from transistordatabase.mongodb_handling import connect_local_tdb, drop_local_tdb

class OperationMode(Enum):
    JSON = "json"
    SQLITE = "sqlite"
    MONGODB = "mongodb" # Shall be deprecated?

class DatabaseManager:
    """This class shall manage the whole transistor database. It represents the whole database as an object and contains
    every needed information.
    Imports/exports as well as the interface to the gui shall be managed by this class

    This manager shall know 2 operation modes:
    1. Database saved as multilple json files
    2. Database saved in a "real" Database (most likely sqlite?)
    3. Database saved like in previously in a mongodb database

    It shall abstract the operation mode from the external users (such as the gui or a possible python code interface which then can easily be implemented)
    """
    operation_mode: OperationMode
    # mongodb_collection which type?

    def __init__(self):
        self.operation_mode = None

    def __del__(self):
        if self.operation_mode == OperationMode.MONGODB:
            drop_local_tdb()

    def set_operation_mode_json(self, json_folder_path: str) -> None:
        """
        Sets operation mode to json. In order to function properly it is necessary that the given folder path
        is empty and is only used by this database.

        :param json_path: Path to json folder.
        :type json_path: str
        """
        if self.operation_mode is not None:
            raise Exception("DatabaseManager operation mode can only be set once.")
        self.operation_mode = OperationMode.JSON

        if not os.path.isdir(json_folder_path):
            os.makedirs(json_folder_path)

        self.json_folder = json_folder_path

    def set_operation_mode_sqlite(self, db_path: str) -> None:
        """
        Sets the operation mode to sqlite database.

        :param db_path: File path to the sqlite file.
        :type db_path: str
        """
        if self.operation_mode is not None:
            raise Exception("DatabaseManager operation mode can only be set once.")
        self.operation_mode = OperationMode.SQLITE

        # TODO Set sqlite path
        raise Exception("Not implemented yet.")

    def set_operation_mode_mongodb(self, collection: str = "local") -> None:
        """
        Sets the operation mode to mongodb database.

        :param collection: By default local database is selected and "local" is provided as value
        :type collection: str
        """
        if self.operation_mode is not None:
            raise Exception("DatabaseManager operation mode can only be set once.")
        self.operation_mode = OperationMode.MONGODB

        if collection == "local":
            self.mongodb_collection = connect_local_tdb()
        else:
            raise Exception("Currently only collection == local is supported.")
            
    def save_transistor(self, transistor: Transistor, overwrite: bool = None) -> None:
        """
        The method save the transistor object to the desired database depending on the set operation mode.
        Currently receives the execution instructions from update_from_fileexchange(..)

        :param transistor: The transistor object which shall be stored in the database.
        :type collection: Transistor
        :param overwrite: Indicates whether to overwrite the existing transistor object in the local database if a match is found
        :type overwrite: bool or None
        """
        if self.operation_mode == None:
            raise Exception("Please select an operation mode for the database manager.")

        transistor_dict = transistor.convert_to_dict()

        if self.operation_mode == OperationMode.JSON:
            transistor_path = os.path.join(self.json_folder, f"{transistor.id}-{transistor.name}.json")
            if str(transistor.id) in os.listdir(self.json_folder):
                if overwrite is None:
                    print(f"A transistor object with id {transistor.id} already exists. \
                    If you want to override it please set the override argument to true, if you want to create a copy with a \
                    different id please set it to false")
                    return
                if overwrite:
                    with open(transistor_path, "w") as fd:
                        json.dump(transistor_dict, fd, indent=2)
                else:
                    new_id = uuid.uuid4()
                    name = transistor_dict["name"]
                    transistor_dict["id"] = new_id
                    with open(os.path.join(self.json_folder, f"{new_id}-{name}.json")):
                        json.dump(transistor_dict, fd, indent=2)
            else:
                with open(transistor_path, "w") as fd:
                    json.dump(transistor_dict, fd, indent=2)

        elif self.operation_mode == OperationMode.SQLITE:
            raise NotImplementedError("Current operation is not implemented.")
        elif self.operation_mode == OperationMode.MONGODB:
            if self.mongodb_collection.find_one({"_id": uuid.uuid4()}) is not None:
                if overwrite is None:
                    print(f"A transistor object with id {transistor.id} already exists in the database. \
                    If you want to override it please set the override argument to true, if you want to create a copy with a \
                    different id please set it to false")
                    return
                if overwrite:
                    self.mongodb_collection.replace_one({"_id": uuid.uuid4()}, transistor_dict)
                else:
                    del transistor_dict["_id"]
                    self.mongodb_collection.insert_one(transistor_dict)
            else:
                self.mongodb_collection.insert_one(transistor_dict)

    def delete_transistor(self, transistor_id: int) -> None:
        """
        Deletes the transistor with the given id from the database.

        :param transistor_id: Id of the transistor
        :type transistor_id: int
        """
        if self.operation_mode == None:
            raise Exception("Please select an operation mode for the database manager.")

        if self.operation_mode == OperationMode.JSON:
            existing_files = os.listdir(self.json_folder)
            for file in existing_files:
                if file.endswith(".json") and file.startswith(str(transistor_id)):
                    os.remove(os.path.join(self.json_folder, file))
            else:
                print(f"Can not find transistor with id {transistor_id} in the database. Therefore it cannot be deleted.")
        elif self.operation_mode == OperationMode.SQLITE:
            raise NotImplementedError("Current operation is not implemented.")
        elif self.operation_mode == OperationMode.MONGODB:
            if self.mongodb_collection.find_one({"_id": transistor_id}) is not None:
                self.mongodb_collection.delete_one({"_id": transistor_id})
            else:
                print(f"Can not find transistor with id {transistor_id} in the database. Therefore it cannot be deleted.")

    def load_transistor(self, transistor_id: int) -> Transistor:
        """
        Loads a transistor from the database. The database is determined by the operation mode.

        :param transistor_id: Id of the transistor
        :type transistor_id: int
        :return: Desired Transistor object
        :rtype: Transistor
        """
        if self.operation_mode == None:
            raise Exception("Please select an operation mode for the database manager.")

        if self.operation_mode == OperationMode.JSON:
            existing_files = os.listdir(self.json_folder)
            for file_name in existing_files:
                if file_name.endswith(".json") and file_name.startswith(str(transistor_id)):
                    with open(os.path.join(self.json_folder, f"{file_name}.json"), "r") as fd:
                        return DatabaseManager.convert_dict_to_transistor_object(json.load(fd))
            print(f"Transitor with id {transistor_id} not found.") 
        elif self.operation_mode == OperationMode.SQLITE:
            raise NotImplementedError("Current operation is not implemented.")
        elif self.operation_mode == OperationMode.MONGODB:
            return self.convert_dict_to_transistor_object(self.mongodb_collection.find_one({"_id": transistor_id}))

        return None

    def get_transistor_names_list(self) -> List[Tuple]:
        """
        Returns a list containing every transistor name and its id.

        :return: List containing the names and ids.
        :rtype:  List[Tuple(str, int)]
        """
        if self.operation_mode == None:
            raise Exception("Please select an operation mode for the database manager.")

        if self.operation_mode == OperationMode.JSON:
            transistor_list = []
            existing_files = os.listdir(self.json_folder)
            for file in existing_files:
                re_result = re.match("(\d+)-(\S+).json", file)
                transistor_id = re_result.group(1)
                transistor_name = re_result.group(2)
                transistor_list.append(tuple(transistor_name, transistor_id))

            return transistor_list
        elif self.operation_mode == OperationMode.SQLITE:
            pass
        elif self.operation_mode == OperationMode.MONGODB:
            transistor_list = []
            returned_cursor = self.mongodb_collection.find()
            for tran in returned_cursor:
                transistor_list.append((tran['name'], tran["_id"]))

            return transistor_list

        return None

    def print_tdb(self, filters: List[str] = None) -> List[str]:
        """
        Print all transistorelements stored in the local database

        :param filters: filters for searching the database, e.g. 'name' or 'type'
        :type filters: List[str]

        :return: Return a list with all transistor objects fitting to the search-filter
        :rtype: List
        """
        # Note: Never use mutable default arguments
        # see https://florimond.dev/en/posts/2018/08/python-mutable-defaults-are-the-source-of-all-evil/
        # This is the better solution
        filters = filters or []

        if not isinstance(filters, list):
            if isinstance(filters, str):
                filters = [filters]
            else:
                raise TypeError(
                    "The 'filters' argument must be specified as a list of strings or a single string but is"
                    f" {type(filters)} instead.")
        if "name" not in filters:
            filters.append("name")
        """Filters must be specified according to the respective objects they're associated with. 
        e.g. 'type' for type of Transistor or 'diode.technology' for technology of Diode."""
        if self.operation_mode == OperationMode.MONGODB:
            returned_cursor = self.mongodb_collection.find({}, filters)
            name_list = []
            for tran in returned_cursor:
                print(tran)
                name_list.append(tran['name'])
            return name_list
        elif self.operation_mode == OperationMode.JSON:
            raise Exception("Print tdb is currently not implemented for json operation mode")
        elif self.operation_mode == OperationMode.SQLITE:
            pass

    @staticmethod
    def export_single_transistor_to_json(transistor: Transistor, file_path: str):
        with open(file_path, "w") as fd:
            json.dump(transistor.convert_to_dict(), fd, indent=2)

    @staticmethod
    def convert_dict_to_transistor_object(transformer_dict: dict) -> Transistor:
        """
        Converts a dictionary to a transistor object.
        This is a helper function of the following functions:

        - parallel_transistors()
        - load()
        - import_json()

        :param db_dict: transistor dictionary
        :type db_dict: dict

        :return: Transistor object
        :rtype: Transistor object
        """
        # Convert transistor_args
        if 'c_oss' in transformer_dict and transformer_dict['c_oss'] is not None:
            for i in range(len(transformer_dict['c_oss'])):
                transformer_dict['c_oss'][i]['graph_v_c'] = np.array(transformer_dict['c_oss'][i]['graph_v_c'])
        if 'c_iss' in transformer_dict and transformer_dict['c_iss'] is not None:
            for i in range(len(transformer_dict['c_iss'])):
                transformer_dict['c_iss'][i]['graph_v_c'] = np.array(transformer_dict['c_iss'][i]['graph_v_c'])
        if 'c_rss' in transformer_dict and transformer_dict['c_rss'] is not None:
            for i in range(len(transformer_dict['c_rss'])):
                transformer_dict['c_rss'][i]['graph_v_c'] = np.array(transformer_dict['c_rss'][i]['graph_v_c'])
        if 'graph_v_ecoss' in transformer_dict and transformer_dict['graph_v_ecoss'] is not None:
            transformer_dict['graph_v_ecoss'] = np.array(transformer_dict['graph_v_ecoss'])
        if 'raw_measurement_data' in transformer_dict:
            for i in range(len(transformer_dict['raw_measurement_data'])):
                for u in range(len(transformer_dict['raw_measurement_data'][i]['dpt_on_vds'])):
                    transformer_dict['raw_measurement_data'][i]['dpt_on_vds'][u] = np.array(transformer_dict['raw_measurement_data'][i]['dpt_on_vds'][u])
                for u in range(len(transformer_dict['raw_measurement_data'][i]['dpt_on_id'])):
                    transformer_dict['raw_measurement_data'][i]['dpt_on_id'][u] = np.array(transformer_dict['raw_measurement_data'][i]['dpt_on_id'][u])
                for u in range(len(transformer_dict['raw_measurement_data'][i]['dpt_off_vds'])):
                    transformer_dict['raw_measurement_data'][i]['dpt_off_vds'][u] = np.array(transformer_dict['raw_measurement_data'][i]['dpt_off_vds'][u])
                for u in range(len(transformer_dict['raw_measurement_data'][i]['dpt_off_id'])):
                    transformer_dict['raw_measurement_data'][i]['dpt_off_id'][u] = np.array(transformer_dict['raw_measurement_data'][i]['dpt_off_id'][u])

        # Convert switch_args
        switch_args = transformer_dict['switch']
        if switch_args['thermal_foster']['graph_t_rthjc'] is not None:
            switch_args['thermal_foster']['graph_t_rthjc'] = np.array(switch_args['thermal_foster']['graph_t_rthjc'])
        for i in range(len(switch_args['channel'])):
            switch_args['channel'][i]['graph_v_i'] = np.array(switch_args['channel'][i]['graph_v_i'])
        for i in range(len(switch_args['e_on'])):
            if switch_args['e_on'][i]['dataset_type'] == 'graph_r_e':
                switch_args['e_on'][i]['graph_r_e'] = np.array(switch_args['e_on'][i]['graph_r_e'])
            elif switch_args['e_on'][i]['dataset_type'] == 'graph_i_e':
                switch_args['e_on'][i]['graph_i_e'] = np.array(switch_args['e_on'][i]['graph_i_e'])
        if 'e_on_meas' in switch_args:
            for i in range(len(switch_args['e_on_meas'])):
                if switch_args['e_on_meas'][i]['dataset_type'] == 'graph_r_e':
                    switch_args['e_on_meas'][i]['graph_r_e'] = np.array(switch_args['e_on_meas'][i]['graph_r_e'])
                elif switch_args['e_on_meas'][i]['dataset_type'] == 'graph_i_e':
                    switch_args['e_on_meas'][i]['graph_i_e'] = np.array(switch_args['e_on_meas'][i]['graph_i_e'])
        for i in range(len(switch_args['e_off'])):
            if switch_args['e_off'][i]['dataset_type'] == 'graph_r_e':
                switch_args['e_off'][i]['graph_r_e'] = np.array(switch_args['e_off'][i]['graph_r_e'])
            elif switch_args['e_off'][i]['dataset_type'] == 'graph_i_e':
                switch_args['e_off'][i]['graph_i_e'] = np.array(switch_args['e_off'][i]['graph_i_e'])
        if 'e_off_meas' in switch_args:
            for i in range(len(switch_args['e_off_meas'])):
                if switch_args['e_off_meas'][i]['dataset_type'] == 'graph_r_e':
                    switch_args['e_off_meas'][i]['graph_r_e'] = np.array(switch_args['e_off_meas'][i]['graph_r_e'])
                elif switch_args['e_off_meas'][i]['dataset_type'] == 'graph_i_e':
                    switch_args['e_off_meas'][i]['graph_i_e'] = np.array(switch_args['e_off_meas'][i]['graph_i_e'])
        if 'charge_curve' in switch_args:
            for i in range(len(switch_args['charge_curve'])):
                switch_args['charge_curve'][i]['graph_q_v'] = np.array(switch_args['charge_curve'][i]['graph_q_v'])
        if 'r_channel_th' in switch_args:
            for i in range(len(switch_args['r_channel_th'])):
                switch_args['r_channel_th'][i]['graph_t_r'] = np.array(switch_args['r_channel_th'][i]['graph_t_r'])
        if 'soa' in switch_args:
            for i in range(len(switch_args['soa'])):
                switch_args['soa'][i]['graph_i_v'] = np.array(switch_args['soa'][i]['graph_i_v'])

        # Convert diode_args
        diode_args = transformer_dict['diode']
        if diode_args['thermal_foster']['graph_t_rthjc'] is not None:
            diode_args['thermal_foster']['graph_t_rthjc'] = np.array(diode_args['thermal_foster']['graph_t_rthjc'])
        for i in range(len(diode_args['channel'])):
            diode_args['channel'][i]['graph_v_i'] = np.array(diode_args['channel'][i]['graph_v_i'])
        for i in range(len(diode_args['e_rr'])):
            if diode_args['e_rr'][i]['dataset_type'] == 'graph_r_e':
                diode_args['e_rr'][i]['graph_r_e'] = np.array(diode_args['e_rr'][i]['graph_r_e'])
            elif diode_args['e_rr'][i]['dataset_type'] == 'graph_i_e':
                diode_args['e_rr'][i]['graph_i_e'] = np.array(diode_args['e_rr'][i]['graph_i_e'])
        if 'soa' in diode_args:
            for i in range(len(diode_args['soa'])):
                diode_args['soa'][i]['graph_i_v'] = np.array(diode_args['soa'][i]['graph_i_v'])

        return Transistor(transformer_dict, switch_args, diode_args)
