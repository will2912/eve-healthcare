from fastapi import FastAPI,APIRouter, Request,Depends, HTTPException
from security import create_token , verifyToken ,hash_password, verify_password

from  model import User
from schema.schema import UserSignup, UserOut, UserLogin, Token

from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post('/login',response_model=Token)
async def login(req:Request , db:Session = Depends(get_db)):

    body = await req.json()
    print(body)
    user = UserLogin.model_validate(body)
    existing_user = db.query(User).filter(
        User.email == user.email,
    ).first()
    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail = "user not found"
        )
    if not verify_password(
        user.password,
        existing_user.password_hash
    ):
         raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token= create_token(existing_user.id)
    
    return Token(access_token=token)

@router.post("/signup",response_model=UserOut,status_code=201)
async def signup(req:Request,db:Session=Depends(get_db)):
    body=await req.json()
    user= UserSignup.model_validate(body)
    existing_user = db.query(User).filter(
        User.email==user.email
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="existing user"
        )
    hashed_password=hash_password(user.password)
    newUser = User(
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name
    )
    db.add(newUser)
    db.commit()
    db.refresh(newUser)

    return newUser
    
