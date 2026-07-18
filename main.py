import streamlit as st

from frontend.components.chat import render_chat
from frontend.components.sidebar import render_sidebar
from frontend.config import BADGE_PATH
from frontend.styles.theme import inject_theme

st.set_page_config(
    page_title="岭南师范学院 · 教务智能问答",
    page_icon=str(BADGE_PATH) if BADGE_PATH.exists() else "📔",
    layout="centered",
    initial_sidebar_state="expanded",
)

inject_theme()
render_sidebar()
render_chat()
