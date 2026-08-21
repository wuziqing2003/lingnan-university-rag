from __future__ import annotations
import logging
from collections.abc import AsyncIterator
from typing import Annotated, Any, Literal
from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    RemoveMessage,
)
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import StreamWriter
from typing_extensions import TypedDict
from app.agent.events import (
    ActionEvent,
    AgentEvent,
    DoneEvent,
    ErrorEvent,
    ObservationEvent,
    SourcesEvent,
    ThoughtEvent,
    TokenEvent,
)
from app.agent.loop import SYSTEM_PROMPT, _chunk_text, _parse_tool_payload
from app.agent.tools import TOOL_MAP, TOOLS, _pack
from app.core.config import DEEPSEEK_API_KEY
from uuid import UUID, uuid4

def _chunk_for_stream(text: str, size: int = 8):
    for i in range(0, len(text), size):
        yield text[i : i + size]

logger = logging.getLogger(__name__)
MAX_ROUNDS = 5
SUMMARIZE_AFTER_TURNS = 5
KEEP_LAST_MESSAGES = 4
model = ChatOpenAI(
    model="deepseek-v4-pro",
    base_url="https://api.deepseek.com",
    api_key=DEEPSEEK_API_KEY,
    temperature=0.0,
    streaming=True,
)
llm_with_tools = model.bind_tools(TOOLS)

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage],add_messages]
    thought : str
    pending_actions : list[dict[str,Any]]
    pending_observations : list [dict[str,Any]]
    sources : list
    error : str | None
    round : int
    turn : int
    summary : str

def _messages_for_model(state:AgentState) -> list[AnyMessage]:
    summary = (state.get("summary") or "").strip()
    sys = SYSTEM_PROMPT
    if summary:
        sys = SYSTEM_PROMPT + "\n\n【此前对话摘要】\n" + summary
    rest = [m for m in state["messages"] if not isinstance(m,SystemMessage)]
    return [SystemMessage(content=sys,id="system"),*rest]

async def _summarize_messages(messages:list[AnyMessage],prev_summary:str) -> str:
    parts : list[str] = []
    if prev_summary:
        parts.append(f"已有摘要：{prev_summary}")
    for m in messages:
        text = _chunk_text(getattr(m,"content",""))
        if not text:
            continue
        parts.append(f"{m.__class__.__name__}:{text[:800]}")
    prompt = (
        "请将以下对话压缩成简短中文摘要，保留用户问过的主题和已得到的关键结论。"
        "不要编造校内条文。\n\n"
        + "\n".join(parts[-40:])
    )
    resp = await model.ainvoke([HumanMessage(content=prompt)])
    return _chunk_text(resp.content) or prev_summary or ""


async def think(state:AgentState,writer : StreamWriter) -> dict:
    if state["round"] >= MAX_ROUNDS:
        return {"error":"执行轮次超限"}

    assembled = None

    async for chunk in llm_with_tools.astream(_messages_for_model(state)):
        assembled = chunk if assembled is None else assembled + chunk
   
    if assembled is None:
        return {"error":"模型无输出","pending_actions":[]}

    tool_calls = getattr(assembled,"tool_calls",None) or []
    thought = _chunk_text(assembled.content)
    if tool_calls:
        if thought:
            writer(ThoughtEvent(delta=thought,skipped=False))
        else:
            writer(ThoughtEvent(delta="",skipped=True))
    return {
        "messages": [
            AIMessage(content=assembled.content,tool_calls=tool_calls)
        ],
        "thought":thought if tool_calls else "",
        "pending_actions":tool_calls,
        "round":state["round"] + 1,
        "error":None,
    }

async def answer(state:AgentState,writer:StreamWriter) -> dict:
    text = state["messages"][-1].content
    text = _chunk_text(text)
    for piece in _chunk_for_stream(text):
        writer(TokenEvent(delta=piece))
    writer(DoneEvent())
    return {}

def route_start(state:AgentState) -> Literal["summarize", "think"]:
    if (state.get("turn") or 0) > SUMMARIZE_AFTER_TURNS:
        return "summarize"
    return "think"
    

def route_after_think(state:AgentState) -> Literal["act","answer","fail"]:
    if state["error"]:
        return "fail"
    if state["pending_actions"]:
        return "act"
    return "answer"

async def act(state:AgentState,writer : StreamWriter) -> dict:
    observations = []
    for tc in state["pending_actions"]:
        name = tc["name"]
        args = tc["args"]
        call_id = tc["id"]
        writer(ActionEvent(name=name,args=args,id=call_id,round=state["round"]-1))
        if name not in TOOL_MAP:
            raw = _pack(
                f"【工具暂时不可用】未知工具：{name}。"
                "请基于已有信息作答或说明无法完成检索，不要假装已经搜到了内容。"
            )

        else:
            try:
                raw = await TOOL_MAP[name].ainvoke(args)
            except Exception as e:
                raw = _pack(
                    f"【工具暂时不可用】{name} 调用失败：{e}。"
                    "请基于已有信息作答或说明无法完成检索，不要假装已经搜到了内容。"
                )
        observations.append({"name":name,"id":call_id,"raw":raw})
    return {"pending_observations":observations}

