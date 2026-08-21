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
from app.agent.tools import _pack
from app.agent.events import (
    ActionEvent,
    AgentEvent,
    DoneEvent,
    ErrorEvent,
    ObservationEvent,
    SourcesEvent,
    TokenEvent,
)
import os


SYSTEM_PROMPT = """你是岭南师范学院规章与信息公开问答助手。
你只能依据工具返回的资料回答，不得使用训练知识或常识补全校内规定。

【工具使用】
1. search_lingnan_knowledge_base
   - 用途：校内规章制度与培养管理原文检索。
   - 触发：学籍、资助、奖助学金、处分、申诉、转专业、转学、实习见习、培养、学位、开题中期、答辩、考试、课程、学分、宿舍、心理危机、教学管理等校内规定问题。
   - 规则：凡涉及校内规定，必须先调用本工具；未调用前不得直接回答规定内容。

2. search_web_messages
   - 用途：公开互联网检索（新闻、公开网页、外部资料摘要）。
   - 触发：仅在以下情况使用：
     a) 问题明显是校外公开信息/时效资讯，且不属于校内规章条文；或
     b) 已调用知识库且返回未检索到相关资料/完全无关后，用户问题仍可能被公开网页覆盖。
   - 禁止：用联网结果替代或伪造学校官方规章；校内条文结论不得主要来自网页。

【回答规则】
3. 只根据工具返回作答；工具没支持的点不要编造。
4. 知识库资料足够时：先给简洁v结论，再引用关键原句或要点；不要追加“联系教务处”。
5. 知识库资料部分相关时：先答能支持的部分，并简要说明未覆盖点；末尾追加一句：具体请联系教务处核实。
6. 对校内规定问题，若知识库未检索到相关资料，或资料与问题完全无关、无法给出任何有依据的要点：
   - 若也不适合/未通过联网补充，则一字不差只回答：
抱歉，学校官方文档未收录此条例
   - 此情况下不要追加“联系教务处”或其他补充句。
7. 若使用了联网结果：必须说明信息来自公开网页，并尽量附上链接；明确其不能视为学校官方规章依据。
8. 严禁编造专业、奖学金、学分、处分标准、办理流程等不存在的规定。
9. 用中文回答；除规定的拒答句外，表述清楚简洁。

"""

model = ChatOpenAI(
    model="deepseek-v4-pro",
    base_url="https://api.deepseek.com",
    api_key=DEEPSEEK_API_KEY,
    temperature=0.0,
    streaming=True,
)
llm_with_tools = model.bind_tools(TOOLS)

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


class LegacyRunner:
    async def run(
        self,
        question: str,
        thread_id: str | None = None,
    ) -> AsyncIterator[AgentEvent]:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=question),
        ]
        max_rounds = 5
        try:
            for round_i in range(max_rounds):
                assembled = None
                saw_tools = False
                async for chunk in llm_with_tools.astream(messages):
                    assembled = chunk if assembled is None else assembled + chunk
                    if getattr(chunk, "tool_call_chunks", None):
                        saw_tools = True
                    text = _chunk_text(chunk.content)
                    if text and not saw_tools:
                        yield TokenEvent(delta=text)
                if assembled is None:
                    yield ErrorEvent(message="模型无输出")
                    yield DoneEvent()
                    return
                ai_msg = AIMessage(
                    content=assembled.content,
                    tool_calls=getattr(assembled, "tool_calls", []) or [],
                )
                messages.append(ai_msg)
                if ai_msg.tool_calls:
                    for tc in ai_msg.tool_calls:
                        yield ActionEvent(
                            round=round_i,
                            name=tc["name"],
                            args=tc["args"],
                            id=tc["id"],
                        )
                        tool_fn = TOOL_MAP[tc["name"]]
                        try:
                            raw = await tool_fn.ainvoke(tc["args"])
                        except Exception as e:
                            raw = _pack(
                                f"【工具暂时不可用】{tc['name']} 调用失败：{e}。"
                                "请基于已有信息作答或说明无法完成检索，不要假装已经搜到了内容。"
                            )
                        content, sources = _parse_tool_payload(raw)
                        messages.append(
                            ToolMessage(content=content, tool_call_id=tc["id"])
                        )
                        preview = content if len(content) <= 500 else content[:500] + "..."
                        yield ObservationEvent(
                            round=round_i,
                            name=tc["name"],
                            id=tc["id"],
                            content=preview,
                        )
                        if sources:
                            yield SourcesEvent(items=sources)
                    continue
                yield DoneEvent()
                return
            yield ErrorEvent(message="执行轮次超限")
            yield DoneEvent()
        except Exception as e:
            yield ErrorEvent(message=str(e))
            yield DoneEvent()




async def run(
    question: str,
    thread_id: str | None = None,
) -> AsyncIterator[AgentEvent]:
    if os.getenv("AGENT_RUNNER", "graph") == "graph":
        from app.agent.graph import GraphRunner

        runner = GraphRunner()
    else:
        runner = LegacyRunner()
    async for event in runner.run(question, thread_id):

        yield event
