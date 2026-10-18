"""API endpoints used by the refreshed single-page frontend."""

from tests.helpers import VALID


def test_recipients_endpoint_returns_synthetic_profiles(client):
    response = client.get("/recipients")
    assert response.status_code == 200
    assert response.json()
    assert response.json()[0]["pickup_available"] is True


def test_matching_blocks_safety_review_donations(client):
    unsafe = client.post("/donations", json={**VALID, "packaging_intact": False}).json()
    response = client.get(f"/match-recipients/{unsafe['id']}")
    assert response.status_code == 409


def test_matching_returns_ranked_recipients_for_cleared_donation(client):
    donation = client.post("/donations", json=VALID).json()
    response = client.get(f"/match-recipients/{donation['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["donation"]["status"] == "safety_cleared"
    assert body["matches"]
    assert all("reason" in item and "score" in item for item in body["matches"])


def test_selecting_match_updates_status(client):
    donation = client.post("/donations", json=VALID).json()
    match = client.get(f"/match-recipients/{donation['id']}").json()["matches"][0]
    response = client.post(f"/donations/{donation['id']}/match", json={
        "recipient_id": match["recipient"]["id"]
    })
    assert response.status_code == 200
    assert response.json()["donation"]["status"] == "matched"


def test_impact_counts_only_completed_handoffs_as_rescued(client):
    client.post("/donations", json=VALID)
    body = client.get("/impact").json()
    assert body["registered_donations"] == 1
    assert body["completed_handoffs"] == 0
    assert body["quantity_completed"] == 0
