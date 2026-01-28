import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet

os.environ.setdefault("MP_FERNET_KEY", Fernet.generate_key().decode("utf-8"))

from app.main import app, get_db
from app.db import Base
from app.models import Thread, Message

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
            "imap_tls": True,
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_tls": True
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_create_account_with_autodiscovery():
    response = client.post(
        "/accounts",
        json={
            "email": "user@gmail.com",
            "password": "password123"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["imap_host"] == "imap.gmail.com"

def test_list_accounts():
    response = client.get("/accounts")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_thread_insights():
    db = TestingSessionLocal()
    try:
        thread = Thread(
            account_id=1,
            provider_thread_key="subject::example.com",
            subject="Rechnung für Oktober",
            category="finance",
            priority_score=50,
            is_newsletter=False,
        )
        db.add(thread)
        db.flush()
        msg = Message(
            thread_id=thread.id,
            imap_uid=123,
            subject=thread.subject,
            snippet="Anbei die Rechnung. Bitte Zahlung bis zum 15.10.",
        )
        db.add(msg)
        db.commit()
    finally:
        db.close()

    response = client.get(f"/threads/{thread.id}/insights")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "actions" in data
    assert "labels" in data
