from fastapi import APIRouter, Depends ,Query
from sqlalchemy.orm import Session
from app.core.exceptions import CustomException, NotFoundException
from app.core.database import get_db
from app.crud import user as user_crud
from app.schemas.user import (
    UserCreateSchema,
    UserListResponseSchema,
    UserResponseSchema,
)
import json
from app.core.redis_client import redis_client
router = APIRouter(tags=["users"])


@router.post("/user", response_model=UserResponseSchema)
async def create_user(user: UserCreateSchema, db: Session = Depends(get_db)):
    existing = user_crud.get_user_by_username(db, user.username)
    if existing:
        raise CustomException(detail="用户名已存在",status_code=409)
    return user_crud.create_user(db, user)


@router.get("/user/{id}", response_model=UserResponseSchema)
async def get_user_by_id(id: int, db: Session = Depends(get_db)):
    cache_key = f"user:{id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    user = user_crud.get_user_by_id(db,id)
    if not user:
        raise NotFoundException()

    data =  UserResponseSchema.model_validate(user).model_dump(mode="json")
    redis_client.set(cache_key,json.dumps(data),ex=300)
    return data
    


@router.get("/user", response_model=UserListResponseSchema)
async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=10, le=100),
    db: Session = Depends(get_db),
):
    start = (page - 1) * size
    total = user_crud.count_users(db)
    users = user_crud.get_users(db, skip=start, limit=size)
    return {"total": total, "user": users}
