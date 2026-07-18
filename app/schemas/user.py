from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class UserCreateSchema(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=20)]
    password: Annotated[str, Field(min_length=6, max_length=30)]


class UserResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class UserListResponseSchema(BaseModel):
    total: int
    user: list[UserResponseSchema]


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"

