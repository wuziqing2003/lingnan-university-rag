from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import SQLALCHEMY_DATABASE_URL


###创建一个与mysql的链接
engine = create_engine(SQLALCHEMY_DATABASE_URL)
#创建一个数据库会话类
sessionlocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

##创建一个模型，用来创建数据库表
Base = declarative_base()
#创建一个数据库会话函数
def get_db():
    ##创建一个数据库会话类的实例
    db = sessionlocal()
    try:
        yield db ##yield是用来暂停的，但调用完毕之后，会自动关闭会话，并返回数据库会话实例
    finally:
        db.close() ##关闭数据库会话








