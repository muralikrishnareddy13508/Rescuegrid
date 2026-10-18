"""RESCUEGRID API: Milestone 3 (donations, safety rules, status workflow, serves the website)."""

from contextlib import asynccontextmanager, closing
from datetime import datetime, timezone
import re

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR
from app.database import check_database, get_connection, init_db
from app.ai_assistant import generate_answer
from app.urgency_model import predict as predict_urgency
from app.repository import (
    DonationNotFound,
    change_status,
    create_donation,
    get_donation,
    get_events,
    list_donations,
)
from app.schemas import DonationCreate, DonationOut, StatusUpdate
from app.statuses import DonationStatus
from app.workflow import InvalidTransition, WorkflowError

APP_VERSION = "0.3.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # make sure the database exists when the server starts
    yield


app = FastAPI(
    title="RESCUEGRID API",
    version=APP_VERSION,
    description="AI-assisted food rescue platform (synthetic-data prototype).",
    lifespan=lifespan,
)


@app.get("/health")
def health(response: Response) -> dict:
    db_ok = check_database()
    if not db_ok:
        response.status_code = 503
    return {
        "status": "ok" if db_ok else "degraded",
        "service": "RESCUEGRID",
        "version": APP_VERSION,
        "database": "ok" if db_ok else "unavailable",
        "data_mode": "synthetic prototype",
    }


@app.post("/donations", response_model=DonationOut, status_code=201)
def register_donation(donation: DonationCreate) -> dict:
    """Register a donation. The safety rules decide its first status."""
    return create_donation(donation)


@app.get("/donations", response_model=list[DonationOut])
def list_all_donations(status: DonationStatus | None = None) -> list[dict]:
    """All donations, newest first. Use ?status=safety_review to filter."""
    return list_donations(status)


@app.get("/donations/{donation_id}", response_model=DonationOut)
def read_donation(donation_id: int) -> dict:
    donation = get_donation(donation_id)
    if donation is None:
        raise HTTPException(status_code=404, detail="Donation not found")
    return donation


@app.patch("/donations/{donation_id}/status", response_model=DonationOut)
def update_status(donation_id: int, update: StatusUpdate) -> dict:
    """Change a donation's status, only along allowed paths."""
    try:
        return change_status(donation_id, update.status, update.reason)
    except DonationNotFound:
        raise HTTPException(status_code=404, detail="Donation not found")
    except InvalidTransition as error:
        raise HTTPException(status_code=409, detail=str(error))
    except WorkflowError as error:
        raise HTTPException(status_code=422, detail=str(error))


@app.get("/donations/{donation_id}/history")
def donation_history(donation_id: int) -> list[dict]:
    """Every status change of one donation (an audit trail)."""
    if get_donation(donation_id) is None:
        raise HTTPException(status_code=404, detail="Donation not found")
    return get_events(donation_id)




# Synthetic recipient profiles for the datathon demo. Replace with verified,
# database-backed organizations before any real-world use.
RECIPIENTS = [
    {"id": 1, "name": "Annapurna Community Kitchen", "type": "Community kitchen",
     "location": "North district", "accepted_categories": ["cooked_meal", "produce", "bakery", "packaged"],
     "capacity_by_unit": {"kg": 100, "portions": 100, "items": 100}, "current_demand": 80, "pickup_available": True},
    {"id": 2, "name": "Hope Shelter", "type": "Shelter",
     "location": "East district", "accepted_categories": ["cooked_meal", "bakery", "dairy", "packaged"],
     "capacity_by_unit": {"kg": 45, "portions": 45, "items": 45}, "current_demand": 40, "pickup_available": True},
    {"id": 3, "name": "Green Valley Home", "type": "Community care home",
     "location": "South district", "accepted_categories": ["produce", "dairy", "packaged"],
     "capacity_by_unit": {"kg": 35, "portions": 35, "items": 35}, "current_demand": 28, "pickup_available": True},
    {"id": 4, "name": "Food for All Center", "type": "Relief organization",
     "location": "Central district", "accepted_categories": ["cooked_meal", "produce", "bakery", "dairy", "packaged", "beverage"],
     "capacity_by_unit": {"kg": 75, "portions": 75, "items": 75}, "current_demand": 60, "pickup_available": False},
]


class MatchRequest(BaseModel):
    recipient_id: int = Field(gt=0)


