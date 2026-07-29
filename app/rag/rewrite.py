# app/rag/rewrite.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import DEEPSEEK_API_KEY



REWRITE_PROMPT = ChatPromptTemplate([
    ("system", """你是岭南师范学院规章检索的 query 改写助手。
把用户问题改写成更适合在校规 PDF 中检索的表述。
要求：
1. 保留原意，不增减事实条件
2. 口语/简称换成规章常见词，例如：
   - 助学金/奖助 → 国家助学金/学业奖学金等规范名
   - 挂科/重修 → 课程考核、补考、重修
   - 转专业、缓考、勤工助学、三助一辅 等尽量用规范术语
3. 只输出改写后的一句话，不要解释、不要引号
4. 若原问题已经规范，可原样输出"""),
    ("human", "{question}"),
])


_rewrite_llm = ChatOpenAI(
    model="deepseek-chat",  # 改写用小/快模型即可，省成本降延迟
    base_url="https://api.deepseek.com",
    api_key=DEEPSEEK_API_KEY,
    temperature=0,

)


_rewrite_chain = REWRITE_PROMPT | _rewrite_llm | StrOutputParser()


def rewrite_query(question:str):
    q = (question or "").strip()
    if not q:
        return q

    try:
        out = _rewrite_chain.invoke({"question":q}).strip()
        return out or q
    except Exception:
        return q