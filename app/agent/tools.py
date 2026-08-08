from __future__ import annotations
from app.rag.web_search import search_web
import json

from langchain_core.tools import tool

from app.rag.chain import format_context, retrieve_hits


def _hits_to_sources(hits: list[dict]) -> list[dict]:
    return [
        {
            "source": h.get("source", "未知"),
            "page": h.get("page"),
            "snippet": (h.get("text") or "")[:100],
        }
        for h in (hits or [])
    ]

def web_to_sources(results:list[dict])->list[dict]:
    return [
        {
            "source":r.get("title") or "未知来源",
            "url":r.get("url") or "",
            "page": None,
        }
        for r in (results or [])
    ]

def _format_web_sources(results:list[dict])->list[dict]:
    parts = []
    for i,r in enumerate(results,start=1):
        title = r.get("title") or "未知来源"
        url = r.get("url") or ""
        content = r.get("content") or ""
        parts.append(f"[{i}] {title}\n{url}\n{content}")
    return "\n\n".join(parts)


def _run_web_search(query:str)->str:
    q = (query or "").strip()
    if not q:
        return _pack("请提供具体问题或关键词。")
    try:

        results = search_web(q)
    except Exception:
        return _pack(
            "【工具暂时不可用】网络搜索失败或超时。"
            "请勿编造检索结果；若问题不依赖网页，可说明限制并谨慎作答；"
            "若是校内规章，仍不得用常识冒充条文。"
        )
    if not results:
        return _pack("未检索到相关资料。"
        "说明：网络搜索没有找到与问题足够相关的信息；"
        "不要编造信息。"
        )
    return _pack(_format_web_sources(results),web_to_sources(results))


def _pack(content: str, sources: list[dict] | None = None) -> str:
    return json.dumps(
        {"content": content, "sources": sources or []},
        ensure_ascii=False,
    )


def _run_search(query: str) -> str:
    q = (query or "").strip()
    if not q:
        return _pack("请提供具体问题或关键词。")
    hits = retrieve_hits(q)
    if not hits:
        return _pack(
            "未检索到相关资料。"
            "说明：知识库中没有与问题足够相关的规章片段；"
            "不要编造条文。"
        )
    return _pack(format_context(hits), _hits_to_sources(hits))


@tool
def search_web_messages(query:str)-> str:
    """在公开互联网上搜索与问题相关的网页摘要（含标题与链接）。
    适用：时效新闻、公开信息、知识库未覆盖的校外资料。
    不适用：校内规章原文（学籍、资助、处分、转专业等）——那些必须用 search_lingnan_knowledge_base。
    Args:
        query: 检索用的自然语言问题或关键词。
    """
    return _run_web_search(query)




@tool
def search_lingnan_knowledge_base(query: str) -> str:
    """在岭南师范学院规章制度知识库中检索与问题相关的原文片段（含来源与页码）。
    适用：奖学金、助学金、学籍、处分、转专业、实习、培养、学位、考试等校内规定。
    流程与线上 RAG 一致：Query 改写 → Hybrid（向量+BM25+RRF）→ Rerank → Top3。
    若返回「未检索到相关资料」，不要编造条文；时效性/库外问题再考虑联网搜索。
    Args:
        query: 检索用的自然语言问题或关键词。
    """
    return _run_search(query)


TOOLS = [search_lingnan_knowledge_base,search_web_messages]
TOOL_MAP = {t.name: t for t in TOOLS}