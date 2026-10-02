from fastapi import FastAPI,Request,Depends, HTTPException
from routers.auth import create_token , verifyToken ,hash_password

from model import User
from schema.schema import UserSignup, UserOut, UserLogin, Token

from sqlalchemy.orm import Session
from database import get_db
app = FastAPI()

@app.get('/')
def home():
    return{"hello": "world"}

@app.post('/login')
async def login(req:Request, db:Session = Depends(get_db)):
    body = await req.json()
    user = UserLogin.model_validate(body)
    hashed_password = hash_password(user.password)
    existing_user = db.query(User).filter(
        User.email == user.email,
        User.password_hash == hashed_password 
    )
    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail = "user not found"
        )
    token= create_token(user.email)
    print("token: ",token)
    return{"token :",token}

@app.get('/list')
async def listing(authenticated=Depends(verifyToken)):
    print(authenticated)
    return{
        "status":201,
        "message":"success"
    }

@app.get("/test")
def testdb(db:Session=Depends(get_db)):
    return {"message":"db recieved"}


@app.post("/signup",response_model=UserOut,status_code=201)
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
    