async def observe(state:AgentState,writer:StreamWriter) -> dict:
    messages : list[ToolMessage] = []
    all_sources: list = []
    for item in state["pending_observations"]:
        content,sources = _parse_tool_payload(item["raw"])
        messages.append(ToolMessage(content=content,tool_call_id=item["id"]))
        preview = content if len(content) <= 500 else content[:500] + "..."
        writer(
            ObservationEvent(
                round=state["round"]-1,
                name=item["name"],
                id=item["id"],
                content=preview,
            )
        )
        if sources:
            writer(SourcesEvent(items=sources))
            all_sources.extend(sources)
    return {
            "messages":messages,
            "sources":all_sources,
            "pending_observations":[],
            "pending_actions":[],
        }

async def summarize(state: AgentState, writer: StreamWriter) -> dict:
    messages = list(state.get("messages") or [])
    prev = state.get("summary") or ""
    new_summary = await _summarize_messages(messages, prev)
    removable = [m for m in messages if not isinstance(m, SystemMessage) and getattr(m, "id", None)]
    stale = removable[:-KEEP_LAST_MESSAGES] if len(removable) > KEEP_LAST_MESSAGES else []
    deletions = [RemoveMessage(id=m.id) for m in stale]
    return {"summary": new_summary, "messages": deletions}

async def fail(state: AgentState, writer: StreamWriter) -> dict:
    writer(ErrorEvent(message=state.get("error") or "未知错误"))
    writer(DoneEvent())
    return {}


def build_graph(checkpointer=None):
    builder = StateGraph(AgentState)
    builder.add_node("summarize", summarize)
    builder.add_node("think", think)
    builder.add_node("act", act)
    builder.add_node("observe", observe)
    builder.add_node("answer", answer)
    builder.add_node("fail", fail)

  
    builder.add_conditional_edges(
        START,
        route_start,
        {"summarize": "summarize", "think": "think"},
    )
    builder.add_edge("summarize", "think")
    builder.add_conditional_edges(
        "think",
        route_after_think,
        {"act": "act", "answer": "answer", "fail": "fail"},
    )
    builder.add_edge("act", "observe")
    builder.add_edge("observe", "think")
    builder.add_edge("answer", END)
    builder.add_edge("fail", END)
    return builder.compile(checkpointer=checkpointer)


graph = build_graph()

def _empty_values(values: dict | None) -> bool:
    if not values:
        return True
    return not values.get("messages")
class GraphRunner:
    def __init__(self, compiled=None):
        self._compiled = compiled
    def _graph(self):
        return self._compiled if self._compiled is not None else graph
    async def run(
        self,
        question: str,
        thread_id: str | UUID | None = None,
    ) -> AsyncIterator[AgentEvent]:
        compiled = self._graph()
        checkpointer = getattr(compiled, "checkpointer", None)
        if not checkpointer:
            initial: AgentState = {
                "messages": [
                    SystemMessage(content=SYSTEM_PROMPT, id="system"),
                    HumanMessage(content=question, id=str(uuid4())),
                ],
                "thought": "",
                "pending_actions": [],
                "pending_observations": [],
                "sources": [],
                "error": None,
                "round": 0,
                "turn": 1,
                "summary": "",
            }
            async for event in compiled.astream(initial, stream_mode="custom"):
                yield event
            return
        if thread_id is None:
            yield ErrorEvent(message="缺少 thread_id")
            yield DoneEvent()
            return
        config = {"configurable": {"thread_id": str(thread_id)}}
        snapshot = await compiled.aget_state(config)
        values = snapshot.values or {}
        if _empty_values(values):
            payload: dict[str, Any] = {
                "messages": [
                    SystemMessage(content=SYSTEM_PROMPT, id="system"),
                    HumanMessage(content=question, id=str(uuid4())),
                ],
                "thought": "",
                "pending_actions": [],
                "pending_observations": [],
                "sources": [],
                "error": None,
                "round": 0,
                "turn": 1,
                "summary": "",
            }
        else:
            payload = {
                "messages": [HumanMessage(content=question, id=str(uuid4()))],
                "thought": "",
                "pending_actions": [],
                "pending_observations": [],
                "sources": [],
                "error": None,
                "round": 0,  # 这一问的 ReAct 步数从 0 再数
                "turn": int(values.get("turn") or 0) + 1,
            }
        async for event in compiled.astream(
            payload,
            config=config,
            stream_mode="custom",
        ):
            yield event
                





