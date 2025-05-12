from fastapi import FastAPI
from typing import Annotated
from fastapi import Form

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/login/")
async def login(username: Annotated[int, Form()], password: Annotated[str, Form()]):
    return {"username": username}


