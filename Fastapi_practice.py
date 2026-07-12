from database import Base,get_db,engine
from fastapi import FastAPI,Depends,Query,status
from models import User
from sqlalchemy.orm import Session
import uvicorn
from pydantic import BaseModel,Field
from typing import Annotated
from datetime import datetime
from fastapi import HTTPException
from auth import hash_password
from fastapi.security import OAuth2PasswordRequestForm
from auth import verify_password,create_access_token,get_current_user
Base.metadata.create_all(bind=engine)

class UserCreateSchema(BaseModel):
    username : Annotated[str,Field(min_length = 3 ,max_length = 20)]
    password : Annotated[str,Field(min_length = 6 ,max_length = 30)]

class UserResponseSchema(BaseModel):
    id : int
    username : str
    created_at : datetime
    class Config:
        from_attributes = True
class UserlistResponseSchema(BaseModel):
    total : int 
    user:list[UserResponseSchema]

class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"



app = FastAPI(title = "lingnang-api")


@app.post("/user",response_model=UserResponseSchema)
async def creat_user(user :UserCreateSchema,db : Session = Depends(get_db)):
    db_user = User(username=user.username,password_hash=hash_password(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
@app.get("/user/{id}",response_model=UserResponseSchema)
async def get_user_by_id(id : int ,db : Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user

@app.post("/login",response_model=TokenSchema)
async def login(form_data:OAuth2PasswordRequestForm=Depends(),db:Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password,user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"}

        )
    access_token = create_access_token(data={"sub":user.username})
    return {"access_token":access_token,"token_type":"bearer"}
    


@app.get("/profile",response_model=UserResponseSchema)
async def read_profile(current_user:User=Depends(get_current_user)):
    return current_user

@app.get("/user",response_model=UserlistResponseSchema)
async def get_user(page: int = Query(1,ge=1),size : int = Query(10,ge=10,le=100),db :Session = Depends(get_db)):
    start = (page - 1) * size
    total = db.query(User).count()
    users = db.query(User).offset(start).limit(size).all()
    return {"total":total,"user": users}

if __name__ == "__main__":
    uvicorn.run("Fastapi_practice:app",host="127.0.0.1",port=8000,reload=True)
    