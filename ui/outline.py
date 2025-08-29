
import streamlit as st
from ui.common import require_unlocked_for_outline, render_chat_area

def render():
    st.header("💭 Outline")
    st.write("Define your characters, setting, and the central conflict.")

    # Gate: requires a valid Key Pieces form
    require_unlocked_for_outline()

    # (We’ll refine the outline flow later; for now just use the shared chat area)
    render_chat_area()
