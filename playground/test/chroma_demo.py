from openai import OpenAI
from app.core.config import SiliconFlow_API_KEY
import chromadb
###创建一个列表，里面存放着关于奖学金的信息
DOCUMENTS = [
    "国家奖学金是由中央政府出资设立，用以奖励在校本专科特别优秀学生的奖学金；国家励志奖学金由中央和地方政府共同出资，奖励资助品学兼优的家庭经济困难学生；国家助学金由中央和地方政府共同出资，资助家庭经济困难学生顺利完成学业。",
    "国家奖学金的奖励对象为学校在校全日制普通本专科二年级及以上（含专插本进入本科第二年、第二学士学位等）特别优秀的学生。",
    "国家励志奖学金的奖励资助对象为学校在校全日制普通本专科二年级及以上品学兼优的家庭经济困难学生。",
    "国家助学金的资助对象为学校在校全日制普通本专科的家庭经济困难学生。",
    "申请国家奖学金：评审学年的上一学年学习成绩和综合测评成绩排名均位于前10%（含）；同等条件下优先考虑没有补考、重修记录的学生。",
    "申请国家励志奖学金：须为经过认定的家庭经济困难学生，且评审学年上一学年学习成绩及综合测评成绩排名位于前30%（含）。",
    "国家奖学金奖励标准为每生每年10000元；国家励志奖学金为每生每年6000元；国家助学金按家庭经济困难等级分档，每生每年2500-5000元，平均资助标准为每生每年3700元。",
    "同一学年，国家奖学金与国家励志奖学金不可兼得；国家奖学金或国家励志奖学金获得者可同时申请获得国家助学金。",
    "国家奖助学金在每年9月开学两周后开始预申请，待上级部门分配名额后进行正式申请，实行等额评审，每学年评审一次。",
    "评审程序：学生向班级负责人提交申请→学院评议小组初审推荐→二级学院评审并公示3个工作日→学生助学中心复核→学校评审委员会和领导小组审定后全校公示5个工作日，无异议后上报省教育厅。",
]


IDS = [f"doc_{i}" for i in range(len(DOCUMENTS))]


client = OpenAI(
    api_key=SiliconFlow_API_KEY,
    base_url="https://api.siliconflow.cn/v1",
)

def get_embedding(text):
    resp = client.embeddings.create(
        model="BAAI/bge-large-zh-v1.5",
        input=text
    )
    return resp.data[0].embedding

chroma = chromadb.PersistentClient(path="./chroma_db")

collection = chroma.get_or_create_collection("scholarship")

embeddings = [get_embedding(doc) for doc in DOCUMENTS]

collection.add(
    embeddings=embeddings,
    documents=DOCUMENTS,
    ids=IDS
)

question = "国家奖学金有哪些申请条件？"
q_emb = get_embedding(question)

results = collection.query(
    query_embeddings=[q_emb],
    n_results=1
)

print(results["documents"][0][0])
print(results["distances"][0][0])



