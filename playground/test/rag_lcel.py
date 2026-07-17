import chromadb
from openai import OpenAI
from app.core.config import SiliconFlow_API_KEY,DEEPSEEK_API_KEY
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough,RunnableLambda
embed_client = OpenAI(
    api_key = SiliconFlow_API_KEY,
    base_url = "https://api.siliconflow.cn/v1",
)


def get_embedding(text):
    resp = embed_client.embeddings.create(
        model = "BAAI/bge-large-zh-v1.5",
        input = text
    )
    return resp.data[0].embedding

with open("data/lingnan_docs.txt","r",encoding="utf-8") as f:
    text = f.read().strip()

if not text:
    raise ValueError("data/lingnan_docs.txt 为空")

chunk_size = 200
chunks = [text[i:i+chunk_size] for i in range(0,len(text),chunk_size)]
chunks = [c.strip() for c in chunks if c.strip()]
ids = [f"chunk_{id}" for id in range(len(chunks))]

chroma = chromadb.PersistentClient(path="./chroma_db")
collection = chroma.get_or_create_collection("lingnan_rag")

embeddings = [get_embedding(i) for i in chunks]

collection.add(
    ids = ids,
    documents=chunks,
    embeddings=embeddings,
)


def retrieve(question):
    result = collection.query(
        query_embeddings= [get_embedding(question)],
        n_results=3
    )
    return "\n\n".join(result["documents"][0])

prompt = ChatPromptTemplate.from_messages([
    ("system","你只能根据给定资料回答,资料没有的内容就说不知道."),
    ("human","根据已知信息:{context},请回答问题:{question}")
]
)


model = ChatOpenAI(
    model = "deepseek-v4-pro",
    base_url = "https://api.deepseek.com",
    api_key = DEEPSEEK_API_KEY,
    temperature=0,
)
# #StrOutputParser 就干一件事：AIMessage → .content → 纯字符串。
# 所以 parser 不调 API、不拼 prompt，它就是个格式转换器。
parser = StrOutputParser()
# ###LCEL 里，ChatOpenAI 的 model.invoke(prompt) 返回的不是字符串，是 AIMessage​ 对象：
# AIMessage(
#     content="不能兼得，根据《岭师奖助管理办法》...",
#     response_metadata={...}
# )
rag_chain = (
    {
        "context":RunnableLambda(retrieve),
        "question":RunnablePassthrough()
    }
    | prompt
    | model
    | parser
)

question = "国家奖学金和国家助学金能不能兼得？"
answer = rag_chain.invoke(question)

print(answer)