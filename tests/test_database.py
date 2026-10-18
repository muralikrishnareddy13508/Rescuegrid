"""Database setup: keeps data normally, rebuilds only when the schema version changes."""

import sqlite3
from contextlib import closing

from app import database
from tests.helpers import VALID


def test_init_db_keeps_data_when_version_is_unchanged(client):
    client.post("/donations", json=VALID)
    database.init_db()
    assert client.get("/donations/1").status_code == 200


def test_older_schema_is_rebuilt(tmp_path, monkeypatch):
    path = tmp_path / "old.db"
    monkeypatch.setenv("RESCUEGRID_DB_PATH", str(path))
    with closing(sqlite3.connect(path)) as conn:
        with conn:
            conn.execute("CREATE TABLE app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            conn.execute("INSERT INTO app_meta VALUES ('schema_version', '2')")
            conn.execute("CREATE TABLE donations (id INTEGER PRIMARY KEY, old_column TEXT)")
    database.init_db()
    assert database.get_schema_version() == database.SCHEMA_VERSION
    with closing(sqlite3.connect(path)) as conn:
        columns = [row[1] for row in conn.execute("PRAGMA table_info(donations)")]
    assert "safety_note" in columns and "old_column" not in columns
