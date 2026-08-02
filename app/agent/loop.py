from __future__ import annotations
import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from app.agent.tools import TOOL_MAP, TOOLS
from app.core.config import DEEPSEEK_API_KEY


SYSTEM_PROMPT = (
    "你是岭南师范学院规章助手。"
    "涉及校内规定时必须先调用 search_lingnan_knowledge_base；"
    "最新放假、近期通知、官网公告等时效问题必须调用 fetch_web_news；"
    "只能根据工具返回的资料用中文回答；资料没有就说不知道。"
)

model = ChatOpenAI(
    model = "deepseek-v4-pro",
    base_url = "https://api.deepseek.com",
    api_key = DEEPSEEK_API_KEY,
    temperature = 0.0,
)

llm_with_tools = model.bind_tools(TOOLS)

def _ndjson(event:dict):
    return json.dumps(event,ensure_ascii=False) + "\n"



async def stream_agent(user_text: str, max_rounds: int = 5) -> AsyncIterator[str]:
    """多层流：status / tool_call / tool_result / token / done / error。"""
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_text),
    ]

    yield _ndjson({"type": "status", "message": "agent_started"})

    try:
        for round_i in range(max_rounds):
            ai_msg = await llm_with_tools.ainvoke(messages)
            messages.append(ai_msg)


            if ai_msg.tool_calls:
                for tc in ai_msg.tool_calls:
                    yield _ndjson(
                        {
                            "type": "tool_call",
                            "round": round_i,
                            "name": tc["name"],
                            "args": tc["args"],
                            "id": tc["id"]

                        }
                    )

                    tool_fn = TOOL_MAP[tc["name"]]
                    result =  await tool_fn.ainvoke(tc["args"])
                    messages.append(ToolMessage(content=result, tool_call_id=tc["id"]))
                    preview = result if len(result) <= 500 else result[:500] + "..."
                    yield _ndjson(
                        {
                            "type": "tool_result",
                            "name": tc["name"],
                            "id": tc["id"],
                            "content": preview,
                        }
                    )
                continue

            content = ai_msg.content or ""
            if content:
                step = 8
                for i in range(0,len(content),step):
                    yield _ndjson({"type": "token", "delta": content[i : i + step]})
                    await asyncio.sleep(0)
            yield _ndjson({"type": "done"})
            return 
        yield _ndjson({"type": "error", "message": "执行超时"})
        yield _ndjson({"type": "done"})
    except Exception as e:
        yield _ndjson({"type": "error", "message": str(e)})
        yield _ndjson({"type": "done"})