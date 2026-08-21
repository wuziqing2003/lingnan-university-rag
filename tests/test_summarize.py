import asyncio
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver

from app.agent import graph as graph_mod
from app.agent.graph import GraphRunner


class FakeChunk:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.tool_call_chunks = None

    def __add__(self, other):
        return FakeChunk(
            content=self.content + other.content,
            tool_calls=other.tool_calls or self.tool_calls,
        )


class RepeatLLM:
    def __init__(self, text="根据资料，可以。"):
        self.text = text
        self.seen_messages = []

    async def astream(self, messages):
        self.seen_messages.append(list(messages))
        yield FakeChunk(content=self.text)


def _unwrap(chunk):
    if hasattr(chunk, "type") and hasattr(chunk, "payload"):
        return chunk
    if isinstance(chunk, dict) and "data" in chunk:
        return _unwrap(chunk["data"])
    return chunk


def _collect(runner, question, thread_id):
    async def _run():
        events = []
        async for chunk in runner.run(question, thread_id):
            event = _unwrap(chunk)
            if hasattr(event, "type"):
                events.append(event)
        return events

    return asyncio.run(_run())


def test_summarize_called_after_five_turns(monkeypatch):
    calls = []

    async def fake_summarize(state, writer):
        calls.append(state.get("turn"))
        return {"summary": "已摘要"}

    monkeypatch.setattr(graph_mod, "summarize", fake_summarize)
    monkeypatch.setattr(graph_mod, "llm_with_tools", RepeatLLM())

    compiled = graph_mod.build_graph(checkpointer=InMemorySaver())
    runner = GraphRunner(compiled=compiled)
    tid = str(uuid4())

    for i in range(5):
        _collect(runner, f"问题{i}", tid)
    assert calls == []

    _collect(runner, "问题5", tid)  # 第 6 问，turn=6 > 5
    assert calls == [6]


def test_same_thread_sees_previous_question(monkeypatch):
    llm = RepeatLLM()
    monkeypatch.setattr(graph_mod, "llm_with_tools", llm)

    compiled = graph_mod.build_graph(checkpointer=InMemorySaver())
    runner = GraphRunner(compiled=compiled)
    tid = str(uuid4())

    _collect(runner, "转专业要什么条件？", tid)
    _collect(runner, "那学分不够呢？", tid)

    last_batch = llm.seen_messages[-1]
    texts = [getattr(m, "content", "") for m in last_batch]
    assert any("转专业" in str(t) for t in texts)
    assert any("学分不够" in str(t) for t in texts)