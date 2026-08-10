from dataclasses import dataclass,field
import httpx
import json
from frontend.config import CHAT_URL, HEALTH_URL
SOURCE_SEP = "\n\n<!--SOURCES-->\n"


@dataclass
class StreamResult:
    sources:list = field(default_factory=list)
    error : str | None = None







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
                headers={"Accept": "application/x-ndjson"},
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
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        et = event.get("type")
                        if et == "token":
                            delta = event.get("delta") or ""
                            if delta:
                                yield delta
                        elif et == "sources":
                            items = event.get("items") or []
                            if items:
                                result.sources = items
                        elif et == "error":
                            result.error = event.get("message") or "未知错误"
                        elif et == "done":
                            return
        if result.error:
            yield f"\n\n（错误：{result.error}）"

    return gen(),result
  
            

                    

