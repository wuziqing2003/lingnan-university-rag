import streamlit as st
from frontend.config import DEMO_SESSION_LIMIT
from frontend.api.client import check_backend
from frontend.config import EXAMPLE_QUESTIONS


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### 教务规章助手")
        st.caption("岭南师范学院 · 知识库 + 联网")

        backend_ok = check_backend()
        if backend_ok:
            st.markdown(
                '<p class="status-ok">● 后端已连接</p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p class="status-bad">● 后端未连接</p>',
                unsafe_allow_html=True,
            )
            st.caption("请先启动：`python -m app.main`")
        used = st.session_state.get("demo_used", 0)
        remain = max(DEMO_SESSION_LIMIT - used, 0)

        st.caption(f"本会话剩余演示次数：{remain}/{DEMO_SESSION_LIMIT}")

        st.divider()
        st.markdown("**试试这些问题**")
        for q in EXAMPLE_QUESTIONS:
            if st.button(q, use_container_width=True, key=f"ex_{q}"):
                st.session_state["pending_question"] = q
                st.rerun()

        st.divider()
        if st.button("清空对话", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pop("pending_question", None)
            st.session_state.thread_id = str(__import__("uuid").uuid4())
            st.rerun()

        st.caption(
            "校内规定走知识库；公开/时效信息可联网检索并附链接。"
            "资料不足时如实说明，不编造。个人项目，非学校官方渠道。"
        )
