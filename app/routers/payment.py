import random
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from model import Booking, Payment ,BOOKING_PENDING, BOOKING_FAILED, BOOKING_CONFIRMED ,WebhookEvent
from schema.schema import PaymentCreate, PaymentResult, WebhookResponse, WebhookPayload
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




@router.post("/payments/webhook/", response_model=WebhookResponse)
async def paymentWebhook(
    data: WebhookPayload,
    db: Session = Depends(get_db)
):
    existing_event = db.query(WebhookEvent).filter(
        WebhookEvent.event_id == data.event_id
    ).first()

    if existing_event:
        return WebhookResponse(
            result="duplicate",
            message="Webhook event already processed"
        )

    payment = db.query(Payment).filter(
        Payment.provider_reference == data.provider_reference
    ).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    webhook_event = WebhookEvent(
        event_id=data.event_id,
        payload=data.model_dump()
    )

    db.add(webhook_event)

    payment.status = data.status

    booking = payment.booking

    if data.status == "SUCCESS":
        booking.status = BOOKING_CONFIRMED
    else:
        booking.status = BOOKING_FAILED

    db.commit()

    return WebhookResponse(
        result="processed",
        message="Webhook processed successfully"
    )