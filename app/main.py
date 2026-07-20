from sqlalchemy.exc import OperationalError
import uvicorn
from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.models.user import User  # noqa: F401  # 注册模型到 Base.metadata
from app.routers import auth, users,chat
from fastapi.responses import JSONResponse
from app.core.exceptions import CustomException

Base.metadata.create_all(bind=engine)
app = FastAPI(title="lingnan-api")
###给应用加一个中间件，任何请求进出都会经过它
app.add_middleware(
    CORSMiddleware,##专门处理跨域响应头
    allow_origins=["*"],####允许任意前端域名访问
    allow_credentials=True,###允许带cookie凭证
    allow_methods=["*"],##允许任何请求方法
    allow_headers=["*"]###允许任意请求头
)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(chat.router)
@app.exception_handler(CustomException)
async def custom_exception_handler(request:Request,exp:CustomException):
    return JSONResponse(
        status_code=exp.status_code,
        content={"detail":exp.detail},
    )
@app.exception_handler(OperationalError)
async def database_exception_handler(request:Request,exc:OperationalError):
    return JSONResponse(
        status_code= 503 ,
        content={
            "detail":"Database connection failed. Please check if MySQL is running",
            "error_type":"DatabaseError",
        }

    )
@app.get("/health")
async def health():
    return {"status":"ok"}



if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
