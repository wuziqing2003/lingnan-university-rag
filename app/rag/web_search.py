from app.core.config import TAVILY_API_KEY,TAVILY_URL
import httpx



def search_web(query:str)-> list[dict]:
    q = (query or "").strip()
    if not q:
        return []
    payload = {
        "query":q,
        "max_results":3,
    }
    headers = {
        "Authorization" : f"Bearer {TAVILY_API_KEY}",
        "Content-Type" : "application/json",
    }

    with httpx.Client(timeout = 60.0) as client:
        response=client.post(TAVILY_URL,json=payload,headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("results",[])