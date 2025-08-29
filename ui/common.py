
import time
import streamlit as st

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
    lines = [
        "Use this context for guiding the user to write the story. Do not re-ask for the form or introduce yourself."
    ]
    for k, v in (form_data or {}).items():
        lines.append(f"- {k}: {v if v else '(empty)'}")
    lines.append("Next: acknowledge briefly and proceed with outlining when prompted.")
    return "\n".join(lines)

# --- Warning card helper (yellow) ---
def lock_card(msg: str) -> None:
    # Plain yellow warning card
    st.warning(msg)

# --- Gate: Outline requires a valid Key Pieces form ---

def render_chat_area(input_key: str):
    # 1) Guard: if Key Pieces not valid, show the yellow warning and stop.
    if not st.session_state.get("form_valid", False):
        lock_card("Complete and submit the *Key Pieces form* to start the Outline.")
        st.stop()

    # 2) Replay history (messages already stored in st.session_state.chat_history)
    for msg in st.session_state.get("chat_history", []):
        with st.chat_message(msg["role"], avatar=("👩🏼‍💻" if msg["role"]=="user" else st.session_state.get("assistant_avatar", "Avatar.png"))):
            st.markdown(msg["parts"])

    # 3) Collect new user input — the **unique key** avoids the duplicate id error
    user_prompt = st.chat_input("Message InspiraBot…", key=input_key)
    if not user_prompt:
        return

    # 4) Immediately echo the user turn to the UI and save to history
    st.session_state.chat_history.append({"role": "user", "parts": user_prompt})
    with st.chat_message("user", avatar="👩🏼‍💻"):
        st.markdown(user_prompt)

    # 5) Stream model reply via the **single shared chat session**
    with st.chat_message("assistant", avatar=st.session_state.get("assistant_avatar", "Avatar.png")):
        placeholder = st.empty()
        parts = []
        for chunk in st.session_state.chat.send_message_stream(user_prompt):
            if getattr(chunk, "text", None):
                parts.append(chunk.text)
                placeholder.markdown("".join(parts) + "▌")
        full = "".join(parts) if parts else ""
        placeholder.markdown(full or "_No response text received._")

    # 6) Save assistant turn to history
    st.session_state.chat_history.append({"role": "assistant", "parts": full})
