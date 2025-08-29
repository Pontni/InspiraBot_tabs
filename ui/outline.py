
import streamlit as st
from ui.common import require_unlocked_for_outline, render_chat_area

def render():
    st.header("💭 Outline")
    st.write("Define your characters, setting, and the central problem. Ask for nudges any time.")

    # Gate: requires a valid Key Pieces form
    require_unlocked_for_outline()

    # Use the shared chat area; pass a UNIQUE input key for this tab
    render_chat_area(input_key="outline_chat_input")
