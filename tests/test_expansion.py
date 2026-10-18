"""Smoke tests for the RESCUEGRID page-expansion APIs."""

def test_donor_and_recipient_registration(client):
    donor = client.post('/registrations/donor', json={
        'name': 'Demo Donor', 'email': 'donor@example.org', 'organization': 'Sample Kitchen',
        'phone': '123456789', 'location': 'Demo City'
    })
    assert donor.status_code == 201
    assert donor.json()['role'] == 'donor'
    recipient = client.post('/registrations/recipient', json={
        'name': 'Demo Recipient', 'email': 'recipient@example.org', 'organization': 'Sample Shelter',
        'phone': '123456789', 'location': 'Demo City'
    })
    assert recipient.status_code == 201
    assert recipient.json()['role'] == 'recipient'
    assert len(client.get('/users').json()) == 2


def test_support_and_volunteer_forms_persist(client):
    support = client.post('/support', json={
        'name': 'Demo', 'email': 'demo@example.org', 'subject': 'Help', 'message': 'Question'
    })
    assert support.status_code == 201
    assert support.json()['status'] == 'open'
    volunteer = client.post('/volunteers', json={
        'name': 'Volunteer', 'email': 'vol@example.org', 'availability': 'Weekends', 'skills': 'Driving'
    })
    assert volunteer.status_code == 201
    assert client.get('/volunteers').json()[0]['email'] == 'vol@example.org'


def test_ai_endpoints_are_transparent(client):
    result = client.post('/ai/predict-urgency', json={
        'hours_until_expiry': 4, 'quantity': 20, 'category': 'cooked_meal'
    })
    assert result.status_code == 200
    body = result.json()
    assert body['model'].startswith('DecisionTreeClassifier')
    assert body['training_data'] == 'synthetic'
    assert 'macro_f1' in body['metrics']
    assistant = client.post('/ai/assistant', json={'question': 'What counts as rescued food?'})
    assert assistant.status_code == 200
    assert 'generated' in assistant.json()


def test_reservation_rejects_missing_donation(client):
    response = client.post('/reservations', json={
        'donation_id': 9999, 'recipient_name': 'Sample Org', 'portions': 1,
        'pickup_at': '2026-10-18T10:00:00+00:00'
    })
    assert response.status_code == 404
