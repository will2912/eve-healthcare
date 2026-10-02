# LabBooker

LabBooker is a FastAPI backend for diagnostic test booking. It provides user authentication, diagnostic test and centre lookup, appointment booking, mock payment processing, and idempotent payment webhooks.

## Features

* User signup and login
* JWT-based authentication
* Password hashing
* Diagnostic test search
* Diagnostic centre lookup
* Test pricing by diagnostic centre
* Authenticated test booking
* Mock payment processing
* Successful and failed payment handling
* Payment webhook handling
* Idempotent webhook processing
* PostgreSQL database
* SQLAlchemy ORM
* Alembic database migrations
* Automated API tests
* FastAPI Swagger/OpenAPI documentation

## Tech Stack

* Python
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* Pydantic
* JWT
* Argon2 password hashing
* Pytest

## Project Structure

```text
LabBooker/
├── alembic/
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/
│       └── 839c943f0f92_create_initial_tables.py
│
├── app/
│   ├── database.py
│   ├── main.py
│   ├── model.py
│   ├── security.py
│   │
│   ├── routers/
│   │   ├── auth.py
│   │   ├── booking.py
│   │   └── payment.py
│   │
│   └── schema/
│       └── schema.py
│
├── test/
│   └── test_api.py
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd LabBooker
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

On Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/labbooker
JWT_SECRET_KEY=your-secret-key
```

Replace the database credentials with the PostgreSQL credentials available in your local environment.

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the application

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

### Authentication

#### Signup

```http
POST /auth/signup
```

Example request:

```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "Test User"
}
```

#### Login

```http
POST /auth/login
```

Example request:

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

The login response returns a JWT access token.

---

### Diagnostic Tests

#### Search for a test

```http
GET /booking/tests?test=Blood
```

This searches for a diagnostic test by name.

#### Get centres offering a test

```http
GET /booking/centre?id=1
```

The response includes the diagnostic centres offering the requested test and the corresponding price.

---

### Booking

#### Create a booking

```http
POST /booking/booking
```

Authentication is required.

Header:

```text
Authorization: Bearer <access_token>
```

Example request:

```json
{
  "centre_id": 1,
  "test_id": 1,
  "appointment_at": "2026-10-05T10:30:00Z"
}
```

The booking amount is obtained from the centre-test relationship rather than being accepted directly from the client.

A new booking starts with:

```text
PENDING
```

---

### Payment

#### Create a mock payment

```http
POST /payment/payments/
```

Authentication is required.

Header:

```text
Authorization: Bearer <access_token>
```

Example request:

```json
{
  "booking_id": 1,
  "simulate_result": "SUCCESS"
}
```

The mock payment can simulate:

```text
SUCCESS
FAILED
```

A successful payment changes the booking status to:

```text
CONFIRMED
```

A failed payment changes the booking status to:

```text
FAILED
```

#### Payment Webhook

```http
POST /payment/payments/webhook/
```

Example request:

```json
{
  "event_id": "event_001",
  "provider_reference": "mock_payment_reference",
  "status": "SUCCESS"
}
```

Webhook events are identified using a unique `event_id`.

Repeated delivery of the same event is handled idempotently.

## Authentication

Protected endpoints require a JWT access token.

Example:

```text
Authorization: Bearer <access_token>
```

JWT tokens expire after 30 minutes.

Passwords are never stored directly. Passwords are hashed before being stored in the database.

## Database Schema

The main database entities are:

* `users`
* `diagnostic_centres`
* `diagnostic_tests`
* `centre_tests`
* `bookings`
* `payments`
* `webhook_events`

### Relationships

```text
User
 │
 └──< Booking
          │
          ├── DiagnosticCentre
          │
          ├── DiagnosticTest
          │
          └──< Payment


DiagnosticCentre
 │
 └──< CentreTest >── DiagnosticTest
```

`centre_tests` represents which diagnostic tests are available at which centres and stores the price for each centre-test combination.

The `(centre_id, test_id)` combination is unique to prevent duplicate centre-test relationships.

`webhook_events.event_id` is also unique to support idempotent webhook processing.

## Booking and Payment Flow

```text
Create Booking
      │
      ▼
   PENDING
      │
      ▼
 Mock Payment
   ┌──┴──┐
   │     │
SUCCESS FAILED
   │     │
   ▼     ▼
CONFIRMED FAILED
```

A payment also generates a unique provider reference.

Payment webhooks can subsequently update the payment and booking status.

## Webhook Idempotency

Payment webhooks can sometimes be delivered more than once.

To handle duplicate events, every webhook contains an `event_id`.

The application stores processed webhook events in the `webhook_events` table with a unique constraint on `event_id`.

If the same event is received again, the application returns a duplicate response instead of processing the event again.

## Edge Cases Handled

The API handles several invalid or unauthorized scenarios:

* Duplicate user signup
* Invalid login credentials
* Missing authentication
* Invalid or expired JWT
* Invalid centre/test combination
* Invalid booking ID
* Payment for another user's booking
* Payment for an already processed booking
* Invalid payment reference in a webhook
* Duplicate webhook events
* Failed payments

## Testing

Run the test suite with:

```bash
pytest
```

The test suite currently covers:

* User signup
* Duplicate signup
* User login
* Invalid login password
* Diagnostic test search
* Diagnostic centre lookup
* Authentication protection
* Booking creation
* Invalid centre/test booking
* Successful payment
* Failed payment
* Invalid booking payment
* Unauthorized payment attempt
* Payment webhook
* Duplicate webhook idempotency
* Invalid payment webhook

Current test result:

```text
16 passed
```

The tests use a separate SQLite test database and do not require the production PostgreSQL database.

## Database Migrations

Alembic is used for database schema migrations.

Apply migrations:

```bash
alembic upgrade head
```

Create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe changes"
```

Then apply it:

```bash
alembic upgrade head
```

## Assumptions

* Payment processing is mocked and does not connect to a real payment provider.
* Appointment availability or slot capacity is not implemented.
* Diagnostic centre and test management is represented through the database and migration data; dedicated admin CRUD APIs are not currently included.
* The booking amount is determined from the configured centre-test price.
* JWT access tokens expire after 30 minutes.
* PostgreSQL is used for the application database.
* SQLite is used only for automated tests.

## Possible Improvements

The following could be added in a production system:

* Redis caching
* Celery/background jobs
* Rate limiting
* Real payment provider integration
* Admin APIs for managing diagnostic centres and tests
* Appointment slot availability and capacity management
* Structured application logging
* Pagination
* Refresh tokens
* Payment retry handling
* Docker and Docker Compose deployment

## API Documentation

FastAPI automatically generates interactive API documentation.

After starting the application, open:

```text
http://127.0.0.1:8000/docs
```

The OpenAPI specification is also available through FastAPI's generated documentation.
