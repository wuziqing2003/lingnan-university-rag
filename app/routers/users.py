from fastapi import APIRouter, Depends ,Query
from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundException
from app.core.database import get_db
from app.crud import user as user_crud
from app.schemas.user import (
    UserCreateSchema,
    UserListResponseSchema,
    UserResponseSchema,
)
import json
from app.core.reids_client import redis_client
router = APIRouter(tags=["users"])


@router.post("/user", response_model=UserResponseSchema)
async def create_user(user: UserCreateSchema, db: Session = Depends(get_db)):
    existing = user_crud.get_user_by_username(db, user.username)
    if existing:
        raise NotFoundException()
    return user_crud.create_user(db, user)


@router.get("/user/{id}", response_model=UserResponseSchema)
async def get_user_by_id(id: int, db: Session = Depends(get_db)):
##创建一个键名
    cache_key = f"user:{id}"
###通过键获取值
    cached = redis_client.get(cache_key)
##如果值存在就将json格式的字符串转变为字典输出
    if cached:
        return json.loads(cached)



###如果不存在就去mysql里通过id去寻找User的实例对象
    user = user_crud.get_user_by_id(db, id)
##如果不存在这个实例对象就报错
    if not user:
        raise NotFoundException()
###如果存在就将找到的这个user套输出模版，并且将他从实例对象转换为json兼容的字典
    data = UserResponseSchema.model_validate(user).model_dump(mode="json")
###然后将data转换为字符串且作为值，cache_key作为键，并且设置过期时间300秒，然后存入redis中
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
