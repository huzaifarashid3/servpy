import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_list_microservices():
    response = client.get("/list-microservices")
    assert response.status_code == 200
    assert "microservices" in response.json()
