import uvicorn
from fastapi import FastAPI

from app.core.database import Base, engine
from app.models.user import User  # noqa: F401  # 注册模型到 Base.metadata
from app.routers import auth, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="lingnan-api")
app.include_router(users.router)
app.include_router(auth.router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
