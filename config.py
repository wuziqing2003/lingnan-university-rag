import os
from dotenv import load_dotenv
import logging
# 自动加载当前目录下的 .env 文件
load_dotenv()
# 1. 配置标准日志层（带时间戳）
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s: %(message)s',
    datefmt='%Y-%m-%d'
)
# 统一对外的变量名
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    logging.error("Config load failed! DEEPSEEK_API_KEY is missing.") # 如果失败，打印红字 ERROR 级别
    raise ValueError("API Key 缺失")

# 3. 成功后触发工业级标准日志记录
logging.info("Config loaded successfully.") 


DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

SQLALCHEMY_DATABASE_URL = (f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4")
logging.info(f"config database successfully: {SQLALCHEMY_DATABASE_URL}")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

if not SECRET_KEY:
    logging.error("Config load failed! SECRET_KEY is missing.")
    raise ValueError("SECRET_KEY 缺失")


