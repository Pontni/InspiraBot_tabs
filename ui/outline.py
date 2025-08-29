# === BEGIN FILE: ui/outline.py ===
import streamlit as st
from .common import require_unlocked_for_outline, render_chat_area

def render():
    st.header("💭 Map Your Story (Outline)")
    st.write("Define who, where, and the central problem. Ask InspiraBot for nudges anytime.")

    require_unlocked_for_outline()  # needs 🌱 Key Pieces submitted
    render_chat_area()              # same chat session as other tabs
# === END FILE ===

