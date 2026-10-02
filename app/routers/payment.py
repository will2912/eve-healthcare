import random
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from model import Booking, Payment ,BOOKING_PENDING, BOOKING_FAILED, BOOKING_CONFIRMED
from schema.schema import PaymentCreate, PaymentResult
from database import get_db
from security import verifyToken


router = APIRouter(prefix="/payment", tags=["pay"])
@router.post("/payments/", response_model=PaymentResult)
async def createPayment(data: PaymentCreate,req: Request,db: Session = Depends(get_db)):
    decoded = verifyToken(req)
    user_id = decoded["user_id"]
    booking = db.query(Booking).filter(
        Booking.id == data.booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if booking.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to pay for this booking"
        )

    if booking.status != BOOKING_PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Booking is already {booking.status}"
        )

    if data.simulate_result:
        payment_status = data.simulate_result
    else:
        payment_status = random.choice(["SUCCESS", "FAILED"])

    provider_reference = f"mock_{uuid.uuid4().hex}"

    payment = Payment(
        booking_id=booking.id,
        amount=booking.amount,
        status=payment_status,
        provider_reference=provider_reference
    )

    if payment_status == "SUCCESS":
        booking.status = BOOKING_CONFIRMED
    else:
        booking.status = BOOKING_FAILED

    db.add(payment)
    db.commit()

    db.refresh(payment)
    db.refresh(booking)

    return PaymentResult(
        payment=payment,
        booking=booking
    )