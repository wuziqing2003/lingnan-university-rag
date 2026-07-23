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
2. 若资料为空、与问题无关、或不足以支持结论，必须一字不差地只回答：
抱歉，学校官方文档未收录此条例
3. 严禁编造专业、奖学金、学分、处分、流程等不存在的规定。
4. 资料足够时：先给简洁结论，再引用资料中的关键原句或要点。
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

def retrieve(question):
    from app.rag.hybrid import hybrid_search
    from app.rag.rerank import rerank_documents
    candidates = hybrid_search(question,n_results=10)
    docs = rerank_documents(question,candidates,top_n=3)
    return "\n\n".join(docs)
   

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


rag_chain = (
   {
    "context":RunnableLambda(retrieve),
    "question":RunnablePassthrough()
   }
    |prompt
    |model
    |parser
)
