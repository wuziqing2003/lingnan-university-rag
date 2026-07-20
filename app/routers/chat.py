from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest
from app.rag.chain import rag_chain



router = APIRouter(tags=["chat"])

@router.post("/chat/stream")
async def chat_stream(body:ChatRequest):
    async def event_generator():
        async for chunks in rag_chain.astream(body.question):
            if chunks:
                yield chunks
    
    return StreamingResponse(
        event_generator(),
        media_type = "text/plain;charset=utf-8",
    )

###body内容示例
# #{
#   "question": "请用通俗的语言解释一下什么是量子纠缠",
#   "session_id": "user-12345",
#   "history": [
#     {"role": "user", "content": "你好"},
#     {"role": "assistant", "content": "你好！有什么我可以帮你的？"}
#   ]
# }