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

# 3. 成功后触发工业级标准日志
logging.info("Config loaded successfully.")