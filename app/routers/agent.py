from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.agent.loop import stream_agent
from app.schemas.agent import AgentRequest

router = APIRouter(tags=["agent"])

@router.post("/agent/stream")
async def agent_stream(body: AgentRequest):
    return StreamingResponse(
        stream_agent(body.question),
        media_type="application/x-ndjson; charset=utf-8",
    )