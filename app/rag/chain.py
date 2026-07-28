from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from openai import OpenAI
from app.core.config import SiliconFlow_API_KEY,DEEPSEEK_API_KEY
import chromadb
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda,RunnablePassthrough

REFUSAL = "抱歉，学校官方文档未收录此条例"

SYSTEM_PROMPT = """你是岭南师范学院官方规章问答助手。

规则（必须遵守）：
1. 只能依据用户消息里提供的【检索资料】回答，不得使用资料外的知识或常识补全。
2. 资料部分相关时：先回答资料能支持的部分，并简要说明资料未覆盖的点；不要因为信息不完整就整句拒答。末尾追加一句：具体请联系教务处核实。
3. 仅当资料为空，或与问题完全无关、无法给出任何有依据的要点时，才一字不差地只回答：
抱歉，学校官方文档未收录此条例
（此情况下不要追加「联系教务处」或其他补充句。）
4. 严禁编造专业、奖学金、学分、处分、流程等不存在的规定。
5. 资料足够、能完整作答时：先给简洁结论，再引用资料中的关键原句或要点；不要追加「联系教务处」。
"""







embed_client = OpenAI(
    api_key = SiliconFlow_API_KEY,
    base_url = "https://api.siliconflow.cn/v1",
)


def get_embedding(text:str):
    resp = embed_client.embeddings.create(
        model =  "BAAI/bge-large-zh-v1.5",
        input = text,
    )
    return resp.data[0].embedding

chroma = chromadb.PersistentClient(path="./chroma_db")
collection = chroma.get_or_create_collection("lingnan_rag_pdfs")

def retrieve_hits(question):
    from app.rag.hybrid import hybrid_search
    from app.rag.rerank import rerank_documents
    candidates = hybrid_search(question,n_results=10)
    return rerank_documents(question,candidates,top_n=3)

def format_context(hits:list[dict]):
    blocks = []
    for i,h  in enumerate(hits,1):
        page = h.get("page")
        page_s = f" p.{page}" if page is not None else ""
        blocks.append(f"[资料{i}] 来源：{h.get('source', '未知')}{page_s}\n{h.get('text', '')}")

    return "\n\n".join(blocks)

def retrieve(question):
    return format_context(retrieve_hits(question))
   

prompt = ChatPromptTemplate([
    ("system",SYSTEM_PROMPT),
    ("human", "【检索资料】\n{context}\n\n【问题】\n{question}"),
])

model = ChatOpenAI(
    model = "deepseek-v4-pro",
    base_url = "https://api.deepseek.com",
    api_key = DEEPSEEK_API_KEY,
    temperature=0,
    streaming=True,
)

parser = StrOutputParser()

def build_chain_from_hits(hits):
    return  (
        {
            "context":RunnableLambda(lambda _: format_context(hits)),
            "question":RunnablePassthrough()
        }
            |prompt
            |model
            |parser
        )
