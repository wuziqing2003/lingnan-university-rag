from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.rag.chain import rag_chain
from app.schemas.chat import ChatRequest


router = APIRouter(tags=["chat"])

@router.post("/chat/stream")
async def chat_stream(body: ChatRequest):
    async def event_generator():
        async for chunk in rag_chain.astream(body.question):
            if chunk:
                yield chunk


    return StreamingResponse(
        event_generator(),
        media_type="text/plain;charset=utf-8",
    )
