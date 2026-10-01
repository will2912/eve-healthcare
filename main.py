from fastapi import FastAPI,Request,Depends
from auth import create_token , verifyToken

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker
load_dotenv()

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

app = FastAPI()

@app.get('/')
def home():
    return{"hello": "world"}

@app.post('/login')
async def login(req:Request):
    data = await req.json()
    userId = data["userId"]
    token= create_token(userId)
    print("token: ",token)
    return{"token":token}

@app.get('/list')
async def listing(authenticated=Depends(verifyToken)):
    print(authenticated)
    return{
        "status":201,
        "message":"success"
    }