def rank_recipients(donation: dict) -> list[dict]:
    """Explainable synthetic ranking; food-safety eligibility is checked first."""
    results = []
    for recipient in RECIPIENTS:
        compatible = donation["category"] in recipient["accepted_categories"]
        capacity = recipient["capacity_by_unit"].get(donation["unit"], 0)
        capacity_ok = float(donation["quantity"]) <= capacity
        pickup_ok = bool(recipient["pickup_available"])
        if not (compatible and capacity_ok and pickup_ok):
            continue
        # Transparent prototype score, not a trained AI prediction.
        demand_score = min(100, round(100 * recipient["current_demand"] /
                                      max(capacity, 1)))
        score = round(0.45 * 100 + 0.35 * min(100, 100 * capacity /
                                             max(float(donation["quantity"]), 1)) / 1.0 * 0.5
                      + 0.20 * demand_score)
        score = max(1, min(100, score))
        results.append({
            "recipient": recipient,
            "score": score,
            "reason": (
                f"Accepts {donation['category']}; capacity is sufficient "
                f"({capacity} {donation['unit']}); pickup is available; "
                f"current demand is {recipient['current_demand']}."
            ),
        })
    return sorted(results, key=lambda item: item["score"], reverse=True)


@app.get("/recipients")
def list_recipients() -> list[dict]:
    """Synthetic recipients for demonstration only."""
    return RECIPIENTS


@app.get("/match-recipients/{donation_id}")
def match_recipients(donation_id: int) -> dict:
    donation = get_donation(donation_id)
    if donation is None:
        raise HTTPException(status_code=404, detail="Donation not found")
    if donation["status"] not in (DonationStatus.safety_cleared, DonationStatus.matched,
                                  DonationStatus.accepted):
        raise HTTPException(
            status_code=409,
            detail="Only safety-cleared donations can be matched; this donation is not eligible.",
        )
    return {"donation": donation, "matches": rank_recipients(donation),
            "note": "Synthetic recipient profiles and prototype scores; verify real capacity and pickup."}


@app.post("/donations/{donation_id}/match")
def select_recipient(donation_id: int, request: MatchRequest) -> dict:
    donation = get_donation(donation_id)
    if donation is None:
        raise HTTPException(status_code=404, detail="Donation not found")
    if donation["status"] != DonationStatus.safety_cleared:
        raise HTTPException(status_code=409, detail="Donation must be safety-cleared and not already matched.")
    ranked = rank_recipients(donation)
    selected = next((item for item in ranked if item["recipient"]["id"] == request.recipient_id), None)
    if selected is None:
        raise HTTPException(status_code=422, detail="Recipient is incompatible, lacks capacity, or cannot pick up.")
    try:
        updated = change_status(donation_id, DonationStatus.matched,
                                f"Matched to synthetic recipient {selected['recipient']['name']}",
                                internal=True)
    except (InvalidTransition, WorkflowError) as error:
        raise HTTPException(status_code=409, detail=str(error))
    return {"donation": updated, "match": selected,
            "note": "Synthetic recipient match; no real organization has been notified."}


@app.get("/impact")
def impact_metrics() -> dict:
    all_donations = list_donations()
    status_counts = {}
    for donation in all_donations:
        status_counts[donation["status"]] = status_counts.get(donation["status"], 0) + 1
    completed = [d for d in all_donations if d["status"] == DonationStatus.completed]
    # Units can differ, so totals are reported as quantities rather than falsely labelled kg.
    return {
        "registered_donations": len(all_donations),
        "quantity_registered": round(sum(float(d["quantity"]) for d in all_donations), 2),
        "completed_handoffs": len(completed),
        "quantity_completed": round(sum(float(d["quantity"]) for d in completed), 2),
        "status_counts": status_counts,
        "data_mode": "synthetic prototype",
        "quantity_warning": "Quantities may use mixed units; totals are not kilograms.",
    }


# --- Expansion endpoints: registrations, reservations, support, volunteer, insights ---
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _required(body: dict, *keys: str) -> None:
    for key in keys:
        if not str(body.get(key, '')).strip():
            raise HTTPException(status_code=422, detail=f"{key} is required")

def _rows(sql: str, params: tuple = ()) -> list[dict]:
    with closing(get_connection()) as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]

def _one(sql: str, params: tuple = ()) -> dict | None:
    with closing(get_connection()) as conn:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None

@app.post('/registrations/donor', status_code=201)
def register_donor(body: dict) -> dict:
    _required(body, 'name', 'email', 'organization', 'phone', 'location')
    email = str(body['email']).strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=422, detail='Enter a valid email address')
    try:
        with closing(get_connection()) as conn, conn:
            cur = conn.execute('INSERT INTO users(name,email,role,phone,organization,location,created_at) VALUES(?,?,?,?,?,?,?)',
                (str(body['name']).strip(), email, 'donor', str(body['phone']).strip(), str(body['organization']).strip(), str(body['location']).strip(), _now()))
            uid = cur.lastrowid
    except Exception as exc:
        if 'UNIQUE' in str(exc): raise HTTPException(status_code=409, detail='An account with this email already exists')
        raise
    return _one('SELECT id,name,email,role,phone,organization,location,created_at FROM users WHERE id=?', (uid,))

