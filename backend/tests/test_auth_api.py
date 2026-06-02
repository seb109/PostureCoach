from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTO_CREATE_TABLES"] = "false"
os.environ["JWT_SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.server import create_app
from app import models  # noqa: F401


engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app = create_app()
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_register_login_refresh_and_me():
    register = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "full_name": "Test User", "password": "password123"},
    )
    assert register.status_code == 201
    tokens = register.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"

    login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "password123"})
    assert login.status_code == 200

    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": login.json()["refresh_token"]})
    assert refresh.status_code == 200


def test_session_metric_report_flow():
    auth = client.post(
        "/api/v1/auth/register",
        json={"email": "flow@example.com", "full_name": "Flow User", "password": "password123"},
    ).json()
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    session = client.post("/api/v1/sessions/start", headers=headers)
    assert session.status_code == 200
    session_id = session.json()["session"]["id"]

    metric = client.post(
        "/api/v1/sessions/metrics",
        headers=headers,
        json={"session_id": session_id, "score": 91, "classification": "GOOD POSTURE", "ratio": 91},
    )
    assert metric.status_code == 200

    stopped = client.post(f"/api/v1/sessions/{session_id}/stop", headers=headers)
    assert stopped.status_code == 200
    assert stopped.json()["report_id"]

    reports = client.get("/api/v1/reports", headers=headers)
    assert reports.status_code == 200
    assert len(reports.json()) == 1
