import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from main import app, get_session
from models import Court

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

@pytest.fixture(autouse=True)
def setup_db():
    # Create tables before each test and drop them after
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
    # First, create a court directly
    client.post("/courts/", json={"name": "Court A", "city": "Tel Aviv", "num_courts": 1})
    
    response = client.get("/courts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Court A"

def test_update_court():
    """Test Update (PATCH)"""
    # 1. Create a court
    create_resp = client.post("/courts/", json={"name": "Old Name", "city": "Eilat", "num_courts": 1})
    court_id = create_resp.json()["id"]
    
    # 2. Update the court's name
    update_payload = {"name": "New Name"}
    update_resp = client.patch(f"/courts/{court_id}", json=update_payload)
    
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["name"] == "New Name"
    # City should remain the same
    assert data["city"] == "Eilat"

def test_delete_court():
    """Test Delete (DELETE)"""
    # 1. Create a court
    create_resp = client.post("/courts/", json={"name": "To Be Deleted", "city": "Jerusalem", "num_courts": 1})
    court_id = create_resp.json()["id"]
    
    # 2. Delete the court
    delete_resp = client.delete(f"/courts/{court_id}")
    assert delete_resp.status_code == 200
    
    # 3. Verify it's gone
    get_resp = client.get("/courts/")
    data = get_resp.json()
    assert len(data) == 0