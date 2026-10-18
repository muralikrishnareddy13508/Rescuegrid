"""PATCH /donations/{id}/status and the history endpoint."""

from tests.helpers import VALID


def make(client, **changes):
    response = client.post("/donations", json={**VALID, **changes})
    assert response.status_code == 201
    return response.json()


def unsafe(client):
    return make(client, temperature_controlled=False)  # goes to safety_review


def patch(client, donation_id, body):
    return client.patch(f"/donations/{donation_id}/status", json=body)


def test_review_decision_needs_a_reason(client):
    d = unsafe(client)
    assert patch(client, d["id"], {"status": "safety_cleared"}).status_code == 422
    assert patch(client, d["id"], {"status": "safety_cleared", "reason": "   "}).status_code == 422
    assert client.get(f"/donations/{d['id']}").json()["status"] == "safety_review"


def test_review_approval_with_reason_works_and_is_recorded(client):
    d = unsafe(client)
    response = patch(client, d["id"], {"status": "safety_cleared", "reason": "Checked on site"})
    assert response.status_code == 200
    assert response.json()["status"] == "safety_cleared"
    history = client.get(f"/donations/{d['id']}/history").json()
    assert history[-1]["to_status"] == "safety_cleared"
    assert history[-1]["reason"] == "Checked on site"


def test_review_rejection_with_reason(client):
    d = unsafe(client)
    response = patch(client, d["id"], {"status": "rejected_unsafe", "reason": "Not kept cold"})
    assert response.status_code == 200
    assert response.json()["status"] == "rejected_unsafe"


def test_matched_cannot_be_set_directly(client):
    d = make(client)
    assert patch(client, d["id"], {"status": "matched"}).status_code == 422


def test_invalid_jump_returns_409(client):
    d = make(client)
    assert patch(client, d["id"], {"status": "completed"}).status_code == 409


def test_unsafe_donation_cannot_skip_review(client):
    d = unsafe(client)
    assert patch(client, d["id"], {"status": "accepted"}).status_code == 409


def test_cancelled_is_final(client):
    d = make(client)
    assert patch(client, d["id"], {"status": "cancelled"}).status_code == 200
    assert patch(client, d["id"], {"status": "safety_cleared"}).status_code == 409


def test_missing_donation_returns_404(client):
    assert patch(client, 999, {"status": "cancelled"}).status_code == 404


def test_history_lists_events_in_order(client):
    d = make(client)
    patch(client, d["id"], {"status": "cancelled"})
    history = client.get(f"/donations/{d['id']}/history").json()
    assert [(e["from_status"], e["to_status"]) for e in history] == [
        ("registered", "safety_cleared"),
        ("safety_cleared", "cancelled"),
    ]


def test_status_update_rejects_unknown_fields(client):
    d = make(client)
    assert patch(client, d["id"], {"status": "cancelled", "owner": "x"}).status_code == 422


def test_history_of_missing_donation_returns_404(client):
    assert client.get("/donations/999/history").status_code == 404
