from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_db
from models import User
from sqlalchemy.orm import Session
###创建密码加密器
pwd_comtext = CryptContext(schemes=["bcrypt"],deprecated="auto")

##告诉Fastapi：Token从哪拿
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


#将明文密码变成哈希
def hash_password(password: str) -> str:
    return pwd_comtext.hash(password)

###将用户输入的密码和数据库里存的那串哈希码做对比，输出bool
def verify_password(plain_password:str,password_hash:str)->bool:
    return pwd_comtext.verify(plain_password,password_hash)




##生成jwt
def create_access_token(data:dict,expires_delta:timedelta | None = None)->str:
###复制一份传入的数据，防止串改
    to_encode = data.copy()

###自定义过期时间
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
###在传入的数据中加入过期时间
    to_encode.update({"exp":expire})
###返回jwt，里面包含Header:algorithm.Payload:核心业务数据，
# 也就是to_encode的内容，里面包含用户id用户名和过期时间.SECRET_KEY之后后端知道的防伪核心
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

###解析并验证前端传来的token
def get_current_user(token:str=Depends(oauth2_scheme),db:Session = Depends(get_db)):
###创建一个401错误，后面一但有错误，不管是什么错误都用这个    
    credentials_exception= HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate":"Bearer"},

    )
####进行异常捕获，将用户输入的token放入jwt，用同一个SECRET_KEY解码Token，
# 取出里面的sub（登录时放进去的用户名），判断sub是否存在，没有sub或者签名不对/过期都报错
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username:str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
###根据sub里面的用户名与是否与User里的某一个username是否相同，若没有相同的则报错，有则返回user
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user
    







