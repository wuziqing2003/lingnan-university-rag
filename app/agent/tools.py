from __future__ import annotations

import json

from langchain_core.tools import tool

from app.rag.chain import format_context, retrieve_hits


def _hits_to_sources(hits: list[dict]) -> list[dict]:
    return [
        {
            "source": h.get("source", "未知"),
            "page": h.get("page"),
            "snippet": (h.get("text") or "")[:200],
        }
        for h in (hits or [])
    ]


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
def search_lingnan_knowledge_base(query: str) -> str:
    """在岭南师范学院规章制度知识库中检索与问题相关的原文片段（含来源与页码）。
    适用：奖学金、助学金、学籍、处分、转专业、实习、培养、学位、考试等校内规定。
    流程与线上 RAG 一致：Query 改写 → Hybrid（向量+BM25+RRF）→ Rerank → Top3。
    若返回「未检索到相关资料」，不要编造条文；时效性/库外问题再考虑联网搜索。
    Args:
        query: 检索用的自然语言问题或关键词。
    """
    return _run_search(query)


TOOLS = [search_lingnan_knowledge_base]
TOOL_MAP = {t.name: t for t in TOOLS}