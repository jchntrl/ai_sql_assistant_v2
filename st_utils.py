import streamlit as st


def clear_chat_history(key="messages"):
    del st.session_state[key]

