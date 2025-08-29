# CUSTOM BOT TEMPLATE
# Copyright (c) 2025 Ronald A. Beghetto
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this code and associated files, to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the code, and to permit
# persons to whom the code is furnished to do so, subject to the
# following conditions:
#
# An acknowledgement of the original template author must be made in any use,
# in whole or part, of this code. The following notice shall be included:
# "This code uses portions of code developed by Ronald A. Beghetto for a
# course taught at Arizona State University."
#
# THE CODE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import streamlit as st
from PIL import Image
import os, time

# --- Google GenAI imports ---------------------------
from google import genai
from google.genai import types
# ----------------------------------------------------

# Streamlit page setup
st.set_page_config(
    page_title="InspiraBot",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Helper: safe image open (supports /assets fallback) ----------------------
def _open_image_any(path1: str, path2: str):
    for p in (path1, path2):
        try:
            if os.path.exists(p):
                return Image.open(p)
        except Exception:
            pass
    raise FileNotFoundError(f"Could not find image at {path1} or {path2}")

# Display bot image (keeps your original caption)
try:
    img = _open_image_any("InspiraBot.png", os.path.join("assets", "InspiraBot.png"))
    st.image(img, caption="Bot Created by I. Pont-Niclos (2025)", use_container_width=True)
except Exception as e:
    st.error(f"Error loading image: {e}")

st.title("InspiraBot")

# Optional CSS — remove bubble/bg only for assistant messages using Avatar.png
st.markdown(
    "<style>"
    "[data-testid='stChatMessage']:has(img[src*=\"Avatar.png\"]) "
    "{background:transparent!important;box-shadow:none!important;}"
    "[data-testid='stChatMessage']:has(img[src*=\"Avatar.png\"]) "
    "[data-testid='stChatMessageAvatar']"
    "{background:transparent!important;border:none!important;box-shadow:none!important;}"
    "</style>",
    unsafe_allow_html=True
)

# --- Sidebar ----------------------------------------
with st.sidebar:
    st.title("⚙️ Controls")
    st.markdown(
        "### About\n"
        "This is a friendly AI-powered chatbot for educational storytelling. "
        "Use the tabs from left to right. The assistant nudges ideas but never writes the full story. "
        "Verify important information."
    )
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.pop("chat", None)
        st.session_state.pop("chat_history", None)
        st.rerun()

# --- Helpers ----------------------------------------
def load_system_prompt() -> str:
    try:
        with open("rules.txt") as f:
            return f.read()
    except FileNotFoundError:
        return "You are InspiraBot. Follow the rules provided by the instructor. Be helpful, friendly, and concise."

# --- Gemini configuration ---------------------------
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    system_instructions = load_system_prompt()
    search_tool = types.Tool(google_search=types.GoogleSearch())

    generation_cfg = types.GenerateContentConfig(
        system_instruction=system_instructions,
        tools=[search_tool],
        temperature=1.0,
        top_p=1,
        top_k=1,
        max_output_tokens=2048,
    )

    if "chat" not in st.session_state:
        st.session_state.chat = client.chats.create(
            model="gemini-2.5-flash",
            config=generation_cfg,
        )
except Exception as e:
    st.error(f"Gemini initialization error: {e}")

# Ensure chat history store exists
st.session_state.setdefault("chat_history", [])

# Resolve assistant avatar path (supports /assets or root)
if "assistant_avatar" not in st.session_state:
    st.session_state["assistant_avatar"] = (
        os.path.join("assets", "Avatar.png")
        if os.path.exists(os.path.join("assets", "Avatar.png"))
        else "Avatar.png"
    )

# --- Tabs glue ---------------------------------------------------------------
from ui import intro, key_pieces, outline, synopsis, brainstorm, drafting

TAB_LABELS = ["👋 Intro", "🌱 Key Pieces", "💭 Outline", "📝 Synopsis", "🧠 Brainstorm", "✏️ Drafting"]
tabs = st.tabs(TAB_LABELS)

with tabs[0]:
    intro.render()
with tabs[1]:
    key_pieces.render()
with tabs[2]:
    outline.render()      # includes chat session (guided outline)
with tabs[3]:
    synopsis.render()     # includes chat session (synopsis + save/validate)
with tabs[4]:
    brainstorm.render()   # skeleton only in Phase 1a
with tabs[5]:
    drafting.render()     # skeleton only in Phase 1a

# Footer
st.markdown(
    "<div style='text-align:center;color:gray;font-size:12px;'>"
    "I can make mistakes—please verify important information."
    "</div>",
    unsafe_allow_html=True,
)

