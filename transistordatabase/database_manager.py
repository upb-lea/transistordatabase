"""Manage the database with its different operation modes (json and mongodb)."""
# Python standard libraries
from enum import Enum
from datetime import datetime
from matplotlib import pyplot as plt
import numpy as np
import os
import json
import requests
import deepdiff
import glob  # Can this be removed?
import logging

# Local libraries
from transistordatabase.transistor import Transistor
from transistordatabase.mongodb_handling import connect_local_tdb 
from transistordatabase.helper_functions import get_copy_transistor_name, isvalid_transistor_name, read_data_file, html_to_pdf, get_xml_data, compare_list
from transistordatabase.checker_functions import check_float

logger = logging.getLogger(__name__)

class OperationMode(Enum):
    """Operation mode definitions."""

    JSON = "json"
    MONGODB = "mongodb"

class DatabaseManager:
    """
    Base class of the transistordatabase.

    After creation, a operation mode must be set (either JSON or MongoDB) and
    then from the DatabaseManager the Transistor data can be accessed.
    """

    operation_mode: OperationMode
    tdb_directory: str

    housing_types: list[str]
    module_manufacturers: list[str]

    module_manufacturers_file_path: str
    housing_types_file_path: str
    
    def __init__(self, housing_types_file_path: str = None, module_manufacturers_file_path: str = None):
        self.operation_mode = None
        self.tdb_directory = os.path.dirname(os.path.abspath(__file__))

        # Load housing_types and module_manufacturers
        if housing_types_file_path is None:
            self.housing_types_file_path = os.path.join(self.tdb_directory, "data", "housing_types.txt")
        else:
            self.housing_types_file_path = housing_types_file_path
        self.housing_types = read_data_file(self.housing_types_file_path)

        if module_manufacturers_file_path is None:
            self.module_manufacturers_file_path = os.path.join(self.tdb_directory, "data", "module_manufacturers.txt")
        else:
            self.module_manufacturers_file_path = module_manufacturers_file_path
        self.module_manufacturers = read_data_file(self.module_manufacturers_file_path)

    def set_operation_mode_json(self, json_folder_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")) -> None:
        """
        Set the database operation mode to json.

        Another operation mode is using mongodb as a database.

        In order to function properly it is necessary that the given folder path
        is empty and is only used by this database. If no path is given the transistordatabase will be created in the package folder.

        :param json_folder_path: Path to json folder.
        :type json_folder_path: str
        """
        index_url = "https://raw.githubusercontent.com/upb-lea/transistordatabase_File_Exchange/main/index.txt"
        if self.operation_mode is not None:
            raise Exception("DatabaseManager operation mode can only be set once.")
        self.operation_mode = OperationMode.JSON
        if not os.path.isdir(json_folder_path):
            os.makedirs(json_folder_path)
            self.json_folder = json_folder_path
            index_response = requests.get(index_url)
            logger.info(index_response)
            if not index_response.ok:
                raise Exception(f"Index file was not found. URL: {index_url}")
            for transistor_url in index_response.iter_lines():
                transistor_response = requests.get(transistor_url)
                logger.info(transistor_url)

                # filename = transistor_url.split('/')[-1].decode()
                filename = transistor_url.decode().split('/')[-1]
                logger.info(filename)
                if not transistor_response.ok:
                    logger.info(f"Transistor with URL {transistor_url} couldn't be downloaded. Transistor was skipped.")
                    continue
                else:
                    transistor = self.convert_dict_to_transistor_object(transistor_response.json())
                    self.save_transistor(transistor, True)
        else:
            self.json_folder = json_folder_path

    def set_operation_mode_mongodb(self, collection: str = "local") -> None:
        """
        Set the database operation mode to mongodb database.

        :param collection: By default, local database is selected and "local" is provided as value
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
        Save the transistor object to the desired database depending on the set operation mode.

        Receives the execution instructions from update_from_fileexchange(..).

        :param transistor: The transistor object which shall be stored in the database.
        :param overwrite: Indicates whether to overwrite the existing transistor object in the local database if a match is found
        :type overwrite: bool or None
        """
        if self.operation_mode is None:
            raise Exception("Please select an operation mode for the database manager.")

        transistor_dict = transistor.convert_to_dict()
        if "_id" in transistor_dict:
            del transistor_dict["_id"]
        if self.operation_mode == OperationMode.JSON:
            transistor_path = os.path.join(self.json_folder, f"{transistor.name}.json")
            if str(transistor.name) in os.listdir(self.json_folder):
                if overwrite is None:
                    logger.info(f"A transistor object with name {transistor.name} already exists. \
                    If you want to override it please set the override argument to true, if you want to create a copy with a \
                    different id please set it to false")
                    return
                if overwrite:
                    with open(transistor_path, "w") as fd:
                        json.dump(transistor_dict, fd, indent=2)
                else:
                    new_name = get_copy_transistor_name(transistor_dict["name"])
                    del transistor_dict["_id"]
                    with open(os.path.join(self.json_folder, f"{new_name}.json")):
                        json.dump(transistor_dict, fd, indent=2)
            else:
                with open(transistor_path, "w") as fd:
                    json.dump(transistor_dict, fd, indent=2)

        elif self.operation_mode == OperationMode.MONGODB:
            if self.mongodb_collection.find_one({"_id": transistor._id}) is not None:
                if overwrite is None:
                    logger.info(f"A transistor object with id {transistor._id} already exists in the database. \
                    If you want to override it please set the override argument to true, if you want to create a copy with a \
                    different id please set it to false")
                    return
                if overwrite:
                    self.mongodb_collection.replace_one({"_id": transistor._id}, transistor_dict)
                else:
                    del transistor_dict["_id"]
                    transistor_dict["name"] = get_copy_transistor_name(transistor_dict["name"])
                    self.mongodb_collection.insert_one(transistor_dict)
            else:
                self.mongodb_collection.insert_one(transistor_dict)

    def delete_transistor(self, transistor_name: str) -> None:
        """
        Delete the transistor with the given id from the database.

        :param transistor_name: Name of the transistor
        :type transistor_name: str
        """
        if self.operation_mode is None:
            raise Exception("Please select an operation mode for the database manager.")

        if self.operation_mode == OperationMode.JSON:
            existing_files = os.listdir(self.json_folder)
            for file in existing_files:
                if file.endswith(".json") and file[:-5] == transistor_name and isvalid_transistor_name(file[:-5]):
                    os.remove(os.path.join(self.json_folder, file))
            else:
                logger.info(f"Can not find transistor with name {transistor_name} in the database. Therefore it cannot be deleted.")
        elif self.operation_mode == OperationMode.MONGODB:
            if self.mongodb_collection.find_one({"name": transistor_name}) is not None:
                self.mongodb_collection.delete_one({"name": transistor_name})
            else:
                logger.info(f"Can not find transistor with name {transistor_name} in the database. Therefore it cannot be deleted.")

    def load_transistor(self, transistor_name: str) -> Transistor:
        """
        Load a transistor from the database. The database is determined by the operation mode.

        :param transistor_name: Name of the transistor
        :type transistor_name: str
        :return: Desired Transistor object
        :rtype: Transistor
        """
        if self.operation_mode is None:
            raise Exception("Please select an operation mode for the database manager.")

        if self.operation_mode == OperationMode.JSON:
            existing_files = os.listdir(self.json_folder)
            for file_name in existing_files:
                if file_name.endswith(".json") and file_name.startswith(str(transistor_name)) and isvalid_transistor_name(file_name[:-5]):
                    with open(os.path.join(self.json_folder, file_name), "r") as fd:
                        return self.convert_dict_to_transistor_object(json.load(fd))
            logger.info(f"Transitor with name {transistor_name} not found.")
        elif self.operation_mode == OperationMode.MONGODB:
            return self.convert_dict_to_transistor_object(self.mongodb_collection.find_one({"name": transistor_name}))

        return None

    def get_transistor_names_list(self) -> list[str]:
        """
        Return a list containing every transistor name.

        :return: List containing the names.
        :rtype:  list[str]
        """
        if self.operation_mode is None:
            raise Exception("Please select an operation mode for the database manager.")

        if self.operation_mode == OperationMode.JSON:
            transistor_list = []
            existing_files = os.listdir(self.json_folder)
            for file in existing_files:
                if isvalid_transistor_name(file[:-5]):
                    transistor_list.append(file[:-5])

            return transistor_list
        elif self.operation_mode == OperationMode.MONGODB:
            transistor_list = []
            returned_cursor = self.mongodb_collection.find()
            for tran in returned_cursor:
                transistor_list.append(tran['name'])

            return transistor_list

        return None

    def print_tdb(self, filters: list[str] = None) -> list[str]:
        """
        Print all transistor elements stored in the local database.

        :param filters: filters for searching the database, e.g. 'name' or 'type'
        :type filters: list[str]

        :return: Return a list with all transistor objects fitting to the search-filter
        :rtype: list
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
            returned_cursor = self.mongodb_collection.find({})
            transistor_list = []
            for tran in returned_cursor:
                transistor = self.convert_dict_to_transistor_object(tran)
                transistor_list.append(transistor)
            logger.info(transistor_list)
            return transistor_list
        elif self.operation_mode == OperationMode.JSON:
            all_transistor_names = self.get_transistor_names_list()
            transistor_list = []
            for transistor_name in all_transistor_names:
                transistor = self.load_transistor(transistor_name)
                transistor_list.append(transistor)
            logger.info(transistor_list)
            return transistor_list

    def update_from_fileexchange(self, overwrite: bool = True,
                                 index_url: str = "https://raw.githubusercontent.com/upb-lea/transistordatabase_File_Exchange/main/index.txt",
                                 module_manufacturers_url: str = \
                                 "https://raw.githubusercontent.com/upb-lea/transistordatabase_File_Exchange/main/module_manufacturers.txt",
                                 housing_types_url: str = \
                                 "https://raw.githubusercontent.com/upb-lea/transistordatabase_File_Exchange/main/housing_types.txt") -> None:
        """
        Update your local transistor database from transistordatabase-fileexchange from given index-file url.

        Also updates module manufacturers and housing types.
        If no index_url or module_manufacturers_url or housing_types_url is given the default Transistordatabase Fileexchange URLs are taken.
        
        :param index_url: URL to the index file which contains the links to all the transistor files (json formatted).
        :type index_url: str
        :param overwrite: True to overwrite existing transistor objects in local database, False to not overwrite existing transistor objects in local database.
        :type overwrite: bool
        :param module_manufacturers_url: URL to the module manufacturers file
        :type module_manufacturers_url: str
        :param housing_types_url: URL to the housing type file
        :type housing_types_url: str
        """
        logger.info("Note: Please make sure that you have installed the latest version of the transistor database, "
                    "especially if the update_from_fileexchange()-method ends in an error. "
                    "Find the latest version here: https://pypi.org/project/transistordatabase/")
        # Read links from index_url
        index_response = requests.get(index_url)
        if not index_response.ok:
            raise Exception(f"Index file was not found. URL: {index_url}")
        
        for transistor_url in index_response.iter_lines():
            transistor_response = requests.get(transistor_url)
            if not transistor_response.ok:
                logger.info(f"Transistor with URL {transistor_url} couldn't be downloaded. Transistor was skipped.")
                continue

            transistor = self.convert_dict_to_transistor_object(transistor_response.json())
            self.save_transistor(transistor, overwrite)

        # Get module manufacturers and housing types if URLs are given
        # Then overwrite local files and update lists
        if module_manufacturers_url is not None:
            module_manufacturers_response = requests.get(module_manufacturers_url)
            if not module_manufacturers_response.ok:
                raise Exception(f"Given module manufacturers file was not found. URL: {module_manufacturers_url}")

            with open(self.module_manufacturers_file_path, "w") as fd:
                fd.write(module_manufacturers_response.text)

            self.module_manufacturers = read_data_file(self.module_manufacturers_file_path)
            logger.info("Updated module manufacturers.")

        if housing_types_url is not None:
            housing_types_response = requests.get(housing_types_url)
            if not housing_types_response.ok:
                raise Exception(f"Given housing types file was not found. URL: {housing_types_response}")

            with open(self.housing_types_file_path, "w") as fd:
                fd.write(housing_types_response.text)

            self.housing_types = read_data_file(self.housing_types_file_path)
            logger.info("Updated housing types.")

    def compare_with_fileexchange(self, index_url: str, output_file: str):
        """
        Compare the current database with the given database from the fileexchange.

        Writes the difference in the given output_file.

        :param index_url: URL to the index file containing links to the Transistors of the Database.
        :type index_url: str
        :param output_file: File path to the file where the diff is written
        :type output_file: str
        """
        current_transistor_list = self.get_transistor_names_list()

        # Read links from index_url
        diff_dict = {}  # Dictionary containing the key as the name of the transistor and the value is the diff text.
        index_response = requests.get(index_url)
        if not index_response.ok:
            raise Exception(f"Index file was not found. URL: {index_url}")
        
        for transistor_url in index_response.iter_lines():
            transistor_response = requests.get(transistor_url)
            if not transistor_response.ok:
                logger.info(f"Transistor with URL {transistor_url} couldn't be downloaded. Transistor was skipped.")
                continue

            downloaded_transistor_dict = transistor_response.json()
            downloaded_transistor_name = downloaded_transistor_dict["name"]
            if downloaded_transistor_name in current_transistor_list:
                existing_transistor_dict = self.load_transistor(downloaded_transistor_name).convert_to_dict()
                # Here it is necessary to first get the deepdiff as json and then back to a dictionary. Because when calling DeepDiff().to_dict() it wouldn't be
                # json serializable due to a datatype called PrettyOrderedSet.
                # And since the to_json returns a srting it needs to be converted back to a dict in order to be represented well in the output file.
                diff = json.loads(deepdiff.DeepDiff(existing_transistor_dict, downloaded_transistor_dict).to_json())
                if diff:
                    diff_dict[downloaded_transistor_name] = diff
                current_transistor_list.remove(downloaded_transistor_name)
            else:
                # Transistor is not in local database
                diff_dict[downloaded_transistor_name] = "Transistor missing in local database."

        for not_found_transistor in current_transistor_list:
            # Transistor was installed locally but not in database
            diff_dict[not_found_transistor] = "Transistor exists in local database but is not on the given fileexchange."

        if not diff_dict:
            logger.info("The local database is equal to the given fileexchange database.") 
        else:
            logger.info("There are differences found between the local database and the given fileexchange database. Please have a look at the output file.")
            with open(output_file, "w") as fd:
                json.dump(diff_dict, fd, indent=2)

    def export_all_datasheets(self, filter_list: list = None):
        """
        Export all the available transistor data present in the local mongoDB database.

        :param filter_list: a list of transistor names that needs to be exported in specific
        :type filter_list: list
        """
        transistor_list = self.get_transistor_names_list()
        filtered_list = list()
        html_list = list()
        pdf_name_list = list()
        paths_list = list()
        if filter_list is not None:
            for item in filter_list:
                if item not in transistor_list:
                    logger.info("{0} transistor is not present in database".format(item))
                else:
                    filtered_list.append(item)
        else:
            filtered_list = transistor_list
        if len(filtered_list) > 0:
            for transistor_name in filtered_list:
                transistor = self.load_transistor(transistor_name)
                html_list.append(transistor.export_datasheet(build_collection=True))
                pdf_name_list.append(transistor.name + ".pdf")
                paths_list.append(os.path.join(os.getcwd(), transistor.name + ".pdf"))
            html_to_pdf(html_list, pdf_name_list, paths_list)
        else:
            logger.info("Nothing to export, please recheck inputs")

    def convert_dict_to_transistor_object(self, transistor_dict: dict) -> Transistor:
        """
        Convert a dictionary to a transistor object.

        This is a helper function of the following functions:
        - parallel_transistors()
        - load()
        - import_json()

        :param transistor_dict: transistor dictionary
        :type transistor_dict: dict

        :return: Transistor object
        :rtype: Transistor object
        """
        # Convert transistor_args
        if 'c_oss' in transistor_dict and transistor_dict['c_oss'] is not None:
            for i in range(len(transistor_dict['c_oss'])):
                transistor_dict['c_oss'][i]['graph_v_c'] = np.array(transistor_dict['c_oss'][i]['graph_v_c'])
        if 'c_iss' in transistor_dict and transistor_dict['c_iss'] is not None:
            for i in range(len(transistor_dict['c_iss'])):
                transistor_dict['c_iss'][i]['graph_v_c'] = np.array(transistor_dict['c_iss'][i]['graph_v_c'])
        if 'c_rss' in transistor_dict and transistor_dict['c_rss'] is not None:
            for i in range(len(transistor_dict['c_rss'])):
                transistor_dict['c_rss'][i]['graph_v_c'] = np.array(transistor_dict['c_rss'][i]['graph_v_c'])
        if 'graph_v_ecoss' in transistor_dict and transistor_dict['graph_v_ecoss'] is not None:
            transistor_dict['graph_v_ecoss'] = np.array(transistor_dict['graph_v_ecoss'])
        if 'raw_measurement_data' in transistor_dict:
            for i in range(len(transistor_dict['raw_measurement_data'])):
                for u in range(len(transistor_dict['raw_measurement_data'][i]['dpt_on_vds'])):
                    transistor_dict['raw_measurement_data'][i]['dpt_on_vds'][u] = np.array(transistor_dict['raw_measurement_data'][i]['dpt_on_vds'][u])
                for u in range(len(transistor_dict['raw_measurement_data'][i]['dpt_on_id'])):
                    transistor_dict['raw_measurement_data'][i]['dpt_on_id'][u] = np.array(transistor_dict['raw_measurement_data'][i]['dpt_on_id'][u])
                for u in range(len(transistor_dict['raw_measurement_data'][i]['dpt_off_vds'])):
                    transistor_dict['raw_measurement_data'][i]['dpt_off_vds'][u] = np.array(transistor_dict['raw_measurement_data'][i]['dpt_off_vds'][u])
                for u in range(len(transistor_dict['raw_measurement_data'][i]['dpt_off_id'])):
                    transistor_dict['raw_measurement_data'][i]['dpt_off_id'][u] = np.array(transistor_dict['raw_measurement_data'][i]['dpt_off_id'][u])

        # Convert switch_args
        switch_args = transistor_dict['switch']
        if switch_args['thermal_foster']['graph_t_rthjc'] is not None:
            switch_args['thermal_foster']['graph_t_rthjc'] = np.array(switch_args['thermal_foster']['graph_t_rthjc'])
        for i in range(len(switch_args['channel'])):
            switch_args['channel'][i]['graph_v_i'] = np.array(switch_args['channel'][i]['graph_v_i'])
        for i in range(len(switch_args['e_on'])):
            if switch_args['e_on'][i]['dataset_type'] == 'graph_r_e':
                switch_args['e_on'][i]['graph_r_e'] = np.array(switch_args['e_on'][i]['graph_r_e'])
            elif switch_args['e_on'][i]['dataset_type'] == 'graph_i_e':
                switch_args['e_on'][i]['graph_i_e'] = np.array(switch_args['e_on'][i]['graph_i_e'])
            elif switch_args['e_on'][i]['dataset_type'] == 'graph_t_e':
                switch_args['e_on'][i]['graph_t_e'] = np.array(switch_args['e_on'][i]['graph_t_e'])
        if 'e_on_meas' in switch_args:
            for i in range(len(switch_args['e_on_meas'])):
                if switch_args['e_on_meas'][i]['dataset_type'] == 'graph_r_e':
                    switch_args['e_on_meas'][i]['graph_r_e'] = np.array(switch_args['e_on_meas'][i]['graph_r_e'])
                elif switch_args['e_on_meas'][i]['dataset_type'] == 'graph_i_e':
                    switch_args['e_on_meas'][i]['graph_i_e'] = np.array(switch_args['e_on_meas'][i]['graph_i_e'])
                elif switch_args['e_on_meas'][i]['dataset_type'] == 'graph_t_e':
                    switch_args['e_on_meas'][i]['graph_t_e'] = np.array(switch_args['e_on_meas'][i]['graph_t_e'])
        for i in range(len(switch_args['e_off'])):
            if switch_args['e_off'][i]['dataset_type'] == 'graph_r_e':
                switch_args['e_off'][i]['graph_r_e'] = np.array(switch_args['e_off'][i]['graph_r_e'])
            elif switch_args['e_off'][i]['dataset_type'] == 'graph_i_e':
                switch_args['e_off'][i]['graph_i_e'] = np.array(switch_args['e_off'][i]['graph_i_e'])
            elif switch_args['e_off'][i]['dataset_type'] == 'graph_t_e':
                switch_args['e_off'][i]['graph_t_e'] = np.array(switch_args['e_off'][i]['graph_t_e'])
        if 'e_off_meas' in switch_args:
            for i in range(len(switch_args['e_off_meas'])):
                if switch_args['e_off_meas'][i]['dataset_type'] == 'graph_r_e':
                    switch_args['e_off_meas'][i]['graph_r_e'] = np.array(switch_args['e_off_meas'][i]['graph_r_e'])
                elif switch_args['e_off_meas'][i]['dataset_type'] == 'graph_i_e':
                    switch_args['e_off_meas'][i]['graph_i_e'] = np.array(switch_args['e_off_meas'][i]['graph_i_e'])
                elif switch_args['e_off_meas'][i]['dataset_type'] == 'graph_t_e':
                    switch_args['e_off_meas'][i]['graph_t_e'] = np.array(switch_args['e_off_meas'][i]['graph_t_e'])
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
        diode_args = transistor_dict['diode']
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

        return Transistor(transistor_dict, switch_args, diode_args, self.housing_types, self.module_manufacturers)

    def parallel_transistors(self, transistor: Transistor, count_parallels: int = 2) -> Transistor:
        """
        Connect [count_parallels] transistors in parallel.

        The returned transistor object behaves like a single transistor.

        - name will be modified by adding _[count_parallels]_parallel
        - channel characteristics will be modified
        - e_on/e_off/e_rr characteristics will be modified
        - thermal behaviour will be modified

        :param transistor: transistor object to paralize
        :type transistor: Transistor
        :param count_parallels: count of parallel transistors of same type, default = 2
        :type count_parallels: int

        :return: transistor object with parallel transistors
        :rtype: Transistor

        :Example:

        >>> import transistordatabase as tdb
        >>> transistor = tdb.load('Infineon_FF200R12KE3')
        >>> parallel_transistorobject = transistor.parallel_transistors(3)

        """
        transistor_dict = transistor.convert_to_dict()

        # modify transistor elements
        transistor_dict['name'] = f"{transistor_dict['name']}_{count_parallels}_parallel"
        transistor_dict['r_th_switch_cs'] = transistor_dict['r_th_switch_cs'] / count_parallels
        transistor_dict['r_th_diode_cs'] /= count_parallels
        transistor_dict['r_th_cs'] /= count_parallels
        transistor_dict['i_abs_max'] = transistor_dict['i_abs_max'] * count_parallels
        transistor_dict['i_cont'] = transistor_dict['i_cont'] * count_parallels
        transistor_dict['c_iss'] = transistor_dict['c_iss'] * count_parallels
        transistor_dict['c_oss'] *= count_parallels
        transistor_dict['c_rss'] *= count_parallels

        # modify switch dict
        for channel_dict in transistor_dict['switch']['channel']:
            if 'graph_v_i' in channel_dict:
                channel_dict['graph_v_i'][1] = [y * count_parallels for y in channel_dict['graph_v_i'][1]]
        for e_on_dict in transistor_dict['switch']['e_on']:
            if e_on_dict['dataset_type'] == 'graph_i_e':
                e_on_dict['graph_i_e'][0] = [y * count_parallels for y in e_on_dict['graph_i_e'][0]]
                e_on_dict['graph_i_e'][1] = [y * count_parallels for y in e_on_dict['graph_i_e'][1]]
            if e_on_dict['dataset_type'] == 'graph_r_e':
                e_on_dict['graph_r_e'][1] = [y * count_parallels for y in e_on_dict['graph_r_e'][1]]
            if e_on_dict['dataset_type'] == 'graph_t_e':
                e_on_dict['graph_t_e'][1] = [y * count_parallels for y in e_on_dict['graph_t_e'][1]]
        for e_off_dict in transistor_dict['switch']['e_off']:
            if e_off_dict['dataset_type'] == 'graph_i_e':
                e_off_dict['graph_i_e'][0] = [y * count_parallels for y in e_off_dict['graph_i_e'][0]]
                e_off_dict['graph_i_e'][1] = [y * count_parallels for y in e_off_dict['graph_i_e'][1]]
            if e_off_dict['dataset_type'] == 'graph_r_e':
                e_off_dict['graph_r_e'][1] = [y * count_parallels for y in e_off_dict['graph_r_e'][1]]
            if e_off_dict['dataset_type'] == 'graph_t_e':
                e_off_dict['graph_t_e'][1] = [y * count_parallels for y in e_off_dict['graph_t_e'][1]]
        # modify diode dict
        for x in transistor_dict['diode']['channel']:
            x['graph_v_i'][1] = [y * count_parallels for y in x['graph_v_i'][1]]
        for e_rr_dict in transistor_dict['diode']['e_rr']:
            if e_rr_dict['dataset_type'] == 'graph_i_e':
                e_rr_dict['graph_i_e'][0] = [y * count_parallels for y in e_rr_dict['graph_i_e'][0]]
                e_rr_dict['graph_i_e'][1] = [y * count_parallels for y in e_rr_dict['graph_i_e'][1]]
            if e_rr_dict['dataset_type'] == 'graph_r_e':
                e_rr_dict['graph_r_e'][1] = [y * count_parallels for y in e_rr_dict['graph_r_e'][1]]

        # modify switch thermal dict
        transistor_dict['switch']['thermal_foster']['r_th_total'] /= count_parallels
        transistor_dict['switch']['thermal_foster']['r_th_vector'] = None if \
            transistor_dict['switch']['thermal_foster']['r_th_vector'] is None else [x / count_parallels for x in
                                                                                     transistor_dict['switch'][
                                                                                         'thermal_foster']['r_th_vector']]
        transistor_dict['switch']['thermal_foster']['c_th_total'] = None if transistor_dict['switch']['thermal_foster']['c_th_total'] is None else \
            transistor_dict['switch']['thermal_foster']['c_th_total'] / count_parallels
        transistor_dict['switch']['thermal_foster']['c_th_vector'] = None if \
            transistor_dict['switch']['thermal_foster']['c_th_vector'] is None else [x / count_parallels for x in
                                                                                     transistor_dict['switch'][
                                                                                         'thermal_foster']['c_th_vector']]

        if transistor_dict['switch']['thermal_foster']['graph_t_rthjc'] is not None:
            transistor_dict['switch']['thermal_foster']['graph_t_rthjc'][1] = [x / count_parallels for x in
                                                                               transistor_dict['switch'][
                                                                                   'thermal_foster'][
                                                                                   'graph_t_rthjc'][1]]
        # modify diode thermal dict
        transistor_dict['diode']['thermal_foster']['r_th_total'] /= count_parallels
        transistor_dict['diode']['thermal_foster']['r_th_vector'] = None if transistor_dict['diode']['thermal_foster']['r_th_vector'] is None else [
            x / count_parallels for x in transistor_dict['diode']['thermal_foster']['r_th_vector']]
        transistor_dict['diode']['thermal_foster']['c_th_total'] = None if transistor_dict['diode']['thermal_foster']['c_th_total'] is None else \
            transistor_dict['diode']['thermal_foster']['c_th_total'] / count_parallels
        transistor_dict['diode']['thermal_foster']['c_th_vector'] = None if transistor_dict['diode']['thermal_foster']['c_th_vector'] is None else [
            x / count_parallels for x in transistor_dict['diode']['thermal_foster']['c_th_vector']]

        if transistor_dict['diode']['thermal_foster']['graph_t_rthjc'] is not None:
            transistor_dict['diode']['thermal_foster']['graph_t_rthjc'][1] = [x / count_parallels for x in
                                                                              transistor_dict['diode'][
                                                                                  'thermal_foster'][
                                                                                  'graph_t_rthjc'][1]]

        return self.convert_dict_to_transistor_object(transistor_dict)

    @staticmethod
    def import_xml_data(files: dict) -> Transistor:
        """
        Import switch and diode characteristics in plecs xml file format.

        :param files: dictionary holding switch and diode xml file names
        :rtype files: dict

        :raises ImportError: raised when file format is not valid or not found

        :return: Transistor object creating using information extracted from the provided files
        :rtype: Transistor
        """
        try:
            s_info, s_energy_on_list, s_energy_off_list, s_channel_list, s_foster_args = get_xml_data(files['switch'])
            switch_args = {
                'comment': 'Gate voltages are set to 12V/0V',
                'manufacturer': s_info['vendor'],
                'technology': None,
                't_j_max': 175,
                'channel': s_channel_list,
                'e_on': s_energy_on_list,
                'e_off': s_energy_off_list,
                'thermal_foster': s_foster_args}
            d_info, d_energy_on_list, d_energy_off_list, d_channel_list, d_foster_args = get_xml_data(files['diode'])
            if s_info['class'] == 'IGBT' and d_info['class'] == 'Diode':
                if s_info['vendor'] != d_info['vendor'] or s_info['partnumber'] != d_info['partnumber']:
                    raise ImportError('Vendor or part number differs')
            else:
                raise ImportError('Invalid files: One of type ' + s_info['class'] + ' and other ' + d_info['class'])
            diode_args = {
                'comment': 'Turn On and Off voltages are set to 12V/0V',
                'manufacturer': d_info['vendor'],
                'technology': None,
                't_j_max': 175,
                'channel': d_channel_list,
                'e_rr': d_energy_off_list,
                'thermal_foster': d_foster_args}
            transistor_args = {
                'name': s_info['partnumber'],
                'type': s_info['class'],
                'author': 'XML importer',
                'comment': 'Generated using xml importer (inaccurate)',
                'manufacturer': s_info['vendor'],
                'datasheet_hyperlink': 'http://www.plexim.com/xml/semiconductors/' + s_info['partnumber'],
                'datasheet_date': datetime.date.today(),
                'datasheet_version': "unknown",
                'housing_area': 0,
                'cooling_area': 0,
                'housing_type': 'PLECS Import',
                'v_abs_max': 999999999,
                'i_abs_max': max(s_channel_list[0]["graph_v_i"][1]),
                'i_cont': max(s_channel_list[0]["graph_v_i"][1]) / 2,
                'c_iss': None,  # insert csv here
                'c_oss': None,  # insert csv here
                'c_rss': None,  # insert csv here
                'graph_v_ecoss': None,
                'r_g_int': 0,
                'r_th_cs': 0,
                'r_th_diode_cs': 0,
                'r_th_switch_cs': 0}
            return Transistor(transistor_args, switch_args, diode_args)
        except ImportError as e:
            logger.info(e.args[0])

    @staticmethod
    def export_single_transistor_to_json(transistor: Transistor, file_path: str | None = None):
        """
        Export a single transistor object to a json file.

        :param transistor: transistor name
        :type transistor: Transistor
        :param file_path: Specify a directory or a file path.
        :type file_path: str | None
        """
        if file_path is None:
            file_path = os.getcwd()
        if os.path.isdir(file_path):
            file_path = os.path.join(file_path, f"{transistor.name}.json")
            logger.info(file_path)
        with open(file_path, "w") as fd:
            json.dump(transistor.convert_to_dict(), fd, indent=2)

    @staticmethod
    def dpt_save_data(measurement_dict: dict) -> dict:
        """Import double pulse measurements and calculates switching losses to each given working point.

        Note: This function brings the measurement data to a dictionary.
        It does not store the data to the transistor!

        [1] options for the integration interval are based on following paper:
        Link: https://ieeexplore.ieee.org/document/8515553

        :param measurement_dict: dictionary with above mentioned parameters
        :type measurement_dict: dict

        example to call this function:

        >>> dpt_save_dict = {
        >>>     'path': 'C:/Users/.../GaN-Systems/400V/*.csv',
        >>>     'dataset_type': 'graph_i_e',
        >>>     'comment': '',
        >>>     'load_inductance': 750e-6,
        >>>     'commutation_inductance': 15.63e-9,
        >>>     'commutation_device': 'IDH06G65C6',
        >>>     'measurement_date': None,
        >>>     'measurement_testbench': 'LEA-UPB Testbench',
        >>>     'v_g': 12,
        >>>     'v_g_off': 0,
        >>>     'energies': 'both',
        >>>     'r_g_off': 1.8,
        >>>     'integration_interval': 'IEC 60747-8',
        >>>     'mode': 'analyze'}

        >>> import transistordatabase as tdb
        >>> dpt_energies_dict = tdb.dpt_save_data(dpt_save_dict)

        """
        if measurement_dict.get('integration_interval') == 'IEC 60747-9':
            # FETs
            off_vds_limit = 0.1
            off_is_limit = 0.02
            on_vds_limit = 0.02
            on_is_limit = 0.1
        elif measurement_dict.get('integration_interval') == 'IEC 60747-8':
            # IGBTs
            off_vds_limit = 0.1
            off_is_limit = 0.1
            on_vds_limit = 0.1
            on_is_limit = 0.1
        elif measurement_dict.get('integration_interval') == 'Mitsubishi':
            off_vds_limit = 0.1
            off_is_limit = 0.1
            on_vds_limit = 0.1
            on_is_limit = 0.1
        elif measurement_dict.get('integration_interval') == 'Infineon':
            off_vds_limit = 0.1
            off_is_limit = 0.02
            on_vds_limit = 0.02
            on_is_limit = 0.1
        elif measurement_dict.get('integration_interval') == 'Wolfspeed':
            off_vds_limit = 0
            off_is_limit = -0.1
            on_vds_limit = -0.1
            on_is_limit = 0
        else:
            off_vds_limit = 0.1
            off_is_limit = 0.1
            on_vds_limit = 0.1
            on_is_limit = 0.1

        # Get a list of all the csv files
        csv_files = glob.glob(measurement_dict.get('path'))
        
        # position_t_j = csv_files[1].rfind("C_")
        # position_t_j_start = csv_files[1].rfind("_", 0, position_t_j)
        # t_j = int(csv_files[1][position_t_j_start + 1:position_t_j])

        # position_r_g = csv_files[1].rfind("R_")
        # position_r_g_start = csv_files[1].rfind("_", 0, position_r_g)
        # r_g = float(csv_files[1][position_r_g_start + 1:position_r_g])

        # position_v_supply = csv_files[1].rfind("V_")
        # position_v_supply_start = csv_files[1].rfind("_", 0, position_v_supply)
        # v_supply = int(csv_files[1][position_v_supply_start + 1:position_v_supply])

        dpt_raw_data = {}
        e_off_meas = dict 
        e_on_meas = dict

        position_attribute_start = 'V_'
        position_attribute_end = 'A_'
        label_x_plot = 'Id / A'

        if measurement_dict['dataset_type'] == 'graph_r_e':
            position_attribute_start = 'C_'
            position_attribute_end = 'R_'
            label_x_plot = 'Ron / Ohm'
            r_g_on_list = []

        if measurement_dict['energies'] == 'e_off' or measurement_dict['energies'] == 'both':
            off_i_locations = []
            off_v_locations = []
            csv_length = len(csv_files)

            #################################################################################
            # Read all Turn-off supply voltage, gate voltage, gate resistance and temperature
            #################################################################################
            csv_count = 0
            v_supply_off = []
            while csv_length > csv_count:
                if csv_files[csv_count].rfind("_OFF_I") != -1:
                    position_v_supply_off = csv_files[csv_count].rfind("V_")
                    position_v_supply_off_start = csv_files[csv_count].rfind("_", 0, position_v_supply_off)
                    v_supply_off.append(csv_files[csv_count][position_v_supply_off_start + 1:position_v_supply_off])
                csv_count += 1
            logger.info('v_supply_off=', v_supply_off)
            if not compare_list(v_supply_off):
                raise ValueError
            i = 0
            v_g_off = []
            while csv_length > i:
                if csv_files[i].rfind("_OFF_I") != -1:
                    position_v_g_off = csv_files[i].rfind("vg_")
                    position_v_g_off_start = csv_files[i].rfind("_", 0, position_v_g_off)
                    v_g_off.append(csv_files[i][position_v_g_off_start + 1:position_v_g_off])
                i += 1
            logger.info('vg_off=', v_g_off)
            if not compare_list(v_g_off):
                raise ValueError
            j = 0
            r_g_off = []
            while csv_length > j:
                if csv_files[j].rfind("_OFF_I") != -1:
                    position_r_g_off = csv_files[j].rfind("R_")
                    position_r_g_off_start = csv_files[j].rfind("_", 0, position_r_g_off)
                    r_g_off.append(csv_files[j][position_r_g_off_start + 1:position_r_g_off])
                j += 1
            logger.info('Rg_off=', r_g_off)
            if not compare_list(r_g_off):
                raise ValueError
            k = 0
            t_j_off = []
            while csv_length > k:
                if csv_files[k].rfind("_OFF_I") != -1:
                    position_t_j_off = csv_files[k].rfind("C_")
                    position_t_j_off_start = csv_files[k].rfind("_", 0, position_t_j_off)
                    t_j_off.append(csv_files[k][position_t_j_off_start + 1:position_t_j_off])
                k += 1
            logger.info('t_j_off=', t_j_off)
            if not compare_list(t_j_off):
                raise ValueError

            ##############################
            # Read all Turn-off current measurements and sort them by Id or Rgon
            ##############################
            i = 0
            while csv_length > i:
                if csv_files[i].rfind("_OFF_I") != -1:
                    position_a = csv_files[i].rfind(position_attribute_end)
                    position_b = csv_files[i].rfind(position_attribute_start)
                    off_i_locations.append([i, float(csv_files[i][position_b + 2:position_a].replace(',', '.'))])
                i += 1
            off_i_locations.sort(key=lambda x: x[1])

            ##############################
            # Read all Turn-off voltage measurements and sort them by Id or Rgon
            ##############################
            i = 0
            while csv_length > i:
                if csv_files[i].rfind("_OFF_U") != -1:
                    position_a = csv_files[i].rfind(position_attribute_end)
                    position_b = csv_files[i].rfind(position_attribute_start)
                    off_v_locations.append([i, float(csv_files[i][position_b + 2:position_a].replace(',', '.'))])
                i += 1
            off_v_locations.sort(key=lambda x: x[1])

            sample_point = 0
            measurement_points = len(off_i_locations)
            e_off = []
            vds_raw_off = []
            id_raw_off = []
            dv_dt_off = []
            di_dt_off = []
            time_correction = 0
            time_input = 0

            while measurement_points > sample_point:
                # Load vds_temp and id_temp pairs in increasing order
                vds_temp = np.genfromtxt(csv_files[off_v_locations[sample_point][0]], delimiter=',', skip_header=24)
                id_temp = np.genfromtxt(csv_files[off_i_locations[sample_point][0]], delimiter=',', skip_header=24)

                vds_raw_off.append(np.array(vds_temp))
                id_raw_off.append(np.array(id_temp))

                sample_length = len(vds_temp)
                sample_interval = abs(vds_temp[1, 0] - vds_temp[2, 0])
                avg_interval = int(sample_length * 0.05)

                vds_avg_max = 0
                id_avg_max = 0

                ##############################
                # Find the max. id_temp in steady state
                ##############################
                i = 0
                while i <= avg_interval:
                    id_avg_max = id_avg_max + id_temp[i, 1] / avg_interval
                    i += 1

                ##############################
                # Find the max. vds_temp in steady state
                ##############################
                i = 0
                while i <= avg_interval:
                    vds_avg_max = vds_avg_max + vds_temp[(sample_length - 1 - i), 1] / avg_interval
                    i += 1

                ##############################
                # Find the starting point of the Eoff integration
                # i equals the lower integration limit
                ##############################
                i = 0
                e_off_temp = 0
                while vds_temp[i, 1] < (vds_avg_max * off_vds_limit):
                    i += 1

                lower_integration_limit = i

                di_dt_counter_low = 0
                while id_temp[di_dt_counter_low, 1] > (id_avg_max * 0.8):
                    di_dt_counter_low += 1

                di_dt_counter_high = di_dt_counter_low
                while id_temp[di_dt_counter_high, 1] > (id_avg_max * 0.2):
                    di_dt_counter_high += 1

                dv_dt_counter_low = 0
                while vds_temp[dv_dt_counter_low, 1] < (vds_avg_max * 0.8):
                    dv_dt_counter_low += 1

                dv_dt_counter_high = dv_dt_counter_low
                while vds_temp[dv_dt_counter_high, 1] < (vds_avg_max * 0.8):
                    dv_dt_counter_high += 1

                ##############################
                # Integrate the power with predefined integration limits
                ##############################
                time_delay: int | None = measurement_dict.get('global_delay_time')
                while id_temp[i - time_correction, 1] >= (id_avg_max * off_is_limit):
                    e_off_temp = e_off_temp + (vds_temp[i, 1] * id_temp[i - time_correction, 1] * sample_interval)
                    i += 1

                upper_integration_limit = i

                if measurement_dict['mode'] == 'analyze':
                    text1 = f"E_off = {(e_off_temp * 1000000).round(2)} µJ, Integration time = " \
                            f"{((id_temp[upper_integration_limit, 0] - id_temp[lower_integration_limit, 0]) * 1000000000).round(2)} ns"
                    text2 = f"time correction = {(time_correction * sample_interval * 1000000000).round(2)} ns"
                    fig, ax1 = plt.subplots()
                    ax1.set_xlabel("t / ns")
                    ax1.set_ylabel("Id / A", color='r')
                    ax1.plot(((id_temp[:, 0] * 1000000000) + float(time_input)), id_temp[:, 1], color='r')
                    plt.axvline(id_temp[upper_integration_limit, 0] * 1000000000, color='green', linestyle='dotted', linewidth=2)
                    plt.axvline(id_temp[lower_integration_limit, 0] * 1000000000, color='green', linestyle='dotted', linewidth=2)
                    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
                    ax1.text(0.02, 1.05, text1, transform=ax1.transAxes, fontsize=12,
                             verticalalignment='bottom', horizontalalignment='left', bbox=props)
                    ax1.text(0.5, .5, text2, transform=ax1.transAxes, fontsize=12,
                             verticalalignment='center', horizontalalignment='left', bbox=props)
                    plt.grid(axis='both', color='grey', linestyle='--', linewidth=1)
                    ax2 = ax1.twinx()
                    ax2.set_ylabel('Uds / V', color='b')
                    ax2.plot(vds_temp[:, 0] * 1000000000, vds_temp[:, 1], color='b')
                    plt.show()
                    if time_delay == 0:
                        time_input = 0
                    else:
                        time_input = input('Please give a value for time correction in ns')
                        if check_float(time_input):
                            time_correction = int(float(time_input) / (sample_interval * 1000000000))
                            continue
                        else:
                            time_correction = 0
                            time_input = 0

                if measurement_dict['dataset_type'] == 'graph_r_e':
                    e_off.append([off_i_locations[sample_point][1], e_off_temp])
                    r_g_on_list.append(off_i_locations[sample_point][1])
                else:
                    e_off.append([id_avg_max, e_off_temp])

                di_dt_off.append((id_temp[di_dt_counter_high, 1] - id_temp[di_dt_counter_low, 1]) / (
                    abs(id_temp[di_dt_counter_high, 0] - id_temp[di_dt_counter_low, 0]) * 1000000000))
                dv_dt_off.append((vds_temp[dv_dt_counter_high, 1] - vds_temp[lower_integration_limit, 1]) / (
                    abs(vds_temp[dv_dt_counter_high, 0] - vds_temp[lower_integration_limit, 0]) * 1000000000))

                sample_point += 1

            e_off_0 = [item[0] for item in e_off]
            e_off_1 = [item[1] for item in e_off]

            e_off_meas = {
                'dataset_type': measurement_dict.get('dataset_type'),
                't_j': t_j_off,
                'load_inductance': measurement_dict.get('load_inductance'),
                'commutation_inductance': measurement_dict.get('commutation_inductance'),
                'commutation_device': measurement_dict.get('commutation_device'),
                'comment': measurement_dict.get('comment'),
                'measurement_date': measurement_dict.get('measurement_date'),
                'measurement_testbench': measurement_dict.get('measurement_testbench'),
                'v_supply': v_supply_off,
                # 'v_g': v_g,
                'v_g_off': v_g_off,
                # 'r_g': r_g,
                'r_g_off': r_g_off,
                'graph_i_e': np.array([e_off_0, e_off_1]),
                'graph_r_e': np.array([e_off_0, e_off_1]),
                'e_x': float(e_off_1[0]),
                'i_x': id_avg_max,
                'dv_dt': dv_dt_off,
                'di_dt': di_dt_off}

            dpt_raw_data |= {'dpt_off_vds': vds_raw_off, 'dpt_off_id': id_raw_off}

            ##############################
            # Plot Eoff
            ##############################
            x = [sub[0] for sub in e_off]
            y = [sub[1] * 1000000 for sub in e_off]
            fig, ax1 = plt.subplots()
            color = 'tab:red'
            ax1.set_xlabel(label_x_plot)
            ax1.set_ylabel("Eoff / µJ", color=color)
            ax1.plot(x, y, marker='o', color=color)
            plt.grid('both')
            plt.show(block=True)

        if measurement_dict['energies'] == 'e_on' or measurement_dict['energies'] == 'both':
            on_i_locations = []
            on_v_locations = []
            csv_length = len(csv_files)

            #################################################################################
            # Read all Turn-on supply voltage, gate voltage, gate resistance and temperature
            #################################################################################
            i = 0
            v_g = []
            while csv_length > i:
                if csv_files[i].rfind("_ON_I") != -1:
                    position_v_g = csv_files[i].rfind("vg_")
                    position_v_g_start = csv_files[i].rfind("_", 0, position_v_g)
                    v_g.append(csv_files[i][position_v_g_start + 1:position_v_g])
                i += 1
            logger.info('vg=', v_g)
            if not compare_list(v_g):
                raise ValueError
            j = 0
            r_g = []
            while csv_length > j:
                if csv_files[j].rfind("_ON_I") != -1:
                    position_r_g = csv_files[j].rfind("R_")
                    position_r_g_start = csv_files[j].rfind("_", 0, position_r_g)
                    r_g.append(csv_files[j][position_r_g_start + 1:position_r_g])
                j += 1
            logger.info('Rg=', r_g)
            if not compare_list(r_g):
                raise ValueError
            k = 0
            t_j = []
            while csv_length > k:
                if csv_files[k].rfind("_ON_I") != -1:
                    position_t_j = csv_files[k].rfind("C_")
                    position_t_j_start = csv_files[k].rfind("_", 0, position_t_j)
                    t_j.append(csv_files[k][position_t_j_start + 1:position_t_j])
                k += 1
            logger.info('t_j=', t_j)
            if not compare_list(t_j):
                raise ValueError
            csv_count = 0
            v_supply_on = []
            while csv_length > csv_count:
                if csv_files[csv_count].rfind("_ON_I") != -1:
                    position_v_supply_on = csv_files[csv_count].rfind("V_")
                    position_v_supply_on_start = csv_files[csv_count].rfind("_", 0, position_v_supply_on)
                    v_supply_on.append(csv_files[csv_count][position_v_supply_on_start + 1:position_v_supply_on])
                csv_count += 1
            logger.info('v_supply=', v_supply_on)
            if not compare_list(v_supply_on):
                raise ValueError
            ##############################
            # Read all Turn-on current measurements and sort them by Id or Rgon
            ##############################
            i = 0
            while csv_length > i:
                if csv_files[i].rfind("_ON_I") != -1:
                    position_a = csv_files[i].rfind(position_attribute_end)
                    position_b = csv_files[i].rfind(position_attribute_start)
                    on_i_locations.append([i, float(csv_files[i][position_b + 2:position_a].replace(',', '.'))])
                i += 1
            on_i_locations.sort(key=lambda x: x[1])

            ##############################
            # Read all Turn-on voltage measurements and sort them by Id or Rgon
            ##############################
            i = 0
            while csv_length > i:
                if csv_files[i].rfind("_ON_U") != -1:
                    position_a = csv_files[i].rfind(position_attribute_end)
                    position_b = csv_files[i].rfind(position_attribute_start)
                    on_v_locations.append([i, float(csv_files[i][position_b + 2:position_a].replace(',', '.'))])
                i += 1
            on_v_locations.sort(key=lambda x: x[1])

            sample_point = 0
            measurement_points = len(on_i_locations)
            e_on = []
            vds_raw_on = []
            id_raw_on = []
            dv_dt_on = []
            di_dt_on = []
            time_correction = 0
            time_input = 0

            while measurement_points > sample_point:
                # Load vds_temp and id_temp pairs in increasing order
                vds_temp = np.genfromtxt(csv_files[on_v_locations[sample_point][0]], delimiter=',', skip_header=24)
                id_temp = np.genfromtxt(csv_files[on_i_locations[sample_point][0]], delimiter=',', skip_header=24)

                vds_raw_on.append(np.array(vds_temp))
                id_raw_on.append(np.array(id_temp))

                sample_length = len(vds_temp)
                sample_interval = abs(vds_temp[1, 0] - vds_temp[2, 0])
                avg_interval = int(sample_length * 0.05)
                vds_avg_max = 0
                id_avg_max = 0

                ##############################
                # Find the max. id_temp in steady state
                ##############################
                i = 0
                while i <= avg_interval:
                    id_avg_max = id_avg_max + (id_temp[(sample_length - 3 - i), 1] / avg_interval)
                    i += 1

                ##############################
                # Find the max. vds_temp in steady state
                ##############################
                i = 0
                while i <= avg_interval:
                    vds_avg_max = vds_avg_max + (vds_temp[i, 1] / avg_interval)
                    i += 1

                # Calculate dv/dt
                dv_dt_counter_low = 0
                while vds_temp[dv_dt_counter_low, 1] > (vds_avg_max * 0.8):
                    dv_dt_counter_low += 1

                dv_dt_counter_high = dv_dt_counter_low
                while vds_temp[dv_dt_counter_high, 1] > (vds_avg_max * 0.2):
                    dv_dt_counter_high += 1

                di_dt_counter_low = 0
                while id_temp[di_dt_counter_low, 1] < (id_avg_max * 0.2):
                    di_dt_counter_low += 1

                di_dt_counter_high = di_dt_counter_low
                while id_temp[di_dt_counter_high, 1] < (id_avg_max * 0.8):
                    di_dt_counter_high += 1

                ##############################
                # Find the starting point of the Eon integration
                # i equals the lower integration limit
                ##############################
                i = 0
                e_on_temp = 0
                while id_temp[i, 1] < (id_avg_max * on_is_limit):
                    i += 1

                lower_integration_limit = i

                ##############################
                # Integrate the power with predefined integration limits
                ##############################
                while vds_temp[i - time_correction, 1] >= (vds_avg_max * on_vds_limit):
                    e_on_temp = e_on_temp + (vds_temp[i - time_correction, 1] * id_temp[i, 1] * sample_interval)
                    i += 1

                upper_integration_limit = i

                if measurement_dict['mode'] == 'analyze':
                    text1 = f"E_on = {(e_on_temp * 1000000).round(2)} µJ, Integration time = " \
                            f"{((id_temp[upper_integration_limit, 0] - id_temp[lower_integration_limit, 0]) * 1000000000).round(2)} ns"
                    text2 = f"time correction = {(time_correction * sample_interval * 1000000000).round(2)} ns"
                    fig, ax1 = plt.subplots()
                    ax1.set_xlabel("t / ns")
                    ax1.set_ylabel("Id / A", color='r')

                    ax1.plot(id_temp[:, 0] * 1000000000, id_temp[:, 1], color='r')
                    plt.axvline(id_temp[upper_integration_limit, 0] * 1000000000, color='green', linestyle='dotted', linewidth=2)
                    plt.axvline(id_temp[lower_integration_limit, 0] * 1000000000, color='green', linestyle='dotted', linewidth=2)
                    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
                    ax1.text(0.02, 1.05, text1, transform=ax1.transAxes, fontsize=12,
                             verticalalignment='bottom', horizontalalignment='left', bbox=props)
                    ax1.text(0.5, .5, text2, transform=ax1.transAxes, fontsize=12,
                             verticalalignment='center', horizontalalignment='left', bbox=props)
                    plt.grid(axis='both', color='grey', linestyle='--', linewidth=1)
                    ax2 = ax1.twinx()
                    ax2.set_ylabel('Uds / V', color='b')
                    ax2.plot(vds_temp[:, 0] * 1000000000 + float(time_input), vds_temp[:, 1], color='b')
                    plt.show()
                    if time_delay == 0:
                        time_input = 0
                    else:
                        time_input = input('Please give a value for time correction in ns')
                        if check_float(time_input):
                            time_correction = int(float(time_input) / (sample_interval * 1000000000))
                            continue
                        else:
                            time_correction = 0
                            time_input = 0

                if measurement_dict['dataset_type'] == 'graph_r_e':
                    e_on.append([on_i_locations[sample_point][1], e_on_temp])
                else:
                    e_on.append([id_avg_max, e_on_temp])

                if measurement_dict['dataset_type'] == 'graph_r_e' and measurement_dict['energies'] != 'both':
                    r_g_on_list.append(on_i_locations[sample_point][1])

                dv_dt_on.append((vds_temp[dv_dt_counter_high, 1] - vds_temp[dv_dt_counter_low, 1]) / (
                    abs(vds_temp[dv_dt_counter_high, 0] - vds_temp[dv_dt_counter_low, 0]) * 1000000000))
                di_dt_on.append((id_temp[di_dt_counter_high, 1] - id_temp[di_dt_counter_low, 1]) / (
                    abs(vds_temp[di_dt_counter_high, 0] - vds_temp[di_dt_counter_low, 0]) * 1000000000))

                sample_point += 1

            e_on_0 = [item[0] for item in e_on]
            e_on_1 = [item[1] for item in e_on]

            e_on_meas = {'dataset_type': measurement_dict.get('dataset_type'),
                         't_j': t_j,
                         'load_inductance': measurement_dict.get('load_inductance'),
                         'commutation_inductance': measurement_dict.get('commutation_inductance'),
                         'commutation_device': measurement_dict.get('commutation_device'),
                         'comment': measurement_dict.get('comment'),
                         'measurement_date': measurement_dict.get('measurement_date'),
                         'measurement_testbench': measurement_dict.get('measurement_testbench'),
                         'v_supply': v_supply_on,
                         'v_g': v_g,
                         # 'v_g_off': v_g_off,
                         'r_g': r_g,
                         # 'r_g_off': r_g_off,
                         'graph_i_e': np.array([e_on_0, e_on_1]),
                         'graph_r_e': np.array([e_on_0, e_on_1]),
                         'e_x': float(e_on_1[0]),
                         'i_x': id_avg_max,
                         'dv_dt': dv_dt_on,
                         'di_dt': di_dt_on}

            dpt_raw_data |= {'dpt_on_vds': vds_raw_on, 'dpt_on_id': id_raw_on}

            ##############################
            # Plot Eon
            ##############################
            x = [sub[0] for sub in e_on]
            y = [sub[1] * 1000000 for sub in e_on]
            fig, ax1 = plt.subplots()
            color = 'tab:red'
            ax1.set_xlabel(label_x_plot)
            ax1.set_ylabel("Eon / µJ", color=color)
            ax1.plot(x, y, marker='o', color=color)
            plt.grid('both')
            plt.show(block=True)

        dpt_raw_data |= {'t_j': t_j,
                         'load_inductance': measurement_dict.get('load_inductance'),
                         'measurement_date': measurement_dict.get('measurement_date'),
                         'measurement_testbench': measurement_dict.get('measurement_testbench'),
                         'v_supply': v_supply_on,
                         'v_g': v_g,
                         'v_g_off': v_g_off}

        if measurement_dict.get('dataset_type') == 'graph_r_e':
            dpt_raw_data |= {'dataset_type': 'dpt_u_i_r', 'r_g': r_g_on_list}
        else:
            dpt_raw_data |= {'dataset_type': 'dpt_u_i', 'r_g': r_g}
        dpt_dict = {'e_off_meas': e_off_meas, 'e_on_meas': e_on_meas, 'raw_measurement_data': dpt_raw_data}
        return dpt_dict
