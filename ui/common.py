# === BEGIN FILE: ui/common.py ===
import streamlit as st

def looks_gibberish(s: str) -> bool:
    """Very light guard for empty / random-like inputs."""
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
    """Turn saved Key Pieces into a compact context string for the assistant."""
    lines = [
        "Use this context to guide the student in writing the story. "
        "Do not re-ask for this form and do not introduce yourself."
    ]
    for k, v in (form_data or {}).items():
        lines.append(f"- {k}: {v if v else '(empty)'}")
    lines.append("When the student opens Outline, acknowledge briefly and start helping.")
    return "\n".join(lines)


def lock_card(msg: str) -> None:
    """Plain yellow warning card (no emojis)."""
    st.warning(msg)


def require_unlocked_for_outline() -> None:
    """Stop rendering Outline unless the Key Pieces form has been submitted."""
    if not st.session_state.get("form_valid", False):
        lock_card("Complete and submit the *Key Pieces form* to start the Outline.")
        st.stop()
# === END FILE: ui/common.py ===
