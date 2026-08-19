from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.agent.loop import run
from app.schemas.agent import AgentRequest
from fastapi import Request
from app.core.rate_limit import check_demo_rate_limit, get_client_ip
from app.agent.sse import encode_sse
router = APIRouter(tags=["agent"])

@router.post("/agent/stream")
async def agent_stream(body: AgentRequest,request:Request):
    ip = get_client_ip(request)
    check_demo_rate_limit(ip)
    async def sse_stream():
        async for event in run(body.question, thread_id=None):
            yield encode_sse(event)

    return StreamingResponse(
        sse_stream(),
        media_type="text/event-stream; charset=utf-8",
        headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    },
    )