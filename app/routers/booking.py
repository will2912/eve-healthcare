from fastapi import FastAPI,APIRouter, Request,Depends, HTTPException
from security import create_token , verifyToken ,hash_password, verify_password

from  model import User,DiagnosticTest, CentreTest, Booking
from schema.schema import TestSearchOut , TestOut , CentreForTestOut, CentreTestOut, BookingCreate

from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(prefix="/booking", tags=["Booking"])

@router.get('/tests',response_model=TestOut)
async def getTests(test:str, db:Session = Depends(get_db)):
    testData = db.query(DiagnosticTest).filter(
        DiagnosticTest.name.ilike(f"%{test}%")
    ).first()

    if not testData:
        raise HTTPException(
            status_code=405,
            detail="test not found"
        )
    return testData

@router.get('/centre',response_model=list[CentreForTestOut])
async def getCentreForTest(id:int,db:Session = Depends(get_db)):
    centres = db.query(CentreTest).filter(
        CentreTest.test_id==id
    ).all()
    if not centres:
            raise HTTPException(
                status_code=405,
                detail="centres with this test not found"
            )
    return centres

@router.post('/booking')
async def createBooking(data: BookingCreate, req: Request, db: Session = Depends(get_db)):
    decoded = verifyToken(req)
    user_id = decoded["user_id"]


    centre_test = db.query(CentreTest).filter(
        CentreTest.centre_id == data.centre_id,
        CentreTest.test_id == data.test_id
    ).first()

    if not centre_test:
        raise HTTPException(
            status_code=404,
            detail="This centre does not offer this test"
        )

    booking = Booking(
        user_id=user_id,
        centre_id=data.centre_id,
        test_id=data.test_id,
        appointment_at=data.appointment_at,
        amount=centre_test.price
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return booking
     
