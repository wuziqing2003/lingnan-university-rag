from dataclasses import dataclass,field
import httpx
import json
from frontend.config import CHAT_URL, HEALTH_URL
SOURCE_SEP = "\n\n<!--SOURCES-->\n"


@dataclass
class StreamResult:
    sources:list = field(default_factory=list)







def check_backend() -> bool:
    try:
        r = httpx.get(HEALTH_URL, timeout=2.0)
        return r.status_code == 200
    except httpx.HTTPError:
        return False


def stream_from_backend(question: str):

    result = StreamResult()
    def gen():
        pending=""
        reading_sources = False
        raw = ""
        
        with httpx.Client(timeout = None) as client:
            with client.stream("POST",CHAT_URL,json={"question":question}) as response:
                response.raise_for_status()
                for chunk in response.iter_text():
                    if not chunk:
                        continue

                    if reading_sources:
                        raw += chunk
                        continue

                    pending += chunk

                    if SOURCE_SEP in pending:
                        answer_part,raw = pending.split(SOURCE_SEP,1)
                        if answer_part:
                            yield answer_part

                        reading_sources = True

                    else:
                        keep = len(SOURCE_SEP) - 1
                        if len(pending) > keep:
                            yield pending[:-keep]
                            pending = pending[-keep:]


        result.sources = json.loads(raw) if raw.strip() else []

    return gen(),result

   

            

                    

