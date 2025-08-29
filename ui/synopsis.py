# -*- coding: utf-8 -*-
import streamlit as st
from ui.common import render_chat_area

def render():
    st.header("📝 Write a Concise Synopsis")
    st.write("Summarize your story in 5–8 sentences. Keep science accurate and central.")
    render_chat_area()
