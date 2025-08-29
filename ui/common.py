# -*- coding: utf-8 -*-
import streamlit as st
import time

# ---- Lightweight validators -------------------------------------------------
def looks_gibberish(s: str) -> bool:
    s = (s or "").strip()
    if not s:
        return True
    lower = s.lower()
    letters_only = "".join(c for c in lower if c.isalpha())

    if len(set(lower)) <= 3 and len(lower) >= 6:
        return True
    if " " not in s and len(letters_only) >= 6 and not any(v in letters_only for v in "aeiou"):
        return True
    if " " not in s and len(letters_only) >= 10 and len(set(letters_only)) <= 4:
        return True

    nonspace = sum(1 for c in s if not c.isspace())
    letters = sum(c.isalpha() for c in s)
    if nonspace > 0 and (letters / nonspace) < 0.5:
        return True
    return False


def build_form_context(form_data: dict) -> str:
    """One-time context message used to prime the assistant after a valid submit."""
    lines = [
        "Use this context for guiding the user to write the story. Do not re-ask for the form or introduce yourself."
    ]
    for k, v in (form_data or {}).items():
        lines.append(f"- {k}: {v if v else '(empty)'}")
    lines.append("Next: acknowledge briefly and proceed with outlining when prompted.")
    return "\n".join(lines)


# ---- UI helpers -------------------------------------------------------------
def lock_card(msg: str) -> None:
    """Plain yellow warning card (no emoji, per design)."""
    st.warning(msg)


def require_unlocked_for_outline() -> None:
    """
    Gate for the Outline tab. If the Key Pieces form is not valid yet,
    show the warning and stop rendering the tab.
    """
    if not st.session_state.get("form_valid", False):
        lock_card("Complete and submit the *Key Pieces form* to start the Outline.")
        st.stop()


# ---- Shared chat area -------------------------------------------------------
def render_chat_area(input_key: str = "chat_input") -> None:
    """
    Replay chat history, accept a new user turn, and stream the assistant reply.

    IMPORTANT:
    - `input_key` must be UNIQUE per tab (e.g., "outline_chat_input", "synopsis_chat_input")
      to avoid StreamlitDuplicateElementId errors.
    - Requires that `st.session_state.chat` (the model chat object) and
      `st.session_state.chat_history` (list of dicts) are initialized in app.py.
    """
    # Guard: ensure Key Pieces has been submitted, and chat session exists
    if not st.session_state.get("form_valid", False):
        lock_card("Complete and submit the *Key Pieces form* to start the Outline.")
        st.stop()

    if "chat" not in st.session_state:
        st.error("Chat session is not initialized. Please restart the app or contact your teacher.")
        st.stop()

    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("assistant_avatar", "Avatar.png")

    # 1) Replay history
    for msg in st.session_state.get("chat_history", []):
        avatar = "👩🏼‍💻" if msg["role"] == "user" else st.session_state["assistant_avatar"]
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["parts"])

    # 2) Collect new user input (unique key per tab prevents duplicate ID)
    user_prompt = st.chat_input("Message InspiraBot…", key=input_key)
    if not user_prompt:
        return

    # 3) Echo user + save
    st.session_state.chat_history.append({"role": "user", "parts": user_prompt})
    with st.chat_message("user", avatar="👩🏼‍💻"):
        st.markdown(user_prompt)

    # 4) Stream assistant reply from the single shared chat session
    full = ""
    with st.chat_message("assistant", avatar=st.session_state["assistant_avatar"]):
        placeholder = st.empty()
        parts = []
        try:
            for chunk in st.session_state.chat.send_message_stream(user_prompt):
                text = getattr(chunk, "text", None)
                if text:
                    parts.append(text)
                    placeholder.markdown("".join(parts) + "▌")
                    # small tick keeps the UI responsive without being heavy
                    time.sleep(0.01)
            full = "".join(parts) if parts else ""
            placeholder.markdown(full or "_No response text received._")
        except Exception as e:
            full = f"❌ Error from Gemini (streaming): {e}"
            placeholder.error(full)

    # 5) Save assistant turn
    st.session_state.chat_history.append({"role": "assistant", "parts": full})
