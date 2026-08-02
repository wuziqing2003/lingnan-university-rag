from __future__ import annotations
import re
import chromadb
import requests
from langchain_core.tools import tool
from openai import OpenAI
from app.core.config import SiliconFlow_API_KEY


embed_client = OpenAI(
    api_key = SiliconFlow_API_KEY,
    base_url = "https://api.siliconflow.cn/v1",
)

chroma = chromadb.PersistentClient(path="./chroma_db")
collection = chroma.get_or_create_collection(name="lingnan_rag")


def get_embedding(text: str):
    resp = embed_client.embeddings.create(
        model="BAAI/bge-large-zh-v1.5",
        input=text,
    )
    return resp.data[0].embedding




def retrieve(question: str, n_results: int = 3) -> str:
    result = collection.query(
        query_embeddings=[get_embedding(question)],
        n_results=n_results,
    )
    docs = result["documents"][0]
    return "\n\n".join(docs).strip() if docs else "未检索到相关资料"


@tool
def search_lingnan_knowledge_base(query: str) -> str:
    """在岭南师范学院规章制度知识库中检索与问题相关的原文片段。
    当用户询问奖学金、助学金、学籍、处分、实习、培养方案等校内规定时使用。
    返回检索到的条文文本，供你据此作答；资料不足时如实说明。
    Args:
        query: 检索用的自然语言问题或关键词。
    """
    return retrieve(query)


NOTICE_URL = "https://www.lingnan.edu.cn/"

@tool
def fetch_web_news(keyword:str = ""):
    """从学校官网通知公告页抓取近期标题列表（伪联网，非搜索引擎）。
    适用：最新放假、近期通知、学校公告、开学安排等时效性问题。
    不适用：需要条文细节的规章制度问答（应改用知识库工具）。

    Args:
        keyword: 可选过滤词，如「八一」「慰问信」；为空则返回最近若干条标题。
    """

    try:
        resp = requests.get(
            NOTICE_URL,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (compatible; LingnanRAG/1.0)"}
        )
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        html = resp.text

    except Exception as e:
        return f"抓取失败: {e}"


    titles = re.findall(
        r"<a[^>]*>([^<]{6,80})</a>",
        html,
        flags=re.IGNORECASE,
    )

    cleaned = []

    for t in titles:
        t = t.strip()
        if not t or t in cleaned:
            continue
        if any( x in t for x in ("首页", "English", "登录", "更多")):
            continue
        cleaned.append(t)

    if keyword:
        cleaned = [t for t in cleaned if keyword in t]

    if not cleaned:
        return "未从官网解析到相关通知标题（可能页面结构变化或关键词过窄）。"

    return "学校官网近期通知（标题摘录）：\n" + "\n".join(
        f"- {t}" for t in cleaned[:15]
    )


TOOLS = [search_lingnan_knowledge_base, fetch_web_news]
TOOL_MAP = {t.name: t for t in TOOLS}
