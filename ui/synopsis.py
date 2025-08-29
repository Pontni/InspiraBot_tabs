import streamlit as st
from ui.common import render_chat_area

def render():
    st.header("📝 Synopsis")
    st.write("Summarize your story in 5–8 sentences. Keep science accurate and central.")
    render_chat_area(input_key="synopsis_chat_input")  # <-- unique key
