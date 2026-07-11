from database import Base,get_db,engine
from fastapi import FastAPI,Depends,Query
from models import User
from sqlalchemy.orm import Session
import uvicorn
from pydantic import BaseModel,Field
from typing import Annotated
from datetime import datetime
from fastapi import HTTPException
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



app = FastAPI(title = "lingnang-api")


@app.post("/user",response_model=UserResponseSchema)
async def creat_user(user :UserCreateSchema,db : Session = Depends(get_db)):
    db_user = User(username=user.username,password=user.password)
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




@app.get("/user")
async def get_user(page: int = Query(1,ge=1),size : int = Query(10,ge=10,le=100),db :Session = Depends(get_db)):
    start = (page - 1) * size
    total = db.query(User).count()
    users = db.query(User).offset(start).limit(size).all()
    return {"total":total,"user":[{"user_id":u.id,"user_username":u.username,"user_created_at":u.created_at}for u in users]}

if __name__ == "__main__":
    uvicorn.run("Fastapi_practice:app",host="127.0.0.1",port=8000,reload=True)
