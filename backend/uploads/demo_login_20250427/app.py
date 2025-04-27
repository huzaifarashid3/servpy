# Demo microservice: login
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(req: LoginRequest):
    if req.username == "admin" and req.password == "password":
        return {"status": "success", "token": "demo-token"}
    return {"status": "error", "message": "Invalid credentials"}


@app.get("/")
def root():
    return {"message": "Demo login microservice is running!"}
