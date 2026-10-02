import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-at-least-32-bytes-long"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db
from model import DiagnosticCentre, DiagnosticTest, CentreTest


TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def setup_database():
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    centre = DiagnosticCentre(
        name="City Diagnostics",
        address="Main Road",
        city="Delhi",
        is_active=True,
    )

    test = DiagnosticTest(
        name="Blood Test",
        description="Basic blood test",
    )

    db.add(centre)
    db.add(test)
    db.commit()

    db.refresh(centre)
    db.refresh(test)

    centre_test = CentreTest(
        centre_id=centre.id,
        test_id=test.id,
        price=500.00,
    )

    db.add(centre_test)
    db.commit()

    db.close()


def teardown_database():
    Base.metadata.drop_all(bind=engine)


def setup_function():
    setup_database()


def teardown_function():
    teardown_database()


def create_user(email="test@example.com"):
    response = client.post(
        "/auth/signup",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 201

    return response.json()


def login_user(email="test@example.com"):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def create_booking(token):
    return client.post(
        "/booking/booking",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "centre_id": 1,
            "test_id": 1,
            "appointment_at": "2026-10-05T10:30:00Z",
        },
    )


def test_signup():
    response = client.post(
        "/auth/signup",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "user@example.com"
    assert data["full_name"] == "Test User"
    assert "password_hash" not in data


def test_duplicate_signup():
    create_user()

    response = client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Another User",
        },
    )

    assert response.status_code == 409


def test_login():
    create_user()

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    create_user()

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_search_test():
    response = client.get(
        "/booking/tests",
        params={"test": "Blood"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Blood Test"


def test_get_centres_for_test():
    response = client.get(
        "/booking/centre",
        params={"id": 1},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert float(data[0]["price"]) == 500.00


def test_booking_requires_authentication():
    response = client.post(
        "/booking/booking",
        json={
            "centre_id": 1,
            "test_id": 1,
            "appointment_at": "2026-10-05T10:30:00Z",
        },
    )

    assert response.status_code == 401


def test_create_booking():
    create_user()

    token = login_user()

    response = create_booking(token)

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == 1
    assert data["centre_id"] == 1
    assert data["test_id"] == 1
    assert float(data["amount"]) == 500.00
    assert data["status"] == "PENDING"


def test_booking_with_invalid_centre_test():
    create_user()

    token = login_user()

    response = client.post(
        "/booking/booking",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "centre_id": 999,
            "test_id": 999,
            "appointment_at": "2026-10-05T10:30:00Z",
        },
    )

    assert response.status_code == 404


def test_successful_payment():
    create_user()

    token = login_user()

    booking_response = create_booking(token)

    booking_id = booking_response.json()["id"]

    response = client.post(
        "/payment/payments/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "booking_id": booking_id,
            "simulate_result": "SUCCESS",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment"]["status"] == "SUCCESS"
    assert data["booking"]["status"] == "CONFIRMED"
    assert data["payment"]["amount"] == "500.00"


def test_failed_payment():
    create_user()

    token = login_user()

    booking_response = create_booking(token)

    booking_id = booking_response.json()["id"]

    response = client.post(
        "/payment/payments/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "booking_id": booking_id,
            "simulate_result": "FAILED",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment"]["status"] == "FAILED"
    assert data["booking"]["status"] == "FAILED"


def test_payment_invalid_booking():
    create_user()

    token = login_user()

    response = client.post(
        "/payment/payments/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "booking_id": 999,
            "simulate_result": "SUCCESS",
        },
    )

    assert response.status_code == 404


def test_user_cannot_pay_for_another_users_booking():
    create_user("user1@example.com")

    token1 = login_user("user1@example.com")

    booking_response = create_booking(token1)

    booking_id = booking_response.json()["id"]

    create_user("user2@example.com")

    token2 = login_user("user2@example.com")

    response = client.post(
        "/payment/payments/",
        headers={
            "Authorization": f"Bearer {token2}"
        },
        json={
            "booking_id": booking_id,
            "simulate_result": "SUCCESS",
        },
    )

    assert response.status_code == 403


def test_payment_webhook():
    create_user()

    token = login_user()

    booking_response = create_booking(token)

    booking_id = booking_response.json()["id"]

    payment_response = client.post(
        "/payment/payments/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "booking_id": booking_id,
            "simulate_result": "FAILED",
        },
    )

    payment_data = payment_response.json()

    provider_reference = payment_data["payment"]["provider_reference"]

    response = client.post(
        "/payment/payments/webhook/",
        json={
            "event_id": "event_001",
            "provider_reference": provider_reference,
            "status": "SUCCESS",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["result"] == "processed"


def test_duplicate_webhook_is_idempotent():
    create_user()

    token = login_user()

    booking_response = create_booking(token)

    booking_id = booking_response.json()["id"]

    payment_response = client.post(
        "/payment/payments/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "booking_id": booking_id,
            "simulate_result": "FAILED",
        },
    )

    provider_reference = payment_response.json()["payment"]["provider_reference"]

    webhook = {
        "event_id": "event_duplicate",
        "provider_reference": provider_reference,
        "status": "SUCCESS",
    }

    first_response = client.post(
        "/payment/payments/webhook/",
        json=webhook,
    )

    second_response = client.post(
        "/payment/payments/webhook/",
        json=webhook,
    )

    assert first_response.status_code == 200
    assert first_response.json()["result"] == "processed"

    assert second_response.status_code == 200
    assert second_response.json()["result"] == "duplicate"


def test_webhook_invalid_payment():
    response = client.post(
        "/payment/payments/webhook/",
        json={
            "event_id": "event_invalid",
            "provider_reference": "does_not_exist",
            "status": "SUCCESS",
        },
    )

    assert response.status_code == 404