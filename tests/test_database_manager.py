"""Unit tests for the database manager."""
from transistordatabase.database_manager import DatabaseManager, _request_get
import pytest
import os
import json
import requests
from unittest.mock import Mock, patch

test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")
database_dir = os.path.join(test_dir, "database")
fixed_transistor_path = os.path.join(test_dir, "CREE_C3M0060065J.json")
database_transistor_path = os.path.join(database_dir, "CREE_C3M0016120K.json")

@pytest.fixture
def database_json():
    """Fixture for further unit tests."""
    if not os.path.exists(database_dir):
        raise Exception("The folder test_data is missing.")

    db = DatabaseManager()
    db.set_operation_mode_json(database_dir)

    # Save current transistor to maybe restore it later
    transistor = db.load_transistor("CREE_C3M0016120K")

    yield db

    # Return to initial state of database
    transistor_names = db.get_transistor_names_list()
    if "CREE_C3M0016120K" not in transistor_names:
        # Add transistor
        with open(database_transistor_path, "w") as fd:
            json.dump(transistor.convert_to_dict(), fd)

    if "CREE_C3M0060065J" in transistor_names:
        # Remove transistor
        os.remove(os.path.join(database_dir, "CREE_C3M0060065J.json"))
        

def test_load_transistor_json(database_json: DatabaseManager):
    """
    Unit test for load_transistor.

    :param database_json: json database
    :type database_json: DatabaseManager
    """
    # Get transistor manually from the database
    t1_dict = None
    with open(os.path.join(database_dir, database_transistor_path), "r") as fd:
        t1_dict = json.load(fd)

    t1 = database_json.convert_dict_to_transistor_object(t1_dict)

    # Load transistor from database
    uut = database_json.load_transistor(t1.name)

    # Compare transistors
    assert t1 == uut, "Transistors are not equal."

def test_save_transistor_json(database_json: DatabaseManager):
    """
    Unit test for save_transistor.

    :param database_json: json database
    :type database_json: DatabaseManager
    """
    # Get transistor manually from single data folder
    t1_dict = None
    with open(os.path.join(database_dir, fixed_transistor_path), "r") as fd:
        t1_dict = json.load(fd)

    t1 = database_json.convert_dict_to_transistor_object(t1_dict)

    # Save transistor
    database_json.save_transistor(t1)

    # Check new database status
    assert sorted(["CREE_C3M0060065J", "CREE_C3M0016120K"]) == sorted(database_json.get_transistor_names_list()), \
        "Transistor is missing after adding it to database."

    # Check if transistor file is created in the database
    assert os.path.isfile(os.path.join(database_dir, "CREE_C3M0060065J.json")), "File does not exists"

    # Load database transistor
    t2_dict = None
    with open(os.path.join(database_dir, "CREE_C3M0060065J.json"), "r") as fd:
        t2_dict = json.load(fd)

    t2 = database_json.convert_dict_to_transistor_object(t2_dict)

    # Check if transistors are equal
    assert t1 == t2

def test_delete_transistor_json(database_json: DatabaseManager):
    """
    Unit test for delete_transistor.

    :param database_json: json database
    :type database_json: DatabaseManager
    """
    database_json.delete_transistor("CREE_C3M0016120K")

    # Check if transistor names list is empty
    assert not database_json.get_transistor_names_list()

    # Check if file has been removed
    assert not os.path.isfile(database_transistor_path)

def test_get_transistor_names_list_json(database_json: DatabaseManager):
    """
    Unit test for get_transistor_names_list.

    :param database_json: json database
    :type database_json: DatabaseManager
    """
    transistor_list = database_json.get_transistor_names_list()

    assert transistor_list == ["CREE_C3M0016120K"]


def test_save_transistor_as_copy(tmp_path: os.PathLike[str]) -> None:
    """
    Test that saving an existing transistor as a copy creates a distinct JSON file.

    :param tmp_path: Temporary directory used as the isolated JSON database.
    :type tmp_path: os.PathLike[str]
    """
    db = DatabaseManager()
    db.set_operation_mode_json(str(tmp_path))
    with open(fixed_transistor_path, "r") as fd:
        transistor = db.convert_dict_to_transistor_object(json.load(fd))

    db.save_transistor(transistor)
    db.save_transistor(transistor, overwrite=False)

    copy_name = f"{transistor.name} (1)"
    assert copy_name in db.get_transistor_names_list()
    assert db.load_transistor(copy_name).name == copy_name


def test_load_transistor_requires_exact_name(tmp_path: os.PathLike[str]) -> None:
    """
    Test that loading requires an exact match and does not accept a name prefix.

    :param tmp_path: Temporary directory used as the isolated JSON database.
    :type tmp_path: os.PathLike[str]
    """
    db = DatabaseManager()
    db.set_operation_mode_json(str(tmp_path))
    with open(fixed_transistor_path, "r") as fd:
        transistor_dict = json.load(fd)

    prefix_name = transistor_dict["name"]
    transistor_dict["name"] = f"{prefix_name}_variant"
    db.save_transistor(db.convert_dict_to_transistor_object(transistor_dict))

    assert db.load_transistor(prefix_name) is None


def test_save_transistor_rejects_path_separators(tmp_path: os.PathLike[str]) -> None:
    """
    Test that saving rejects transistor names containing path separators.

    :param tmp_path: Temporary directory used as the isolated JSON database.
    :type tmp_path: os.PathLike[str]
    """
    db = DatabaseManager()
    db.set_operation_mode_json(str(tmp_path))
    with open(fixed_transistor_path, "r") as fd:
        transistor_dict = json.load(fd)

    transistor_dict["name"] = "../outside"
    transistor = db.convert_dict_to_transistor_object(transistor_dict)

    with pytest.raises(ValueError, match="Invalid transistor name"):
        db.save_transistor(transistor)


@patch("transistordatabase.database_manager.requests.get")
def test_request_get_sets_finite_timeouts(mock_get: Mock) -> None:
    """
    Test that network requests use finite connect and read timeouts.

    :param mock_get: Mocked requests.get function.
    :type mock_get: Mock
    """
    url = "https://example.test/data.json"
    response = Mock()
    mock_get.return_value = response

    assert _request_get(url, "testing") is response
    mock_get.assert_called_once_with(url, timeout=(5, 30))


@patch("transistordatabase.database_manager.requests.get")
def test_request_get_wraps_timeout_with_context(mock_get: Mock) -> None:
    """
    Test that a request timeout is raised with operation context.

    :param mock_get: Mocked requests.get function.
    :type mock_get: Mock
    """
    mock_get.side_effect = requests.Timeout("read timed out")

    with pytest.raises(TimeoutError, match="fetching test data"):
        _request_get("https://example.test/data.json", "fetching test data")


@patch("transistordatabase.database_manager.requests.get")
def test_request_get_wraps_connection_errors(mock_get: Mock) -> None:
    """
    Test that request connection failures are raised with operation context.

    :param mock_get: Mocked requests.get function.
    :type mock_get: Mock
    """
    mock_get.side_effect = requests.ConnectionError("connection refused")

    with pytest.raises(ConnectionError, match="fetching test data"):
        _request_get("https://example.test/data.json", "fetching test data")
