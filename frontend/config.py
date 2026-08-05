from pathlib import Path

API_BASE = "http://127.0.0.1:8000"
CHAT_URL = f"{API_BASE}/agent/stream"
HEALTH_URL = f"{API_BASE}/health"
BADGE_PATH = Path("image/School_badge.jpg")

EXAMPLE_QUESTIONS = [
    "新生可以申请保留入学资格吗？期限多久？",
    "缓考怎么申请？",
    "普通全日制本科生转专业需要什么条件？",
]
