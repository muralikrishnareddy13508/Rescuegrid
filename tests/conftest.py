import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A test client using a temporary database, so real data is never touched."""
    monkeypatch.setenv("RESCUEGRID_DB_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as test_client:
        yield test_client
