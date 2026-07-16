from openai import OpenAI
import chromadb
from app.core.config import SiliconFlow_API_KEY, DEEPSEEK_API_KEY

embed_client = OpenAI(
    api_key=SiliconFlow_API_KEY,
    base_url="https://api.siliconflow.cn/v1",
)

llm_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)

def get_embedding(text):
    resp = embed_client.embeddings.create(
        model="BAAI/bge-large-zh-v1.5",
        input=text
    )
    return resp.data[0].embedding

with open("data/lingnan_docs.txt", "r", encoding="utf-8") as f:
    text = f.read().strip()
if not text:
    raise ValueError("data/lingnan_docs.txt 是空的，先粘贴文档内容")


CHUNK_SIZE = 200
chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
chunks = [c.strip() for c in chunks if c.strip()]

chroma = chromadb.PersistentClient(path="./chroma_db")
collection = chroma.get_or_create_collection("lingnan_RAG")

ids = [f"chunk_{i}" for i in range(len(chunks))]
embeddings = [get_embedding(c) for c in chunks]


collection.add(
    ids = ids,
    documents = chunks,
    embeddings = embeddings
)

print("入库完成")


question = "国家奖学金和励志奖学金能一起拿吗?"
q_emb = get_embedding(question)
results = collection.query(
    query_embeddings=[q_emb],
    n_results=3
)

top_chunks=results["documents"][0]
context="\n\n".join(top_chunks)
print("=== 召回段落 ===")
print(context)


prompt = f"根据已知信息:{context},请回答问题:{question}"

resp = llm_client.chat.completions.create(
    model = "deepseek-v4-pro",
    messages = [
        {"role": "system", "content": "你只能根据给定资料回答，资料没有的内容就说不知道。"},
        {"role": "user", "content": prompt},

    ],
    stream = False,

)

answer = resp.choices[0].message.content

print("=== 最终答案 ===")
print(answer)