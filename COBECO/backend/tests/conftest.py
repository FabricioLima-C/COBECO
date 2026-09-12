import os
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.adapters.database import Database
from backend.adapters.repositories import MySQLStore
from backend.adapters.security import TokenSecurity
from backend.config import Settings
from backend.main import create_app
from backend.seed import seed


@pytest.fixture(scope="session")
def settings():
    if os.getenv("MYSQL_TEST") != "1":
        pytest.skip("MySQL integration: set MYSQL_TEST=1 and an isolated *_test database")
    result = Settings()
    if not result.mysql_database.endswith("_test"):
        pytest.fail("Integration tests require a database ending in _test")
    return result


@pytest.fixture(scope="session")
def database(settings):
    db = Database(settings)
    db.migrate()
    seed(db, settings)
    return db


@pytest.fixture(scope="session")
def security(settings):
    return TokenSecurity(settings.jwt_secret)


@pytest.fixture
def app(settings, database, security):
    return create_app(settings, MySQLStore(database), security)


@pytest.fixture
def client(app):
    with TestClient(app, base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture
def account(client):
    username = "test" + uuid.uuid4().hex[:12]
    data = {
        "username": username,
        "name": "Pessoa Teste",
        "email": f"{username}@example.com",
        "password": "Test-password-123!",
        "confirm_password": "Test-password-123!",
        "security_question": "Qual é o nome do projeto?",
        "security_answer": "COBECO",
    }
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 201, response.text
    return data


@pytest.fixture
def logged(client, account):
    response = client.post("/api/auth/login", json={k: account[k] for k in ("username", "password")})
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}
