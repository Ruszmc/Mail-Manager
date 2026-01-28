from fastapi.testclient import TestClient
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db
from app.db import Base
from app.crypto import encrypt

# Use a separate test database
TEST_DB_URL = "sqlite:///./test_mailpilot.db"

import sqlalchemy
engine = sqlalchemy.create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def setup_module():
    Base.metadata.create_all(bind=engine)

def teardown_module():
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_mailpilot.db"):
        os.remove("./test_mailpilot.db")

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True

def test_create_account():
    response = client.post(
        "/accounts",
        json={
            "email": "test@example.com",
            "password": "password123",
            "imap_host": "imap.example.com",
            "imap_port": 993,
            "imap_tls": True
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_list_accounts():
    response = client.get("/accounts")
    assert response.status_code == 200
    assert len(response.json()) >= 1
