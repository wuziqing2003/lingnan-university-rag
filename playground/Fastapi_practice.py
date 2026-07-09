from fastapi import FastAPI, Query
import uvicorn
from pydantic import BaseModel,Field
from typing import Annotated

# 数据库
FADE_DB : list[dict] = [] 
# 用户注册模型
class UserCreateSchema(BaseModel):
    username : Annotated[str,Field(min_length=3,max_length=20)]
    password : Annotated[str,Field(min_length=6,max_length=30)]

# 创建FastAPI实例
app = FastAPI(title="lingnan")

# 用户注册接口
@app.post("/user")
async def users(users : list[UserCreateSchema]):
    for user in users:
        FADE_DB.append(user.model_dump())
    return {"message":"用户注册成功!!","user":users}
# 用户查询接口
@app.get("/user")
async def get_user(page: int = Query(1,ge=1),size : int = Query(10,ge=10,le=100)):
    start=(page-1)*size
    end = start + size
    return {"total" : len(FADE_DB),"user" : FADE_DB[start:end]}

if __name__ == "__main__":
    uvicorn.run("Fastapi_practice:app",host ="127.0.0.1",port=8000,reload=True)