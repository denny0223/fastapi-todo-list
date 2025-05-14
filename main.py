import json
import uuid
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, Path, Body
from pydantic import BaseModel, Field

app = FastAPI(
    title="Todo API",
    description="A simple API to manage user-specific todo lists.",
    version="1.0.0",
)

DATA_FILE = "todos.json"

class TodoItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="The unique identifier of the todo item.")
    title: str = Field(..., description="The title of the todo item.")
    description: Optional[str] = Field(None, description="An optional description of the todo item.")
    completed: bool = Field(False, description="Indicates whether the todo item is completed.")

class TodoCreate(BaseModel):
    title: str = Field(..., description="The title of the todo item.")
    description: Optional[str] = Field(None, description="An optional description of the todo item.")
    completed: bool = Field(False, description="Indicates whether the todo item is completed. Defaults to False.")

# Helper functions to load and save data
def load_data() -> Dict[str, List[TodoItem]]:
    try:
        with open(DATA_FILE, "r") as f:
            content = f.read()
            if not content:
                return {}
            data = json.loads(content)
            # Ensure todos are parsed into TodoItem models
            parsed_data = {}
            for user, todos_list in data.items():
                parsed_data[user] = [TodoItem(**todo) for todo in todos_list]
            return parsed_data
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {} # Or handle error appropriately

def save_data(data: Dict[str, List[TodoItem]]):
    # Convert TodoItem objects to dicts for JSON serialization
    serializable_data = {}
    for user, todos_list in data.items():
        serializable_data[user] = [todo.model_dump() for todo in todos_list]
    with open(DATA_FILE, "w") as f:
        json.dump(serializable_data, f, indent=4)

@app.post("/users/{username}/todos/", response_model=TodoItem, summary="Create a new todo item for a user", tags=["Todos"])
async def create_todo_for_user(
    username: str = Path(..., description="The username of the user for whom to create the todo."),
    todo_create: TodoCreate = Body(..., description="The todo item to create.")
):
    """
    Create a new todo item for a specific user.

    - **username**: The username of the user.
    - **todo_create**: The todo item details.
    """
    data = load_data()
    if username not in data:
        data[username] = []

    new_todo = TodoItem(title=todo_create.title, description=todo_create.description, completed=todo_create.completed)
    data[username].append(new_todo)
    save_data(data)
    return new_todo

@app.get("/users/{username}/todos/", response_model=List[TodoItem], summary="Get all todo items for a user", tags=["Todos"])
async def get_todos_for_user(
    username: str = Path(..., description="The username of the user whose todos to retrieve.")
):
    """
    Retrieve all todo items for a specific user.

    - **username**: The username of the user.
    """
    data = load_data()
    if username not in data:
        raise HTTPException(status_code=404, detail="User not found or no todos for this user")
    return data[username]

@app.get("/users/{username}/todos/{todo_id}", response_model=TodoItem, summary="Get a specific todo item for a user", tags=["Todos"])
async def get_todo_for_user(
    username: str = Path(..., description="The username of the user."),
    todo_id: str = Path(..., description="The ID of the todo item to retrieve.")
):
    """
    Retrieve a specific todo item by its ID for a specific user.

    - **username**: The username of the user.
    - **todo_id**: The unique identifier of the todo item.
    """
    data = load_data()
    if username not in data:
        raise HTTPException(status_code=404, detail="User not found")

    user_todos = data[username]
    for todo in user_todos:
        if todo.id == todo_id:
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")

@app.put("/users/{username}/todos/{todo_id}", response_model=TodoItem, summary="Update a todo item for a user", tags=["Todos"])
async def update_todo_for_user(
    username: str = Path(..., description="The username of the user."),
    todo_id: str = Path(..., description="The ID of the todo item to update."),
    todo_update: TodoCreate = Body(..., description="The updated todo item details.")
):
    """
    Update an existing todo item for a specific user.

    - **username**: The username of the user.
    - **todo_id**: The unique identifier of the todo item to update.
    - **todo_update**: The new details for the todo item.
    """
    data = load_data()
    if username not in data:
        raise HTTPException(status_code=404, detail="User not found")

    user_todos = data[username]
    for i, todo in enumerate(user_todos):
        if todo.id == todo_id:
            updated_todo = todo.model_copy(update=todo_update.model_dump(exclude_unset=True))
            user_todos[i] = updated_todo
            save_data(data)
            return updated_todo
    raise HTTPException(status_code=404, detail="Todo not found")

@app.delete("/users/{username}/todos/{todo_id}", response_model=dict, summary="Delete a todo item for a user", tags=["Todos"])
async def delete_todo_for_user(
    username: str = Path(..., description="The username of the user."),
    todo_id: str = Path(..., description="The ID of the todo item to delete.")
):
    """
    Delete a specific todo item by its ID for a specific user.

    - **username**: The username of the user.
    - **todo_id**: The unique identifier of the todo item to delete.
    """
    data = load_data()
    if username not in data:
        raise HTTPException(status_code=404, detail="User not found")

    user_todos = data[username]
    initial_len = len(user_todos)
    data[username] = [todo for todo in user_todos if todo.id != todo_id]

    if len(data[username]) == initial_len:
        raise HTTPException(status_code=404, detail="Todo not found")

    save_data(data)
    return {"message": "Todo deleted successfully"}

@app.get("/", summary="Root path", include_in_schema=False)
async def root():
    """
    Root endpoint of the API.

    Provides a welcome message and guidance to access the API documentation.
    """
    return {"message": "Welcome to the Todo API. Use /docs for API documentation."}
