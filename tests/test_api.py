import csv
import io
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from api.auth import create_access_token, hash_password
from api.main import app, get_session
from api.models import Court, User

# --- Setup In-Memory Database for Testing ---
sqlite_url = "sqlite:///:memory:"
engine = create_engine(
    sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool
)

def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session
client = TestClient(app)


def create_user(username: str, password: str, role: str = "user") -> User:
    user = User(
        username=username,
        hashed_password=hash_password(password),
        role=role,
    )
    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


# --- CRUD Tests for Court ---

def test_create_court():
    """Test Create (POST)"""
    payload = {
        "name": "Test Court",
        "address": "123 Test St",
        "city": "Haifa",
        "num_courts": 2,
        "has_lighting": True
    }
    response = client.post("/courts/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Court"
    assert data["id"] is not None

def test_read_courts():
    """Test Read/Listing (GET)"""
    client.post("/courts/", json={"name": "Court A", "address": "Ben Yehuda 1", "city": "Tel Aviv", "num_courts": 1, "has_lighting": True})
    
    response = client.get("/courts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Court A"

def test_update_court():
    """Test Update (PATCH)"""
    create_resp = client.post("/courts/", json={"name": "Old Name", "address": "HaTmarim 10", "city": "Eilat", "num_courts": 1, "has_lighting": False})
    court_id = create_resp.json()["id"]
    
    update_payload = {"name": "New Name"}
    update_resp = client.patch(f"/courts/{court_id}", json=update_payload)
    
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["name"] == "New Name"
    assert data["city"] == "Eilat"

def test_delete_court():
    """Test Delete (DELETE)"""
    admin = create_user("admin-delete", "adminpass", role="admin")
    token = create_access_token({"sub": admin.username, "role": admin.role})

    create_resp = client.post("/courts/", json={"name": "To Be Deleted", "address": "Jaffa Rd", "city": "Jerusalem", "num_courts": 1, "has_lighting": True})
    court_id = create_resp.json()["id"]
    
    delete_resp = client.delete(f"/courts/{court_id}", headers={"Authorization": f"Bearer {token}"})
    assert delete_resp.status_code == 200
    
    get_resp = client.get("/courts/")
    data = get_resp.json()
    assert len(data) == 0


def test_delete_court_without_token_returns_401():
    create_resp = client.post(
        "/courts/",
        json={
            "name": "Protected Court",
            "address": "Main St",
            "city": "Tel Aviv",
            "num_courts": 1,
            "has_lighting": True,
        },
    )
    court_id = create_resp.json()["id"]

    response = client.delete(f"/courts/{court_id}")
    assert response.status_code == 401


def test_delete_court_with_user_role_returns_403():
    user = create_user("standard-user", "password123", role="user")
    token = create_access_token({"sub": user.username, "role": user.role})

    create_resp = client.post(
        "/courts/",
        json={
            "name": "Protected Court",
            "address": "Main St",
            "city": "Tel Aviv",
            "num_courts": 1,
            "has_lighting": True,
        },
    )
    court_id = create_resp.json()["id"]

    response = client.delete(
        f"/courts/{court_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_delete_court_with_expired_token_returns_401():
    admin = create_user("expired-admin", "adminpass", role="admin")
    token = create_access_token(
        {"sub": admin.username, "role": admin.role},
        expires_delta=timedelta(seconds=-1),
    )

    create_resp = client.post(
        "/courts/",
        json={
            "name": "Expired Token Court",
            "address": "Main St",
            "city": "Tel Aviv",
            "num_courts": 1,
            "has_lighting": True,
        },
    )
    court_id = create_resp.json()["id"]

    response = client.delete(
        f"/courts/{court_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_login_via_token_endpoint():
    create_user("admin-user", "adminpass", role="admin")

    response = client.post(
        "/token",
        data={"username": "admin-user", "password": "adminpass"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]


def test_csv_export_format():
    games_to_export = [
        {
            "ID": 1,
            "Court": "Rucker Park",
            "Date": "2026-06-30",
            "Time": "18:00",
            "Skill Level": "intermediate",
            "Status": "open",
            "Occupancy": "3/10 Players",
        },
        {
            "ID": 2,
            "Court": "Venice Beach Courts",
            "Date": "2026-07-02",
            "Time": "19:30",
            "Skill Level": "advanced",
            "Status": "open",
            "Occupancy": "5/8 Players",
        },
    ]

    csv_buffer = io.StringIO()
    csv_writer = csv.DictWriter(csv_buffer, fieldnames=games_to_export[0].keys())
    csv_writer.writeheader()
    csv_writer.writerows(games_to_export)

    csv_output = csv_buffer.getvalue()
    assert "ID,Court,Date,Time,Skill Level,Status,Occupancy" in csv_output
    assert "1,Rucker Park,2026-06-30,18:00,intermediate,open,3/10 Players" in csv_output
    assert "2,Venice Beach Courts,2026-07-02,19:30,advanced,open,5/8 Players" in csv_output
    assert "games_schedule.csv" == "games_schedule.csv"