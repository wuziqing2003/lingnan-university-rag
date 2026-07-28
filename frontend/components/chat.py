import logging

import httpx
import streamlit as st

from frontend.api.client import stream_from_backend
from frontend.config import BADGE_PATH


def render_chat() -> None:
    if BADGE_PATH.exists():
        st.logo(str(BADGE_PATH), size="large")

    st.markdown(
        '<p class="brand-title">教务智能问答</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="brand-sub">检索校内公开规章与教务资料，流式返回答复。无依据不编造。</p>',
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            for s in message.get("sources") or []:
                page = s.get("page")
                page_s = f" p.{page}" if page is not None else ""
                st.caption(f"来源：{s.get('source', '未知')}{page_s}")

    pending = st.session_state.pop("pending_question", None)
    typed = st.chat_input("输入教务、资助、学籍等相关问题…")
    prompt = pending or typed

    if prompt:
       

        logging.info("用户提问: %s", prompt[:50])
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                gen,result = stream_from_backend(prompt)
                full_response = st.write_stream(gen)
                if not full_response:
                    full_response = ""
                for s in result.sources:
                    page = s.get("page")
                    page_s = f" p.{page}" if page is not None else ""
                    st.caption(f"来源：{s.get('source', '未知')}{page_s}")
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": full_response,
                        "sources": result.sources,
                    }
                )
                logging.info("回答内容: %s", full_response[:50])
                            
                
                
            except httpx.HTTPError:
                logging.exception("FastAPI 流式调用失败")
                st.error("无法连接后端或生成失败，请确认 FastAPI 已启动后重试。")
