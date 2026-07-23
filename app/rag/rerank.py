import httpx
from app.core.config import SiliconFlow_API_KEY

RERANK_URL = "https://api.siliconflow.cn/v1/rerank"

RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
##第一步是拿到混合检索后的字符串列表，判断列表是否为空，去除每个字符串的空白，如果清洗后的列表还是空的
##直接返回一个空列表，判断清洗后端字符串列表里是不是只有一个字符串，如果是就不用重排，构建请求体和请求头
##创建一个httpx客户端用来发送请求，包含请求方式，请求地址，请求体，请求头，判断请求是否成功
##拿到API返还的json格式数据，取出数据中的result，里面存放的是字典列表，遍历每一个字典
###从字典中拿出index的值，判断会不会超出docs的长度，如果不会就根据index的值，往新列表中存放字符串
###


def rerank_documents(query:str,documents:list[str],top_n:int =3):
    docs = [d.strip() for d in (documents or []) if (d or "").strip()]
    if not docs:
        return []

    if len(docs) == 1:
        return docs[:top_n]

    payload = {
        "model":RERANK_MODEL,
        "query":query,
        "documents":docs,
        "top_n":min(top_n,len(docs)),
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
        if 0 <= idx < len(docs):
            ranked.append(docs[idx])

    return ranked[:top_n]
