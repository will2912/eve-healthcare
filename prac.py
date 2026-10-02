from fastapi import FastAPI, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import create_token, verifyToken, hash_password
from database import get_db
from models import User
from schemas import UserSignup, UserOut

@app.post("/auth/signup", response_model=UserOut, status_code=201)
def signup(
    data: UserSignup,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    hashed_password = hash_password(data.password)

    user = User(
        email=data.email,
        password_hash=hashed_password,
        full_name=data.full_name
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user