import jwt
import os
from fastapi import Request, HTTPException
from datetime import datetime, timedelta, timezone
# secret = "catisgood-this-is-a-longer-secret-key-123456"
secret= os.getenv("JWT_SECRET_KEY")
from dotenv import load_dotenv
from pwdlib import PasswordHash
load_dotenv()

password_hash = PasswordHash.recommended()

def hash_password(password: str):
    return password_hash.hash(password)

def create_token(userId:int):
    payload={
        "user_id":userId,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }

    encoded = jwt.encode(payload, secret, algorithm="HS256")
    return encoded

def verifyToken(req:Request):
    auth = req.headers.get("Authorization")
    if not auth:
        raise HTTPException(
            status=401,
            detail="no auth"
        )
    token = auth.split(" ")[1]

    try:
        decoded=jwt.decode(token, secret, algorithms=["HS256"])
        return decoded
    
    except jwt.InvalidTokenError:
        raise HTTPException(
             status_code=401,
            detail="token error"
        )


