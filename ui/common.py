# === BEGIN FILE: ui/common.py ===
"""
Shared helpers used across multiple tabs.

Keep tab-specific logic (e.g., Outline-only state machines) inside that tab's
module so we avoid accidental cross-coupling.
"""

from __future__ import annotations

import time
import streamlit as st


# -----------------------------
# 1) Light validation utilities
# -----------------------------
def looks_gibberish(s: str) -> bool:
    """
    Heuristic to catch empty/noisy inputs like 'fjdkajfdlkasjfl'.
    It's intentionally simple—only to prevent accidental submits.
    """
    s = (s or "").strip()
    if not s:
        return True

    lower = s.lower()
    letters_only = "".join(c for c in lower if c.isalpha())

    # very few distinct characters over a long-ish span often means mashing
    if len(set(lower)) <= 3 and len(lower) >= 6:
        return True

    # long consonant clusters with no spaces
    if " " not in s and len(letters_only) >= 6 and not any(v in letters_only for v in "aeiou"):
        return True

    # very repetitive strings
    if " " not in s and len(letters_only) >= 10 and len(set(letters_only)) <= 4:
        return True

    # too many non-letters relative to letters
    nonspace = sum(1 for c in s if not c.isspace())
    letters = sum(c.isalpha() for c in s)
    if nonspace > 0 and (letters / nonspace) < 0.5:
        return True

    return False


def build_form_context(form_data: dict) -> str:
    """
    Convert the Key Pieces form into a compact context string the assistant
    can use. Do NOT re-ask for the form inside the chat.
    """
    lines = [
        "Use this brief to guide the student. Do not re-ask for the form or introduce yourself."
    ]
    for k, v in (form_data or {}).items():
        lines.append(f"- {k}: {v if v else '(empty)'}")
    lines.append("Acknowledge briefly, then continue the current stage when prompted.")
    return "\n".join(lines)


# --------------------------------
# 2) Small UI helpers / flow gates
# --------------------------------
def lock_card(msg: str) -> None:
    """Plain yellow warning card (no emoji)."""
    st.warning(msg)


def require_unlocked_for_outline() -> None:
    """
    Block Outline/Synopsis until the Key Pieces form was submitted & accepted.
    """
    if not st.session_state.get("form_valid", False):
        lock_card("Complete and submit the *Key Pieces form* to start the Outline.")
        st.stop()


# ---------------------------------------
# 3) Model-facing helpers (generic, safe)
# ---------------------------------------
def send_hidden(text: str) -> None:
    """
    Send an instruction message to the shared chat **without** adding a UI
    bubble. Use for one-time 'kickoff' nudges that steer the assistant.
    """
    chat = st.session_state.get("chat")
    if not chat:
        return
    try:
        chat.send_message(text)
    except Exception:
        # Don't crash the app if the SDK raises
        pass


def consolidate_outline_item(instruction: str) -> str:
    """
    Ask the model to condense the most-recent discussion into a short summary.
    Returns plain text (empty string on failure).
    """
    chat = st.session_state.get("chat")
    if not chat:
        return ""
    try:
        resp = chat.send_message(
            f"{instruction}\n\nUse only the student's ideas from the recent chat."
        )
        return (getattr(resp, "text", "") or "").strip()
    except Exception:
        return ""


# -------------------------------------------------
# 4) Chat area (history above, input box underneath)
# -------------------------------------------------
def render_chat_area(input_key: str) -> None:
    """
    Replays the conversation stored in st.session_state.chat_history,
    then renders the input box **below** the messages and streams the reply.

    Requirements (created elsewhere, e.g., in app.py on form submit):
      - st.session_state.chat           -> the Gemini chat/session object
      - st.session_state.chat_history   -> list[{"role": "user"/"assistant", "parts": str}]
      - st.session_state.assistant_avatar (optional) -> image path or emoji for assistant
    """
    history = st.session_state.get("chat_history", [])

    # 1) Replay history (keeps the input field below on each rerun)
    for msg in history:
        avatar = "👩🏼‍💻" if msg["role"] == "user" else st.session_state.get("assistant_avatar", "Avatar.png")
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["parts"])

    # 2) Input lives *after* the transcript
    user_prompt = st.chat_input("Message InspiraBot…", key=input_key)
    if not user_prompt:
        return

    # 3) Append & show user turn
    st.session_state.chat_history.append({"role": "user", "parts": user_prompt})
    with st.chat_message("user", avatar="👩🏼‍💻"):
        st.markdown(user_prompt)

    # 4) Stream the assistant reply
    with st.chat_message("assistant", avatar=st.session_state.get("assistant_avatar", "Avatar.png")):
        placeholder = st.empty()
        parts: list[str] = []
        try:
            for chunk in st.session_state.chat.send_message_stream(user_prompt):
                if getattr(chunk, "text", None):
                    parts.append(chunk.t
