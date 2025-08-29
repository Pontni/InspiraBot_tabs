# === BEGIN FILE: ui/synopsis.py ===
import streamlit as st
from .common import render_chat_area

def render():
    st.header("📝 Write a Concise Synopsis")
    st.write("Summarize your story in 5–8 sentences. Keep science accurate and central.")
    render_chat_area()  # same chat session as Outline
# === END FILE ===

