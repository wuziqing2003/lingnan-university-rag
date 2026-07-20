from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from openai import OpenAI
from app.core.config import SiliconFlow_API_KEY,DEEPSEEK_API_KEY
import chromadb
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda,RunnablePassthrough






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
    result = collection.query(
        query_embeddings=[get_embedding(question)],
        n_results=3
    )
    docs = result["documents"][0] or []

    return "\n\n".join(docs)

prompt = ChatPromptTemplate([
    ("system","你只能根据给定资料回答，资料没有的内容就说不知道。"),
    ("human","根据已知信息{context},请回答问题{question}"),
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
