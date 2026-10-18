"""SQLite helpers for RESCUEGRID (uses Python's built-in sqlite3 module)."""

import sqlite3
from contextlib import closing

from app.config import get_db_path

SCHEMA_VERSION = "3"


def get_connection() -> sqlite3.Connection:
    """Open a connection to the database, creating the data folder if needed."""
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create the tables and record the schema version.

    PROTOTYPE ONLY: there are no migrations. If the stored schema version is
    different from SCHEMA_VERSION, the donations tables are dropped and rebuilt
    (the data is synthetic test data). With the same version nothing is touched.
    """
    with closing(get_connection()) as conn:
        with conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            row = conn.execute(
                "SELECT value FROM app_meta WHERE key = 'schema_version'"
            ).fetchone()
            if row and row["value"] != SCHEMA_VERSION:
                conn.execute("DROP TABLE IF EXISTS status_events")
                conn.execute("DROP TABLE IF EXISTS donations")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS donations (
                    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                    donor_name             TEXT NOT NULL,
                    donor_phone            TEXT NOT NULL,
                    food_name              TEXT NOT NULL,
                    category               TEXT NOT NULL,
                    quantity               REAL NOT NULL CHECK (quantity > 0),
                    unit                   TEXT NOT NULL,
                    prepared_on            TEXT,
                    expiry_at              TEXT NOT NULL,
                    pickup_address         TEXT NOT NULL,
                    pickup_at              TEXT NOT NULL,
                    temperature_controlled INTEGER CHECK (temperature_controlled IN (0, 1)),
                    packaging_intact       INTEGER CHECK (packaging_intact IN (0, 1)),
                    notes                  TEXT,
                    status                 TEXT NOT NULL,
                    safety_note            TEXT,
                    created_at             TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS status_events (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    donation_id INTEGER NOT NULL REFERENCES donations(id),
                    from_status TEXT,
                    to_status   TEXT NOT NULL,
                    reason      TEXT,
                    changed_at  TEXT NOT NULL
                )
                """
            )
            # Expansion tables are additive; keep existing donations and audit history intact.
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
                    role TEXT NOT NULL DEFAULT 'donor', phone TEXT, organization TEXT, location TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, donation_id INTEGER NOT NULL REFERENCES donations(id),
                    recipient_name TEXT NOT NULL, portions REAL NOT NULL CHECK(portions > 0),
                    pickup_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'reserved', created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS support_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL,
                    subject TEXT NOT NULL, message TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS volunteer_signups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL,
                    availability TEXT NOT NULL, skills TEXT, created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "INSERT OR REPLACE INTO app_meta (key, value) VALUES ('schema_version', ?)",
                (SCHEMA_VERSION,),
            )


def get_schema_version() -> str | None:
    """Return the stored schema version, or None if it is not there."""
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT value FROM app_meta WHERE key = 'schema_version'"
        ).fetchone()
    return row["value"] if row else None


def check_database() -> bool:
    """Return True if we can open the database and run a trivial query."""
    try:
        with closing(get_connection()) as conn:
            conn.execute("SELECT 1").fetchone()
        return True
    except (sqlite3.Error, OSError):
        return False
