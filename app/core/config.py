import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s: %(message)s",
    datefmt="%Y-%m-%d",
)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    logging.error("Config load failed! DEEPSEEK_API_KEY is missing.")
    raise ValueError("DEEPSEEK_API_KEY 缺失")

logging.info("Config loaded successfully.")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)
logging.info("config database successfully")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

if not SECRET_KEY:
    logging.error("Config load failed! SECRET_KEY is missing.")
    raise ValueError("SECRET_KEY 缺失")


REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None
DEMO_IP_HOURLY_LIMIT = int(os.getenv("DEMO_IP_HOURLY_LIMIT", "5"))
DEMO_IP_DAILY_LIMIT = int(os.getenv("DEMO_IP_DAILY_LIMIT", "7"))
DEMO_GLOBAL_DAILY_LIMIT = int(os.getenv("DEMO_GLOBAL_DAILY_LIMIT", "50"))


SiliconFlow_API_KEY = os.getenv("SiliconFlow_API_KEY")
if not SiliconFlow_API_KEY:
    logging.error("Config load failed! SiliconFlow_API_KEY is missing")
    raise ValueError("SiliconFlow_API_KEY 缺失")

TAVILY_URL = "https://api.tavily.com/search"
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    logging.error("Config load failed! TAVILY_API_KEY is missing")
    raise ValueError("TAVILY_API_KEY 缺失")

