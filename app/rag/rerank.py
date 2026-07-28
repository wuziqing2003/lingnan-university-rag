import httpx
from app.core.config import SiliconFlow_API_KEY

RERANK_URL = "https://api.siliconflow.cn/v1/rerank"

RERANK_MODEL = "BAAI/bge-reranker-v2-m3"



def rerank_documents(query:str,hits:list[dict],top_n:int =3):
    docs = [(h.get("text") or "").strip() for h in (hits or [])]
    valid = [(h,t) for h,t in zip(hits,docs) if t]
    if not valid:
        return []
    hits_clean, texts = zip(*valid)
    hits_clean, texts = list(hits_clean), list(texts)

    if len(texts) == 1:
        return hits_clean[:top_n]

    payload = {
        "model":RERANK_MODEL,
        "query":query,
        "documents":texts,
        "top_n":min(top_n,len(texts)),
        "return_documents":False
    }

    headers = {
        "Authorization" : f"Bearer {SiliconFlow_API_KEY}",
        "Content-Type" : "application/json",
    }

    with httpx.Client(timeout = 60.0) as client:
        resp = client.post(RERANK_URL,json=payload,headers=headers)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results") or []
    ranked = []
    for item in results:
        idx = item["index"]
        if 0 <= idx < len(hits_clean):
            ranked.append(hits_clean[idx])

    return ranked[:top_n]
