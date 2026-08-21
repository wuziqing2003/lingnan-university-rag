import asyncio
import json

from app.agent import loop as loop_mod
from app.agent.loop import LegacyRunner


class FakeChunk:
    def __init__(self, content="", tool_calls=None, tool_call_chunks=None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.tool_call_chunks = tool_call_chunks

    def __add__(self, other):
        return FakeChunk(
            content=self.content + other.content,
            tool_calls=other.tool_calls or self.tool_calls,
            tool_call_chunks=other.tool_call_chunks or self.tool_call_chunks,
        )


class FakeLLM:
    def __init__(self, rounds):
        self._rounds = list(rounds)
        self.seen_messages = []

    async def astream(self, messages):
        self.seen_messages.append(list(messages))
        chunks = self._rounds.pop(0)
        for chunk in chunks:
            yield chunk


class FakeTool:
    def __init__(self, raw: str):
        self._raw = raw

    async def ainvoke(self, args):
        return self._raw


class BoomTool:
    async def ainvoke(self, args):
        raise RuntimeError("timeout")


def _compact_types(events):
    names = [e.type for e in events]
    out = []
    for name in names:
        if out and out[-1] == "token" and name == "token":
            continue
        out.append(name)
    return out


def _collect(monkeypatch, llm, tool):
    monkeypatch.setattr(loop_mod, "llm_with_tools", llm)
    monkeypatch.setitem(
        loop_mod.TOOL_MAP,
        "search_lingnan_knowledge_base",
        tool,
    )

    async def _run():
        events = []
        async for event in LegacyRunner().run("转专业要什么条件？"):
            events.append(event)
        return events

    return asyncio.run(_run())


def test_main_path_thought_then_tool_then_answer(monkeypatch):
    llm = FakeLLM(
        [
            [
                FakeChunk(content="我先查知识库。"),
                FakeChunk(
                    content="",
                    tool_call_chunks=[{}],
                    tool_calls=[
                        {
                            "name": "search_lingnan_knowledge_base",
                            "args": {"query": "转专业"},
                            "id": "call_1",
                        }
                    ],
                ),
            ],
            [FakeChunk(content="根据资料，转专业需满足学院公布的条件。")],
        ]
    )
    tool = FakeTool(
        json.dumps({"content": "转专业需满足条件。", "sources": []}, ensure_ascii=False)
    )
    events = _collect(monkeypatch, llm, tool)
    assert _compact_types(events) == [
        "token",
        "action",
        "observation",
        "token",
        "done",
    ]
    tokens = "".join(e.delta for e in events if e.type == "token")
    assert "我先查知识库" in tokens
    assert "转专业需满足学院公布的条件" in tokens


def test_tool_failure_does_not_pretend_found_rules(monkeypatch):
    refuse = "抱歉，学校官方文档未收录此条例"
    llm = FakeLLM(
        [
            [
                FakeChunk(
                    content="",
                    tool_call_chunks=[{}],
                    tool_calls=[
                        {
                            "name": "search_lingnan_knowledge_base",
                            "args": {"query": "没有的条例"},
                            "id": "call_1",
                        }
                    ],
                ),
            ],
            [FakeChunk(content=refuse)],
        ]
    )
    events = _collect(monkeypatch, llm, BoomTool())

    observations = [e for e in events if e.type == "observation"]
    assert observations
    assert "工具暂时不可用" in observations[0].content

    # 失败说明被写回给了模型，而不是丢弃
    tool_msgs = [
        m
        for batch in llm.seen_messages
        for m in batch
        if getattr(m, "type", None) == "tool" or m.__class__.__name__ == "ToolMessage"
    ]
    assert tool_msgs
    assert "工具暂时不可用" in str(tool_msgs[-1].content)

    final = "".join(e.delta for e in events if e.type == "token")
    assert final == refuse
    assert "第" not in final
    assert "条例" in final  # 拒答原句可以有「条例」二字