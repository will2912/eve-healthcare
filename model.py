from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def utcnow():
    return datetime.now(timezone.utc)


# Status values are plain strings (easy to read and use in the API)
BOOKING_PENDING = "PENDING"
BOOKING_CONFIRMED = "CONFIRMED"
BOOKING_FAILED = "FAILED"
BOOKING_CANCELLED = "CANCELLED"

PAYMENT_SUCCESS = "SUCCESS"
PAYMENT_FAILED = "FAILED"


# 1. Users
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")


# 2. Diagnostic centres
class DiagnosticCentre(Base):
    __tablename__ = "diagnostic_centres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    address: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(80), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tests: Mapped[list["CentreTest"]] = relationship(back_populates="centre")


# 3. Diagnostic tests (catalogue, no price here)
class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))

    centres: Mapped[list["CentreTest"]] = relationship(back_populates="test")


# 4. Which centre offers which test, and at what price
class CentreTest(Base):
    __tablename__ = "centre_tests"
    # the same test cannot be listed twice for one centre
    __table_args__ = (UniqueConstraint("centre_id", "test_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    centre_id: Mapped[int] = mapped_column(ForeignKey("diagnostic_centres.id"))
    test_id: Mapped[int] = mapped_column(ForeignKey("diagnostic_tests.id"))
    price: Mapped[float] = mapped_column(Numeric(10, 2))

    centre: Mapped["DiagnosticCentre"] = relationship(back_populates="tests")
    test: Mapped["DiagnosticTest"] = relationship(back_populates="centres")


# 5. Bookings
class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    centre_id: Mapped[int] = mapped_column(ForeignKey("diagnostic_centres.id"))
    test_id: Mapped[int] = mapped_column(ForeignKey("diagnostic_tests.id"))
    appointment_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))  # price copied at booking time
    status: Mapped[str] = mapped_column(String(20), default=BOOKING_PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="bookings")
    centre: Mapped["DiagnosticCentre"] = relationship()
    test: Mapped["DiagnosticTest"] = relationship()
    payments: Mapped[list["Payment"]] = relationship(back_populates="booking")


# 6. Payments (one booking can have many attempts)
class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), index=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20))  # SUCCESS or FAILED
    provider_reference: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    booking: Mapped["Booking"] = relationship(back_populates="payments")


# 7. Webhook events (used to ignore duplicate webhooks)
class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(100), unique=True)  # makes webhook idempotent
    payload: Mapped[dict] = mapped_column(JSON)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)