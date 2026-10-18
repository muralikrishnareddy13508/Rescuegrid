"""Safety rules: plain logic, no web server needed."""

from datetime import UTC, datetime, timedelta

from app.safety import evaluate
from app.statuses import DonationStatus as S

NOW = datetime(2026, 10, 17, 12, 0)
LATER = NOW + timedelta(hours=5)


def test_both_yes_and_not_expired_is_cleared():
    status, note = evaluate(True, True, LATER, now=NOW)
    assert status == S.safety_cleared
    assert note is None


def test_missing_temperature_answer_goes_to_review():
    status, note = evaluate(None, True, LATER, now=NOW)
    assert status == S.safety_review
    assert "safe temperature" in note


def test_failed_packaging_answer_goes_to_review():
    status, note = evaluate(True, False, LATER, now=NOW)
    assert status == S.safety_review
    assert "intact packaging" in note


def test_expired_food_goes_to_review():
    status, note = evaluate(True, True, NOW - timedelta(hours=1), now=NOW)
    assert status == S.safety_review
    assert "already passed" in note


def test_all_problems_are_listed_together():
    status, note = evaluate(None, False, NOW - timedelta(hours=1), now=NOW)
    assert status == S.safety_review
    assert "safe temperature" in note and "intact packaging" in note and "already passed" in note


def test_timezone_aware_expiry_does_not_crash():
    far_future = datetime(2100, 1, 1, tzinfo=UTC)
    status, note = evaluate(True, True, far_future)
    assert status == S.safety_cleared
