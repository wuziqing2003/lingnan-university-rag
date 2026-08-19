import json
from app.agent.events import AgentEvent


def encode_sse(event: AgentEvent) -> str:
    payload = json.dumps(event.payload(), ensure_ascii=False)
    return f"event:{event.type}\ndata:{payload}\n\n"