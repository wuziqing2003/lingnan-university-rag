import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(ellipse 80% 50% at 50% -10%, #f3e8e8 0%, transparent 55%),
                linear-gradient(180deg, #faf8f6 0%, #f0f2f5 100%);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ffffff 0%, #f7f4f2 100%);
            border-right: 1px solid #e8e2de;
        }
        .brand-title {
            font-family: "Source Han Serif SC", "Noto Serif SC", "Songti SC", Georgia, serif;
            font-size: 1.75rem;
            font-weight: 700;
            color: #8b1e1e;
            letter-spacing: 0.04em;
            margin: 0.2rem 0 0.35rem 0;
        }
        .brand-sub {
            color: #5c656e;
            font-size: 0.95rem;
            margin-bottom: 1.25rem;
            line-height: 1.5;
        }
        .status-ok { color: #1f7a4c; font-weight: 600; }
        .status-bad { color: #a33b3b; font-weight: 600; }
        div[data-testid="stChatMessage"] {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid #ebe4df;
            border-radius: 14px;
            padding: 0.15rem 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
