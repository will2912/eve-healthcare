from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ORMModel(BaseModel):
    """Base for response schemas: lets Pydantic read SQLAlchemy objects directly."""
    model_config = ConfigDict(from_attributes=True)

class UserSignup(BaseModel):                      
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=120)


class UserLogin(BaseModel):                       # POST /auth/login
    email: EmailStr
    password: str


class UserOut(ORMModel):                          # response (never includes password)
    id: int
    email: EmailStr
    full_name: str
    is_admin: bool
    created_at: datetime


class Token(BaseModel):                           # response of login
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# 2. Diagnostic tests
# ---------------------------------------------------------------------------
class TestCreate(BaseModel):                      # POST /tests/   (admin)
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)


class TestOut(ORMModel):
    id: int
    name: str
    description: str | None = None

class TestSearchOut(BaseModel):
    id: int
    name: str
    description: str | None = None


# ---------------------------------------------------------------------------
# 3. Diagnostic centres
# ---------------------------------------------------------------------------
class CentreCreate(BaseModel):                    # POST /centres/   (admin)
    name: str = Field(min_length=1, max_length=150)
    address: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=80)



class CentreOut(ORMModel):                        # used in list responses
    id: int
    name: str
    address: str
    city: str
    is_active: bool

class CentreForTestOut(ORMModel):
    centre: CentreOut
    price: Decimal


class CentreTestCreate(BaseModel):                # POST /centres/{centre_id}/tests   (admin)
    test_id: int
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class CentreTestOut(ORMModel):                    # a test offered by a centre, with price
    test: TestOut
    price: Decimal


class CentreDetailOut(CentreOut):                 # GET /centres/{id}  -> centre + its tests
    tests: list[CentreTestOut] = []


# ---------------------------------------------------------------------------
# 4. Bookings
# ---------------------------------------------------------------------------
BookingStatusLiteral = Literal["PENDING", "CONFIRMED", "FAILED", "CANCELLED"]


class BookingCreate(BaseModel):                   # POST /bookings/
    centre_id: int
    test_id: int
    appointment_at: datetime

    @field_validator("appointment_at")
    @classmethod
    def must_be_in_future(cls, value: datetime) -> datetime:
        # treat naive datetimes as UTC so the comparison never crashes
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        if value <= datetime.now(timezone.utc):
            raise ValueError("appointment_at must be in the future")
        return value


class BookingOut(ORMModel):                       # GET /bookings/, GET /bookings/{id}
    id: int
    user_id: int
    centre_id: int
    test_id: int
    appointment_at: datetime
    amount: Decimal
    status: BookingStatusLiteral
    created_at: datetime


# ---------------------------------------------------------------------------
# 5. Simulated payments
# ---------------------------------------------------------------------------
class PaymentCreate(BaseModel):                   # POST /payments/
    booking_id: int
    # optional: force an outcome (handy for tests); if omitted the server picks randomly
    simulate_result: Literal["SUCCESS", "FAILED"] | None = None


class PaymentOut(ORMModel):
    id: int
    booking_id: int
    amount: Decimal
    status: Literal["SUCCESS", "FAILED"]
    provider_reference: str
    created_at: datetime


class PaymentResult(BaseModel):                   # response of POST /payments/
    payment: PaymentOut
    booking: BookingOut


# ---------------------------------------------------------------------------
# 6. Webhook
# ---------------------------------------------------------------------------
class WebhookPayload(BaseModel):                  # POST /payments/webhook/
    event_id: str = Field(min_length=1, max_length=100)            # unique per event -> idempotency key
    provider_reference: str = Field(min_length=1, max_length=100)  # matches payments.provider_reference
    status: Literal["SUCCESS", "FAILED"]


class WebhookResponse(BaseModel):
    # "processed" = applied, "duplicate" = already seen, "ignored" = valid but no state change
    result: Literal["processed", "duplicate", "ignored"]
    message: str | None = None


# ---------------------------------------------------------------------------
# 7. Shared helpers
# ---------------------------------------------------------------------------
class Message(BaseModel):                         # simple responses, e.g. cancel booking
    detail: str


class Page(BaseModel):                            # optional pagination query model
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)