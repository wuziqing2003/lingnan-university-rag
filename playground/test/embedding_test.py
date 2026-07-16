from app.core.config import SiliconFlow_API_KEY

from openai import OpenAI


client = OpenAI(
    api_key = SiliconFlow_API_KEY,
    base_url = "https://api.siliconflow.cn/v1"
)


resp = client.embeddings.create(
    model = "BAAI/bge-large-zh-v1.5",
    input = "岭南师范学院"

)

vector = resp.data[0].embedding
print(len(vector))
print(vector[:5])

assert len(vector) == 1024