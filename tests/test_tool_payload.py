from app.agent.loop import _parse_tool_payload


def test_valid_json_with_content_and_sources():
    raw = '{"content":"转专业需满足条件","sources":[{"source":"手册","page":3}]}'
    content, sources = _parse_tool_payload(raw)
    assert content == "转专业需满足条件"
    assert sources == [{"source": "手册", "page": 3}]


def test_plain_text_is_content_with_no_sources():
    content, sources = _parse_tool_payload("未检索到相关资料。")
    assert content == "未检索到相关资料。"
    assert sources == []


def test_broken_json_is_treated_as_plain_text():
    raw = '{"content": 不完整'
    content, sources = _parse_tool_payload(raw)
    assert content == raw
    assert sources == []