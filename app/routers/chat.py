from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest
from app.rag.chain import retrieve_hits, build_chain_from_hits
import json

router = APIRouter(tags=["chat"])
SOURCE_SEP = "\n\n<!--SOURCES-->\n" 
@router.post("/chat/stream")
async def chat_stream(body:ChatRequest):
    async def event_generator():
        hits = retrieve_hits(body.question)
        chain = build_chain_from_hits(hits)
        async for chunk in chain.astream(body.question):
            if chunk:
                yield chunk
        
        sources = [
            {
                "source": h.get("source"),
                "page": h.get("page"),
                "snippet": (h.get("text") or "")[:200],  # 原文片段，方便核对 / 判 A/B
            }
            for h in hits
        ]

        yield SOURCE_SEP + json.dumps(sources, ensure_ascii=False)


    return StreamingResponse(
        event_generator(),
        media_type="text/plain;charset=utf-8",
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