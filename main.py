import streamlit as st
import os
from openai import OpenAI
from datetime import datetime


client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com")
system_prompt = '''你是岭南师范学院专属官方RAG智能咨询助手，依托岭南师范学院官方公开文件、学生管理规定、教务管理办法、招生章程、就业政策、后勤管理条例、各院系官方公告等权威数据库为用户提供咨询服务。

核心工作准则：
1. 绝对权威：回答内容100%依托检索匹配的岭南师范学院官方知识库内容，无检索依据的信息一律不予作答，禁止主观推断、私自解读、虚假补充。
2. 精准合规：严格按照学校现行有效规章制度作答，区分新旧政策、通用规则与专项通知，不混用、不误导。
3. 场景限定：仅受理岭南师范学院招生咨询、学籍管理、教学考试、学生奖惩、资助评优、住宿后勤、校园管理、毕业离校、就业创业等校内相关业务咨询。
4. 答疑原则：条理清晰、表述严谨、忠于原文，涉及办理流程、申报条件、截止时间、所需材料等关键信息，完整、准确、无遗漏。
5. 兜底机制：若知识库未收录相关问题、信息缺失或内容模糊，统一告知用户：「当前暂无岭南师范学院相关官方信息，建议前往学校官网、咨询辅导员或对应职能部门核实办理。」'''
### 页面配置
st.set_page_config(
    page_title="Lingnan University RAG",
    page_icon="📔",
    layout="centered",
    initial_sidebar_state="auto",
)
st.caption("基于 RAG 技术，快速查询校园教务信息")
### 标题
st.header(
    "📚 教务智能问答系统",
    text_alignment="left",   # 文字靠左
    width="content",         # 宽度跟随内容，不撑满全行
    divider="gray"           # 分割线颜色
)
st.logo("data/school_badge.jpg",  size="large", )
### 侧边栏
with st.sidebar:
    st.title("岭南师范学院")
    st.caption("教务智能体系统 v1.0")
    st.divider()
def time_data():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
### 初始化会话状态messages
if 'messages' not in st.session_state:
    st.session_state.messages = []
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])
prompt = st.chat_input("请输入你的问题：")
if prompt:
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role":"user", "content":prompt})

    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content": system_prompt},
            *st.session_state.messages
        ],
        stream=True,

    )


    empty_container = st.empty()
    empty_str = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            empty_str += chunk.choices[0].delta.content
            empty_container.chat_message("assistant").write(empty_str)
    st.session_state.messages.append({"role":"assistant", "content":empty_str})






