from pathlib import Path
import os

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
CHAT_URL = f"{API_BASE}/agent/stream"
HEALTH_URL = f"{API_BASE}/health"

DEMO_SESSION_LIMIT = int(os.getenv("DEMO_SESSION_LIMIT", "5"))

BADGE_PATH = Path("image/School_badge.jpg")
LOGO_PATH = Path("image/app_logo.png")

EXAMPLE_QUESTIONS = [
    "新生可以申请保留入学资格吗？期限多久？",
    "缓考怎么申请？",
    "普通全日制本科生转专业需要什么条件？",
    "帮我在公开网页上查一下：最近有哪些关于高校人工智能人才培养的新闻？",
]
