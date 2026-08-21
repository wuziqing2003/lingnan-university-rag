import logging
import uuid
import httpx
import streamlit as st
from frontend.config import DEMO_SESSION_LIMIT
from frontend.api.client import stream_from_backend

def _format_source_caption(s: dict) -> str:
    name = s.get("source") or "未知"
    url = (s.get("url") or "").strip()
    if url:
        # 联网：标题 + 链接
        return f"来源：[{name}]({url})"
    page = s.get("page")
    page_s = f" p.{page}" if page is not None else ""

    return f"来源：{name}{page_s}"

def _format_steps(steps: list) -> str:
    lines = []
    for s in steps:
        if s.get("kind") == "action":
            name = s.get("name") or "工具"
            args = s.get("args") or {}
            query = args.get("query") if isinstance(args, dict) else args
            lines.append(f"**调用工具** `{name}`  \n参数：{query}")
        elif s.get("kind") == "observation":
            lines.append(f"**工具返回结果**  \n{s.get('content') or ''}")
        elif s.get("kind") == "thought":
            lines.append(f"**思考**  \n{s.get('delta') or ''}")
    return "\n\n".join(lines)

def _render_assistant_body(content: str, steps: list | None, sources: list | None) -> None:
    if steps:
        st.caption(_format_steps(steps))
    if content:
        st.markdown(content)
    for s in sources or []:
        st.caption(_format_source_caption(s))

def render_chat() -> None:
    st.markdown(
        '<p class="brand-title">教务规章助手</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="brand-sub">'
        "Agent 检索校内公开规章，必要时联网查询公开信息并标注来源；"
        "流式返回答复，无依据不编造。"
        "</p>",
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "demo_used" not in st.session_state:
        st.session_state.demo_used = 0
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    remain = max(DEMO_SESSION_LIMIT - st.session_state.demo_used, 0)
    st.caption(f"演示额度：本会话剩余 {remain}/{DEMO_SESSION_LIMIT} 次")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                _render_assistant_body(
                    message.get("content") or "",
                    message.get("steps") or [],
                    message.get("sources") or [],
                )
            else:
                st.markdown(message["content"])
            

    pending = st.session_state.pop("pending_question", None)
    typed = st.chat_input("输入学籍、资助等校内规定，或需要联网的公开资讯问题…")
    prompt = pending or typed

    if prompt:
        if st.session_state.demo_used >= DEMO_SESSION_LIMIT:
            st.warning("本会话演示次数已用完。")
            return 
        st.session_state.demo_used += 1
        
        
       

        logging.info("用户提问: %s", prompt[:50])
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                thought_box = st.empty()   # 先创建 → 在上面
                answer_box = st.empty()
                gen,result = stream_from_backend(prompt, st.session_state.thread_id)
                full_response = ""
                cleared_for_tools = False
                for delta in gen:
                    if result.steps:
                        thought_box.caption(_format_steps(result.steps))
                        if not cleared_for_tools:
                            full_response = ""
                            answer_box.markdown("")
                            cleared_for_tools = True

                    if delta:
                        full_response += delta
                        answer_box.markdown(full_response)
           
                if result.error:
                    st.warning(result.error)
                for s in result.sources:
                    st.caption(_format_source_caption(s))
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": full_response,
                        "sources": result.sources,
                        "steps": result.steps
                    }
                )
              
                logging.info("回答内容: %s", full_response[:50])
                st.rerun()
                            
                
                
            except httpx.HTTPError:
                logging.exception("FastAPI 流式调用失败")
                st.error("无法连接后端或生成失败，请确认 FastAPI 已启动后重试。")
