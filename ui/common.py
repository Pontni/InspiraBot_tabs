# === BEGIN FILE: ui/common.py ===
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
    lines = ["Use this context for guiding the user to write the story. Do not re-ask for the form or introduce yourself."]
    for k, v in (form_data or {}).items():
        lines.append(f"- {k}: {v if v else '(empty)'}")
    lines.append("Next: acknowledge briefly and proceed with outlining when prompted.")
    return "\n".join(lines)

def lock_card(msg: str) -> None:
    st.warning(msg)

def require_unlocked_for_outline() -> None:
    if not st.session_state.get("form_valid", False):
        lock_card("Complete and submit the *Key Pieces form* to start the Outline.")
        st.stop()

def render_chat_area(input_key: str):
    """Chat with input shown ABOVE previous messages (old app feel)."""
    if not st.session_state.get("form_valid", False):
        lock_card("Complete and submit the *Key Pieces form* to start chatting.")
        st.stop()

    # 1) input first (so it appears above)
    user_prompt = st.chat_input("Message InspiraBot…", key=input_key)

    # 2) history after (so messages appear below the input)
    for msg in st.session_state.get("chat_history", []):
        avatar = "👩🏼‍💻" if msg["role"] == "user" else st.session_state.get("assistant_avatar", "Avatar.png")
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["parts"])

    # 3) handle new input
    if user_prompt:
        st.session_state.chat_history.append({"role": "user", "parts": user_prompt})
        with st.chat_message("user", avatar="👩🏼‍💻"):
            st.markdown(user_prompt)

        with st.chat_message("assistant", avatar=st.session_state.get("assistant_avatar", "Avatar.png")):
            placeholder, parts = st.empty(), []
            try:
                for chunk in st.session_state.chat.send_message_stream(user_prompt):
                    if getattr(chunk, "text", None):
                        parts.append(chunk.text)
                        placeholder.markdown("".join(parts) + "▌")
                        time.sleep(0.01)
                full = "".join(parts) if parts else ""
                placeholder.markdown(full or "_No response text received._")
            except Exception as e:
                full = f"❌ Error from model: {e}"
                placeholder.error(full)

        st.session_state.chat_history.append({"role": "assistant", "parts": full})
# === END FILE ===
