from database import Base,get_db,engine
from fastapi import FastAPI,Depends,Query
from models import User
from sqlalchemy.orm import Session
import uvicorn
from pydantic import BaseModel,Field
from typing import Annotated
Base.metadata.create_all(bind=engine)

class UserCreateSchema(BaseModel):
    username : Annotated[str,Field(min_length = 3 ,max_length = 20)]
    password : Annotated[str,Field(min_length = 6 ,max_length = 30)]


app = FastAPI(title = "lingnang-api")


@app.post("/user")
async def creat_user(user :UserCreateSchema,db : Session = Depends(get_db)):
    db_user = User(username=user.username,password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message":"用户注册成功！","user":{"user_id":db_user.id,"user_username":db_user.username}}
    

@app.get("/user")
async def get_user(page: int = Query(1,ge=1),size : int = Query(10,ge=10,le=100),db :Session = Depends(get_db)):
    start = (page - 1) * size
    total = db.query(User).count()
    users = db.query(User).offset(start).limit(size).all()
    return {"total":total,"user":[{"user_id":u.id,"user_username":u.username,"user_created_at":u.created_at}for u in users]}

if __name__ == "__main__":
    uvicorn.run("Fastapi_practice:app",host="127.0.0.1",port=8000,reload=True)
