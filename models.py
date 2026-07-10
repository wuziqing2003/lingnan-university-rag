from database import Base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"
    id  =  Column(Integer,primary_key=True,autoincrement=True,comment="用户ID")
    username = Column(String(50),unique=True,nullable=False,comment="用户名")
    password = Column(String(255),nullable=False,comment="用户密码")
    created_at = Column(DateTime,default=func.now(),comment="创建时间")


