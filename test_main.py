import json
import os
import shutil # For cleanup if needed, though os.remove is often enough
from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest # Using pytest for fixtures like tmp_path

# Import the FastAPI app instance
from main import app, DATA_FILE as MAIN_DATA_FILE # Import original for safety, though we patch it

# Global test client
client = TestClient(app)

# Define a path for a temporary data file for testing
# Using pytest's tmp_path fixture is even better, will do that in test functions
TEST_DATA_FILENAME = "test_todos.json"

# Helper function to set up the data file for a test
def setup_test_data(test_data_path: str, data: dict):
    with open(test_data_path, "w") as f:
        json.dump(data, f, indent=4)

# Helper function to load data from the test file
def load_test_data(test_data_path: str) -> dict:
    try:
        with open(test_data_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Basic test to ensure the setup is working
def test_ping_server():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Todo API. Use /docs for API documentation."}

# Test cases for rename_user will be added below
# For now, let's add a simple placeholder for the first rename test

@pytest.fixture(autouse=True)
def manage_test_data_file(tmp_path):
    """
    Pytest fixture to automatically use a temporary file for DATA_FILE
    and clean it up after each test.
    """
    temp_file = tmp_path / TEST_DATA_FILENAME
    with patch('main.DATA_FILE', str(temp_file)):
        if os.path.exists(str(temp_file)): # Should not exist if tmp_path works as expected
            os.remove(str(temp_file))
        yield str(temp_file) # provide the path to the test if needed
        if os.path.exists(str(temp_file)):
            os.remove(str(temp_file))


def test_rename_user_success(manage_test_data_file):
    test_data_path = manage_test_data_file # Get the patched data file path

    initial_user_data = {
        "user1": [
            {"id": "todo1", "title": "Task 1", "description": "Description 1", "completed": False},
            {"id": "todo2", "title": "Task 2", "description": "Description 2", "completed": True},
        ],
        "another_user": [
            {"id": "todo3", "title": "Task 3", "description": "Description 3", "completed": False}
        ]
    }
    setup_test_data(test_data_path, initial_user_data)

    response = client.put("/users/user1/rename/newUser1")

    assert response.status_code == 200
    assert response.json() == {"message": "Username renamed successfully"}

    updated_data = load_test_data(test_data_path)
    assert "user1" not in updated_data
    assert "newUser1" in updated_data
    assert updated_data["newUser1"] == initial_user_data["user1"]
    assert "another_user" in updated_data # Ensure other users are not affected
    assert updated_data["another_user"] == initial_user_data["another_user"]


def test_rename_user_not_found(manage_test_data_file):
    test_data_path = manage_test_data_file
    setup_test_data(test_data_path, {"user1": []}) # Setup some initial data

    response = client.put("/users/nonexistentuser/rename/newname")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

    # Ensure data file is not changed for this user
    current_data = load_test_data(test_data_path)
    assert "nonexistentuser" not in current_data
    assert "newname" not in current_data
    assert "user1" in current_data


def test_rename_user_conflict(manage_test_data_file):
    test_data_path = manage_test_data_file
    initial_user_data = {
        "userA": [
            {"id": "todoA1", "title": "Task A1", "description": "Desc A1", "completed": False}
        ],
        "userB": [
            {"id": "todoB1", "title": "Task B1", "description": "Desc B1", "completed": True}
        ]
    }
    setup_test_data(test_data_path, initial_user_data)

    response = client.put("/users/userA/rename/userB")

    assert response.status_code == 409
    assert response.json() == {"detail": "New username already exists"}

    # Verify data is unchanged
    current_data = load_test_data(test_data_path)
    assert "userA" in current_data
    assert current_data["userA"] == initial_user_data["userA"]
    assert "userB" in current_data
    assert current_data["userB"] == initial_user_data["userB"]
    assert len(current_data) == 2 # No new users, no deleted users

# Example of how a test using tmp_path directly could look, if not using autouse fixture
# def test_rename_user_success_alt(tmp_path):
#     test_file_path = tmp_path / "test_todos.json"
#     with patch('main.DATA_FILE', str(test_file_path)):
#         # ... rest of the test logic ...
#         initial_user_data = {
#             "user1": [
#                 {"id": "todo1", "title": "Task 1", "description": "Description 1", "completed": False},
#             ]
#         }
#         setup_test_data(str(test_file_path), initial_user_data)
#         response = client.put("/users/user1/rename/newUser1")
#         assert response.status_code == 200
#         # ... more assertions ...
#         if os.path.exists(str(test_file_path)):
#             os.remove(str(test_file_path))

# Remember to install pytest and httpx if not already in requirements.txt
# pip install pytest httpx
# The main.py uses pydantic.TodoItem which converts data to TodoItem objects.
# The load_data in main.py converts dicts to TodoItem instances.
# The save_data in main.py converts TodoItem instances back to dicts.
# So the test_todos.json will store dicts, which is fine.
# The helper functions setup_test_data and load_test_data work with dicts.
# The application logic handles the Pydantic model conversion.
# The actual TodoItem model has default for id, so we provide it in tests for consistency.
# The TodoCreate model is used for creating/updating, so the fields match.
# The structure of data in initial_user_data for test_rename_user_success
# matches the structure of TodoItem model fields.
# {"id": "todo1", "title": "Task 1", "description": "Description 1", "completed": False}
# is compatible with TodoItem.
# The `TodoItem` in main.py uses `default_factory` for `id`, and `Field(...)` for `title`.
# `description` is `Optional`, `completed` defaults to `False`.
# The test data for todos should be a list of dictionaries, where each dict represents a TodoItem.
# This is what `initial_user_data["user1"]` is.
# The `load_data` in main.py will turn these dicts into `TodoItem` instances.
# The `save_data` in main.py will turn `TodoItem` instances back into dicts.
# So, the `load_test_data` helper is fine as it is, it will read the dicts written by `save_data`.
# The `setup_test_data` helper is also fine, as it writes dicts that `load_data` can parse into `TodoItem`s.
# All seems correct.
