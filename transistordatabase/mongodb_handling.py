"""Hanle with the mongodb database."""
# Third party libraries
import pymongo
from pymongo.errors import ServerSelectionTimeoutError

def connect_tdb(host: str):
    """
    Establish a connection with transistordatabase_exchange.

    :param host: "local" is specified by default, other cases need to be investigated
    :type host: str

    :return: transistor_database collection
    """
    if host == "local":
        host = "mongodb://localhost:27017/"
    my_transistor_database = pymongo.MongoClient(host)
    return my_transistor_database.transistor_database.collection


def connect_local_tdb():
    """
    Establish a connection with transistordatabase_exchange.

    Internally used by

      - update_from_fileexchange() method to sync the local with transistordatabase_File_Exchange
      - load() methods for saving and loading the transistor object to local mongodb-database.

    :return: transistor_database collection

    :raises pymongo.errors.ServerSelectionTimeoutError: if there is no mongoDB instance running
    :raises MissingServerConnection:
    """
    try:
        max_server_delay = 1
        host = "mongodb://localhost:27017/"
        my_client = pymongo.MongoClient(host, serverSelectionTimeoutMS=max_server_delay)
        my_client.server_info()
    except ServerSelectionTimeoutError:
        msg = 'Make sure that your MongoDB instance is running. If not please install it from ' \
              'https://docs.mongodb.com/manual/administration/install-community/'
        raise MissingServerConnection(msg)
    else:
        return my_client["local"]["transistor_database"]


def drop_local_tdb():
    """
    Drop the local database.

    :raises pymongo.errors.ServerSelectionTimeoutError: if there is no mongoDB instance running
    :raises MissingServerConnection: Missing server connection
    """
    try:
        max_server_delay = 1
        host = "mongodb://localhost:27017/"
        my_client = pymongo.MongoClient(host, serverSelectionTimeoutMS=max_server_delay)
        my_client.server_info()
    except ServerSelectionTimeoutError:
        msg = 'Make sure that your MongoDB instance is running. If not please install it from ' \
              'https://docs.mongodb.com/manual/administration/install-community/'
        raise MissingServerConnection(msg)
    else:
        my_client.drop_database('transistor_database')

class MissingServerConnection(ServerSelectionTimeoutError):
    """Reserved for future use."""

    # TODO 
    pass
