from dataclasses import dataclass,field
import httpx
import json

from frontend.config import CHAT_URL, HEALTH_URL
SOURCE_SEP = "\n\n<!--SOURCES-->\n"


@dataclass
class StreamResult:
    sources:list = field(default_factory=list)
    error : str | None = None
    steps : list | None = field(default_factory=list)

def _parse_sse_frame(frame:str):
    event_name = None
    data_lines = []
    for raw in frame.split("\n"):
        line = raw.rstrip("\r")
        if line.startswith("event:"):
            event_name = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    raw_data = "\n".join(data_lines).strip()
    payload = json.loads(raw_data) if raw_data else {}
    return event_name,payload
        
        





def check_backend() -> bool:
    try:
        r = httpx.get(HEALTH_URL, timeout=2.0)
        return r.status_code == 200
    except httpx.HTTPError:
        return False


def stream_from_backend(question: str):

    result = StreamResult()
    def gen():
        buf = ""
        with httpx.Client(timeout=None) as client:
            with client.stream(
                "POST",
                CHAT_URL,
                json={"question": question},
                headers={"Accept": "text/event-stream"},
            ) as response:
                if response.status_code == 429:
                    try:
                        data = response.json()
                        msg = data.get("detail") or "演示额度已用完，请稍后再试。"
                    except Exception:
                        msg = "演示额度已用完，请稍后再试。"
                    result.error = msg
                    yield f"\n\n（错误：{msg}）"
                    return
                response.raise_for_status()
                for chunk in response.iter_text():
                    if not chunk:
                        continue
                    buf += chunk
                    while "\n\n" in buf:
                        frame, buf = buf.split("\n\n", 1)
                        frame = frame.strip()
                        if not frame:
                            continue
                        try:
                            et,data = _parse_sse_frame(frame)
                        except json.JSONDecodeError:
                            continue
                        
                        if et == "token":
                            delta = data.get("delta") or ""
                            if delta:
                                yield delta
                        elif et == "action":
                            result.steps.append(
                                {
                                    "kind": "action",
                                    "name": data.get("name") or "",
                                    "args": data.get("args") or {},
                                }
                            )
                            yield ""
                        elif et == "observation":
                            result.steps.append(
                                {
                                    "kind": "observation",
                                    "name": data.get("name") or "",
                                    "content": data.get("content") or "",
                                }
                            )
                            yield ""
                        elif et == "sources":
                            items = data.get("items") or []
                            if items:
                                result.sources = items
                        elif et == "error":
                            result.error = data.get("message") or "未知错误"
                        elif et == "done":
                            return
        if result.error:
            yield f"\n\n（错误：{result.error}）"

    return gen(),result
  
            

                    