@app.post('/registrations/recipient', status_code=201)
def register_recipient_org(body: dict) -> dict:
    _required(body, 'name', 'email', 'organization', 'phone', 'location')
    email = str(body['email']).strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=422, detail='Enter a valid email address')
    try:
        with closing(get_connection()) as conn, conn:
            cur = conn.execute('INSERT INTO users(name,email,role,phone,organization,location,created_at) VALUES(?,?,?,?,?,?,?)',
                (str(body['name']).strip(), email, 'recipient', str(body['phone']).strip(), str(body['organization']).strip(), str(body['location']).strip(), _now()))
            uid = cur.lastrowid
    except Exception as exc:
        if 'UNIQUE' in str(exc): raise HTTPException(status_code=409, detail='An account with this email already exists')
        raise
    return _one('SELECT id,name,email,role,phone,organization,location,created_at FROM users WHERE id=?', (uid,))

@app.get('/users')
def list_users() -> list[dict]:
    return _rows('SELECT id,name,email,role,phone,organization,location,created_at FROM users ORDER BY id DESC')

@app.get('/users/{user_id}')
def read_user(user_id: int) -> dict:
    user_row = _one('SELECT id,name,email,role,phone,organization,location,created_at FROM users WHERE id=?', (user_id,))
    if not user_row: raise HTTPException(status_code=404, detail='User not found')
    return user_row

@app.patch('/users/{user_id}')
def update_user(user_id: int, body: dict) -> dict:
    allowed = {'name','phone','organization','location'}
    changes = {k: str(v).strip() for k,v in body.items() if k in allowed and v is not None}
    if not changes: raise HTTPException(status_code=422, detail='Provide at least one editable field')
    if not _one('SELECT id FROM users WHERE id=?', (user_id,)): raise HTTPException(status_code=404, detail='User not found')
    with closing(get_connection()) as conn, conn:
        conn.execute('UPDATE users SET ' + ','.join(f'{k}=?' for k in changes) + ' WHERE id=?', (*changes.values(), user_id))
    return read_user(user_id)

@app.post('/reservations', status_code=201)
def create_reservation(body: dict) -> dict:
    _required(body, 'recipient_name', 'pickup_at')
    try: donation_id = int(body.get('donation_id', 0)); portions = float(body.get('portions', 0))
    except (TypeError, ValueError): raise HTTPException(status_code=422, detail='Donation ID and portions must be numeric')
    donation = get_donation(donation_id)
    if donation is None: raise HTTPException(status_code=404, detail='Donation not found')
    if donation['status'] != DonationStatus.safety_cleared: raise HTTPException(status_code=409, detail='Only safety-cleared donations can be reserved')
    if portions <= 0 or portions > float(donation['quantity']): raise HTTPException(status_code=422, detail='Portions must be positive and cannot exceed the listed donation quantity')
    pickup = str(body['pickup_at'])
    try:
        with closing(get_connection()) as conn, conn:
            cur=conn.execute('INSERT INTO reservations(donation_id,recipient_name,portions,pickup_at,status,created_at) VALUES(?,?,?,?,?,?)', (donation_id,str(body['recipient_name']).strip(),portions,pickup,'reserved',_now()))
            rid=cur.lastrowid
    except Exception as exc: raise HTTPException(status_code=422, detail=str(exc))
    return _one('SELECT * FROM reservations WHERE id=?', (rid,))

@app.get('/reservations')
def list_reservations() -> list[dict]:
    return _rows('SELECT * FROM reservations ORDER BY id DESC')

@app.get('/donations/{donation_id}/reservations')
def donation_reservations(donation_id: int) -> list[dict]:
    if get_donation(donation_id) is None: raise HTTPException(status_code=404, detail='Donation not found')
    return _rows('SELECT * FROM reservations WHERE donation_id=? ORDER BY id DESC', (donation_id,))

@app.post('/support', status_code=201)
def create_support_request(body: dict) -> dict:
    _required(body, 'name', 'email', 'subject', 'message')
    if len(str(body['message'])) > 3000: raise HTTPException(status_code=422, detail='Message must be 3000 characters or fewer')
    with closing(get_connection()) as conn, conn:
        cur=conn.execute('INSERT INTO support_requests(name,email,subject,message,status,created_at) VALUES(?,?,?,?,?,?)', (str(body['name']).strip(),str(body['email']).strip(),str(body['subject']).strip(),str(body['message']).strip(),'open',_now()))
        rid=cur.lastrowid
    return _one('SELECT * FROM support_requests WHERE id=?', (rid,))

