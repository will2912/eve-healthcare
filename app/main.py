from fastapi import FastAPI,Request,Depends, HTTPException
from security import create_token , verifyToken ,hash_password
from routers import auth , booking
app = FastAPI()

@app.get('/')
def home():
    return{"hello": "world"}

app.include_router(auth.router)
app.include_router(booking.router)


@app.get('/list')
async def listing(authenticated=Depends(verifyToken)):
    print(authenticated)
    return{
        "status":201,
        "message":"success"
    }




