# === BEGIN FILE: ui/intro.py ===
import streamlit as st

def render():
    st.header("👋 Welcome to InspiraBot")
    st.write("We’ll co-create an educational story step-by-step. Follow the tabs from left to right. You’ll end with a clear synopsis and strong ideas to draft your story.")

    with st.expander("What you’ll produce"):
        st.markdown("- A **story brief** (Key Pieces)\n- A **mapped outline** (characters, scenario, conflict)\n- A **concise synopsis**\n- **Brainstormed ideas** ready for drafting")

    with st.expander("Tips for success"):
        st.markdown("- Align with your **level & goals**\n- Keep **science accurate** and **age-appropriate**\n- Try **What if… / Why not… / As if…** prompts in Brainstorm")
# === END FILE ===

