"""Donations API: register, read, list, validate, and the safety rules at registration."""

import pytest

from tests.helpers import VALID, future


def test_create_donation_returns_201_and_saved_fields(client):
    response = client.post("/donations", json=VALID)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["status"] == "safety_cleared"
    assert body["safety_note"] is None
    assert body["food_name"] == "Day-old bread"
    assert body["category"] == "bakery"
    assert body["quantity"] == 12.5
    assert body["expiry_at"] == VALID["expiry_at"]
    assert body["pickup_at"] == VALID["pickup_at"]
    assert body["created_at"]
    assert body["prepared_on"] is None


def test_get_donation_returns_what_was_saved(client):
    created = client.post("/donations", json=VALID).json()
    response = client.get(f"/donations/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_missing_donation_returns_404(client):
    assert client.get("/donations/999").status_code == 404


def test_optional_prepared_on_is_saved(client):
    body = client.post("/donations", json={**VALID, "prepared_on": "2026-10-17"}).json()
    assert body["prepared_on"] == "2026-10-17"


def test_missing_safety_answers_go_to_review(client):
    payload = {k: v for k, v in VALID.items()
               if k not in ("temperature_controlled", "packaging_intact")}
    body = client.post("/donations", json=payload).json()
    assert body["status"] == "safety_review"
    assert "Missing answer" in body["safety_note"]
    assert body["temperature_controlled"] is None


def test_failed_safety_answer_goes_to_review(client):
    body = client.post("/donations", json={**VALID, "temperature_controlled": False}).json()
    assert body["status"] == "safety_review"
    assert 'Answered "No"' in body["safety_note"]
    assert body["temperature_controlled"] is False


def test_expired_food_goes_to_review(client):
    payload = {**VALID, "expiry_at": future(-5), "pickup_at": future(-10)}
    body = client.post("/donations", json=payload).json()
    assert body["status"] == "safety_review"
    assert "already passed" in body["safety_note"]


@pytest.mark.parametrize("missing", ["food_name", "donor_phone", "expiry_at", "pickup_at"])
def test_missing_required_field_returns_422(client, missing):
    payload = {key: value for key, value in VALID.items() if key != missing}
    assert client.post("/donations", json=payload).status_code == 422


@pytest.mark.parametrize(
    "field, bad_value",
    [
        ("quantity", 0),
        ("quantity", -5),
        ("category", "pizza_party"),
        ("unit", "tons"),
        ("expiry_at", "not-a-date"),
        ("food_name", "   "),
        ("donor_phone", "12"),
    ],
)
def test_invalid_values_are_rejected_and_not_saved(client, field, bad_value):
    response = client.post("/donations", json={**VALID, field: bad_value})
    assert response.status_code == 422
    assert client.get("/donations/1").status_code == 404


def test_pickup_after_expiry_is_rejected(client):
    payload = {**VALID, "pickup_at": future(72), "expiry_at": future(48)}
    assert client.post("/donations", json=payload).status_code == 422


def test_pickup_equal_to_expiry_is_rejected(client):
    same = future(24)
    assert client.post("/donations", json={**VALID, "pickup_at": same, "expiry_at": same}).status_code == 422


def test_mixing_timezone_and_no_timezone_is_rejected(client):
    payload = {**VALID, "expiry_at": "2030-01-02T10:00:00Z", "pickup_at": "2030-01-01T10:00:00"}
    assert client.post("/donations", json=payload).status_code == 422


def test_unknown_fields_are_rejected(client):
    # A donor must not be able to choose the status themselves.
    assert client.post("/donations", json={**VALID, "status": "completed"}).status_code == 422


def test_list_is_newest_first(client):
    client.post("/donations", json={**VALID, "food_name": "First"})
    client.post("/donations", json={**VALID, "food_name": "Second"})
    names = [d["food_name"] for d in client.get("/donations").json()]
    assert names == ["Second", "First"]


def test_list_can_filter_by_status(client):
    client.post("/donations", json=VALID)                                        # cleared
    client.post("/donations", json={**VALID, "packaging_intact": False})         # review
    reviews = client.get("/donations", params={"status": "safety_review"}).json()
    assert len(reviews) == 1 and reviews[0]["status"] == "safety_review"


def test_list_rejects_unknown_status(client):
    assert client.get("/donations", params={"status": "nonsense"}).status_code == 422
