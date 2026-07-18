from pathlib import Path

API_BASE = "http://127.0.0.1:8000"
CHAT_URL = f"{API_BASE}/chat/stream"
HEALTH_URL = f"{API_BASE}/health"
BADGE_PATH = Path("image/School_badge.jpg")

EXAMPLE_QUESTIONS = [
    "国家奖学金和国家助学金能不能兼得？",
    "本科生毕业需要修满多少学分？",
    "如何申请勤工助学岗位？",
]
