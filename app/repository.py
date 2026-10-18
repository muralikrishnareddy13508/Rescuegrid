"""Saving and loading donations in SQLite."""

import sqlite3
from contextlib import closing
from datetime import UTC, datetime

from app.database import get_connection
from app.safety import evaluate
from app.schemas import DonationCreate
from app.statuses import DonationStatus
from app.workflow import check_transition


class DonationNotFound(Exception):
    """No donation with that id."""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _bool_to_db(value: bool | None) -> int | None:
    return None if value is None else int(value)


def _db_to_bool(value: int | None) -> bool | None:
    return None if value is None else bool(value)


def _row_to_dict(row: sqlite3.Row) -> dict:
    donation = dict(row)
    donation["temperature_controlled"] = _db_to_bool(donation["temperature_controlled"])
    donation["packaging_intact"] = _db_to_bool(donation["packaging_intact"])
    return donation


def get_donation(donation_id: int) -> dict | None:
    with closing(get_connection()) as conn:
        row = conn.execute("SELECT * FROM donations WHERE id = ?", (donation_id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_donations(status: DonationStatus | None = None) -> list[dict]:
    """All donations, newest first. Optionally only one status."""
    query = "SELECT * FROM donations"
    params: tuple = ()
    if status is not None:
        query += " WHERE status = ?"
        params = (status.value,)
    query += " ORDER BY id DESC"
    with closing(get_connection()) as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def create_donation(data: DonationCreate) -> dict:
    """Run the safety rules, save the donation, and record the first status event."""
    status, note = evaluate(data.temperature_controlled, data.packaging_intact, data.expiry_at)
    created_at = _now()
    with closing(get_connection()) as conn:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO donations (
                    donor_name, donor_phone, food_name, category, quantity, unit,
                    prepared_on, expiry_at, pickup_address, pickup_at,
                    temperature_controlled, packaging_intact,
                    notes, status, safety_note, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data.donor_name,
                    data.donor_phone,
                    data.food_name,
                    data.category.value,
                    data.quantity,
                    data.unit.value,
                    data.prepared_on.isoformat() if data.prepared_on else None,
                    data.expiry_at.isoformat(),
                    data.pickup_address,
                    data.pickup_at.isoformat(),
                    _bool_to_db(data.temperature_controlled),
                    _bool_to_db(data.packaging_intact),
                    data.notes,
                    status.value,
                    note,
                    created_at,
                ),
            )
            donation_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO status_events (donation_id, from_status, to_status, reason, changed_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (donation_id, "registered", status.value,
                 note or "Automatic safety rules passed", created_at),
            )
    return get_donation(donation_id)


def change_status(donation_id: int, new_status: DonationStatus, reason: str | None, internal: bool = False) -> dict:
    """Apply an allowed status change and record it. Raises WorkflowError if not allowed."""
    with closing(get_connection()) as conn:
        with conn:  # rolls everything back if an error is raised inside
            row = conn.execute(
                "SELECT status FROM donations WHERE id = ?", (donation_id,)
            ).fetchone()
            if row is None:
                raise DonationNotFound(donation_id)
            check_transition(row["status"], new_status, reason, internal=internal)
            conn.execute(
                "UPDATE donations SET status = ? WHERE id = ?", (new_status.value, donation_id)
            )
            conn.execute(
                "INSERT INTO status_events (donation_id, from_status, to_status, reason, changed_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (donation_id, row["status"], new_status.value,
                 reason.strip() if reason else None, _now()),
            )
    return get_donation(donation_id)


def get_events(donation_id: int) -> list[dict]:
    """The status history of one donation, oldest first."""
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT from_status, to_status, reason, changed_at FROM status_events"
            " WHERE donation_id = ? ORDER BY id",
            (donation_id,),
        ).fetchall()
    return [dict(r) for r in rows]
