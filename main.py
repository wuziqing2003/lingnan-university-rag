import streamlit as st

from frontend.components.chat import render_chat
from frontend.components.sidebar import render_sidebar
from frontend.config import LOGO_PATH
from frontend.styles.theme import inject_theme

st.set_page_config(
    page_title="教务规章助手 · 岭南师范学院",
    page_icon="🏫",
    layout="centered",
    initial_sidebar_state="expanded",
)

if LOGO_PATH.exists():
    st.logo(str(LOGO_PATH), size="large")

inject_theme()
render_sidebar()
render_chat()
