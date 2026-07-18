import streamlit as st

from frontend.api.client import check_backend
from frontend.config import BADGE_PATH, EXAMPLE_QUESTIONS


def render_sidebar() -> None:
    with st.sidebar:
        if BADGE_PATH.exists():
            st.image(str(BADGE_PATH), width=96)
        st.markdown("### 岭南师范学院")
        st.caption("教务智能问答 · v1.0")

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
            st.rerun()

        st.caption("仅依据校内规章制度检索作答；知识库未覆盖时会如实告知。")
