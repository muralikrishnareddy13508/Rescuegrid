"""Tests for Milestone 1: /health and SQLite setup."""

import pytest
from fastapi.testclient import TestClient

from app.database import SCHEMA_VERSION, get_schema_version, init_db
from app.main import app


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Point the app at a temporary database so tests never touch real data."""
    path = tmp_path / "test_rescuegrid.db"
    monkeypatch.setenv("RESCUEGRID_DB_PATH", str(path))
    return path


def test_health_returns_ok(db_path):
    # "with" makes the server start up (and create the database) like for real.
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "RESCUEGRID"
    assert body["database"] == "ok"
    assert body["data_mode"] == "synthetic prototype"


def test_startup_creates_database_with_schema_version(db_path):
    assert not db_path.exists()
    with TestClient(app):
        pass
    assert db_path.exists()
    assert get_schema_version() == SCHEMA_VERSION


def test_init_db_can_run_twice(db_path):
    init_db()
    init_db()  # must not crash or create duplicates
    assert get_schema_version() == SCHEMA_VERSION


def test_health_reports_503_when_database_unavailable(tmp_path, monkeypatch):
    # A folder cannot be opened as a database file, so this simulates a failure.
    monkeypatch.setenv("RESCUEGRID_DB_PATH", str(tmp_path))
    client = TestClient(app)  # no "with": startup is skipped on purpose
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["database"] == "unavailable"