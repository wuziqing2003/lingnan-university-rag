from __future__ import annotations
import json
from collections.abc import AsyncIterator
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_openai import ChatOpenAI
from app.agent.tools import TOOL_MAP, TOOLS
from app.core.config import DEEPSEEK_API_KEY

SYSTEM_PROMPT = """你是岭南师范学院官方规章问答助手。
规则（必须遵守）：
1. 涉及校内规定（学籍、资助、处分、实习、考试、学位、转专业等）时，必须先调用 search_lingnan_knowledge_base，再根据工具返回作答。
2. 只能依据工具返回的检索资料回答，不得使用资料外的知识或常识补全。
3. 资料部分相关时：先回答资料能支持的部分，并简要说明资料未覆盖的点；不要因为信息不完整就整句拒答。末尾追加一句：具体请联系教务处核实。
4. 仅当工具返回未检索到相关资料，或资料与问题完全无关、无法给出任何有依据的要点时，才一字不差地只回答：
抱歉，学校官方文档未收录此条例
（此情况下不要追加「联系教务处」或其他补充句。）
5. 严禁编造专业、奖学金、学分、处分、流程等不存在的规定。
6. 资料足够时：先给简洁结论，再引用资料中的关键原句或要点；不要追加「联系教务处」。
7. 用中文回答。
"""
model = ChatOpenAI(
    model="deepseek-v4-pro",
    base_url="https://api.deepseek.com",
    api_key=DEEPSEEK_API_KEY,
    temperature=0.0,
    streaming=True,
)
llm_with_tools = model.bind_tools(TOOLS)
def _ndjson(event: dict) -> str:
    return json.dumps(event, ensure_ascii=False) + "\n"

def _parse_tool_payload(raw:str):
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "content" in data:
            return str(data["content"]),list(data.get("sources") or [])

    except json.JSONDecodeError:
        pass

    return raw,[]

def _chunk_text(content):
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content,list):
        parts = []
        for p in content:
            if isinstance(p, dict):
                parts.append(p.get("text", ""))
            else:
                parts.append(str(p))
        return "".join(parts)
    return str(content)


async def stream_agent(user_text: str, max_rounds: int = 5)-> AsyncIterator[str]:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_text),
    ]
    yield _ndjson({"type": "status", "message": "agent_started"})

    try:
        for round_i in range(max_rounds):
            assembled = None
            saw_tool_calls = False
            async for chunk in llm_with_tools.astream(messages):
                assembled = chunk if assembled is None else assembled + chunk
                if getattr(chunk,"tool_call_chunks",None):
                    saw_tool_calls = True
                text = _chunk_text(chunk.content)
                if text and not saw_tool_calls:
                    yield _ndjson({"type": "token", "delta": text})

            if assembled is None:
                yield _ndjson({"type": "error", "message": "模型无输出"})
                yield _ndjson({"type": "done"})
                return
            ai_msg = AIMessage(
                content=assembled.content,
                tool_calls=getattr(assembled, "tool_calls", []) or [],
            )
            messages.append(ai_msg)

            if ai_msg.tool_calls:
                for tc in ai_msg.tool_calls:
                    yield _ndjson(
                        {
                            "type": "tool_call",
                            "round": round_i,
                            "name": tc["name"],
                            "args": tc["args"],
                            "id": tc["id"],
                        }
                    )
                    tool_fn = TOOL_MAP[tc["name"]]
                    raw = await tool_fn.ainvoke(tc["args"])
                    content, sources = _parse_tool_payload(raw)
                    messages.append(
                        ToolMessage(content=content, tool_call_id=tc["id"])
                    )
                    preview = content if len(content) <= 500 else content[:500] + "..."
                    yield _ndjson(
                        {
                            "type": "tool_result",
                            "name": tc["name"],
                            "id": tc["id"],
                            "content": preview,
                        }
                    )
                    if sources:
                        yield _ndjson({"type": "sources", "items": sources})
                continue

            yield _ndjson({"type": "done"})
            return
        yield _ndjson({"type": "error", "message": "执行轮次超限"})
        yield _ndjson({"type": "done"})
    except Exception as e:
        yield _ndjson({"type": "error", "message": str(e)})
        yield _ndjson({"type": "done"})