@app.get('/support')
def list_support_requests() -> list[dict]:
    return _rows('SELECT * FROM support_requests ORDER BY id DESC')

@app.post('/volunteers', status_code=201)
def signup_volunteer(body: dict) -> dict:
    _required(body, 'name', 'email', 'availability')
    with closing(get_connection()) as conn, conn:
        cur=conn.execute('INSERT INTO volunteer_signups(name,email,availability,skills,created_at) VALUES(?,?,?,?,?)', (str(body['name']).strip(),str(body['email']).strip(),str(body['availability']).strip(),str(body.get('skills','')).strip(),_now()))
        vid=cur.lastrowid
    return _one('SELECT * FROM volunteer_signups WHERE id=?', (vid,))

@app.get('/volunteers')
def list_volunteers() -> list[dict]:
    return _rows('SELECT * FROM volunteer_signups ORDER BY id DESC')

@app.post('/ai/predict-urgency')
def predict_donation_urgency(body: dict) -> dict:
    try:
        hours=float(body.get('hours_until_expiry'))
        quantity=float(body.get('quantity', 1))
        category=str(body.get('category', 'other'))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail='hours_until_expiry and quantity must be numeric')
    if hours < 0 or quantity <= 0: raise HTTPException(status_code=422, detail='hours_until_expiry must be non-negative and quantity must be positive')
    codes={'cooked_meal':0,'produce':1,'bakery':2,'dairy':3,'packaged':4,'beverage':5,'other':6}
    return predict_urgency(hours, quantity, codes.get(category,6))

@app.post('/ai/assistant')
def ai_assistant(body: dict) -> dict:
    question=str(body.get('question','')).strip()
    if not question: raise HTTPException(status_code=422, detail='question is required')
    return generate_answer(question)

@app.get('/ai/insights')
def ai_insights() -> dict:
    all_donations=list_donations()
    now=datetime.now(timezone.utc)
    urgency=[]
    for d in all_donations:
        if d['status'] not in (DonationStatus.safety_cleared,): continue
        try:
            expiry=datetime.fromisoformat(str(d['expiry_at']).replace('Z','+00:00'))
            if expiry.tzinfo is None: expiry=expiry.replace(tzinfo=timezone.utc)
            hours=max(0,(expiry-now).total_seconds()/3600)
        except Exception: hours=999
        level='high' if hours <= 6 else 'medium' if hours <= 24 else 'low'
        urgency.append({'donation_id':d['id'],'food_name':d['food_name'],'hours_until_expiry':round(hours,1),'urgency':level,'method':'transparent expiry-time baseline, not a trained model'})
    model_predictions=[]
    category_codes={'cooked_meal':0,'produce':1,'bakery':2,'dairy':3,'packaged':4,'beverage':5,'other':6}
    for d in all_donations:
        if d['status'] != DonationStatus.safety_cleared: continue
        try:
            expiry=datetime.fromisoformat(str(d['expiry_at']).replace('Z','+00:00'))
            if expiry.tzinfo is None: expiry=expiry.replace(tzinfo=timezone.utc)
            hours=max(0,(expiry-now).total_seconds()/3600)
            result=predict_urgency(hours,float(d['quantity']),category_codes.get(str(d['category']),6))
            model_predictions.append({'donation_id':d['id'],'food_name':d['food_name'],'hours_until_expiry':round(hours,1),'prediction':result['urgency'],'probabilities':result['probabilities']})
        except Exception: continue
    _, model_metrics = __import__('app.urgency_model', fromlist=['_trained'])._trained()
    return {'data_mode':'live database records where available; no invented totals','urgency_predictions':sorted(urgency,key=lambda x:x['hours_until_expiry']), 'model_predictions':model_predictions, 'model_metrics':model_metrics, 'method_note':'Time-to-expiry baseline and a DecisionTree model trained on synthetic data are shown separately. Synthetic-data metrics are not real-world performance. Safety eligibility remains a separate hard-rule process.', 'assistant_mode':'configured OpenAI-compatible endpoint if configured; otherwise transparent fallback'}

@app.get('/admin/overview')
def admin_overview() -> dict:
    return {'users':_rows('SELECT id,name,email,role,organization,location,created_at FROM users ORDER BY id DESC'), 'donations':list_donations(), 'organizations':_rows('SELECT id,name,email,role,organization,location,created_at FROM users WHERE organization IS NOT NULL ORDER BY id DESC'), 'support_requests':_rows('SELECT * FROM support_requests ORDER BY id DESC'), 'data_mode':'demo workspace; endpoint is not protected by production authentication'}

# Serve the website. This MUST stay last so the API routes above win.
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
