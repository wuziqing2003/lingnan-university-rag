from app.agent.events import DoneEvent, TokenEvent
from app.agent.sse import encode_sse
from frontend.api.client import decode_sse


def _frames_from_chunks(chunks:list[str]):
    buf = ""
    frames = []
    for chunk in chunks:
        buf += chunk
        while "\n\n" in buf:
            frame,buf = buf.split("\n\n",1)
            frame = frame.strip()
            if frame:
                frames.append(decode_sse(frame))
    return frames

def test_encode_then_decode_token():
    raw = encode_sse(TokenEvent(delta="学"))
    event,data = decode_sse(raw.strip())
    assert event == "token"
    assert data == {"delta":"学"}

def test_decode_empty_data_is_empty_dict():
    event,data = decode_sse("event:done\ndata:\n\n")
    assert event == "done"
    assert data == {}

def test_decode_done_encoded_payload():
    event, data = decode_sse(encode_sse(DoneEvent()).strip())
    assert event == "done"
    assert data == {}


def test_decode_multiple_data_lines():
    frame = 'event:token\ndata:{"delta":\ndata:"学"}'
    event, data = decode_sse(frame)
    assert event == "token"
    assert data == {"delta": "学"}

def test_half_frame_waits_then_decodes():
    full = encode_sse(TokenEvent(delta="学"))
    mid = max(len(full) // 2, 1)
    first, second = full[:mid], full[mid:]
    assert _frames_from_chunks([first]) == []
    frames = _frames_from_chunks([first, second])
    assert frames == [("token", {"delta": "学"})]
            