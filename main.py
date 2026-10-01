from fastapi import FastAPI,Request,Depends, HTTPException
from auth import create_token , verifyToken ,hash_password

from model import User
from schema.schema import UserSignup, UserOut

from sqlalchemy.orm import Session
from database import get_db
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

@app.get("/test")
def testdb(db:Session=Depends(get_db)):
    return {"message":"db recieved"}
