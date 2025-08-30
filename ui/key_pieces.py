# === BEGIN FILE: ui/key_pieces.py ===
import streamlit as st
from ui.common import build_form_context, looks_gibberish

def _ensure_defaults():
    ss = st.session_state
    ss.setdefault("form_valid", False)
    ss.setdefault("form_data", {})
    ss.setdefault("editing_form", True)   # show form by default until submitted
    ss.setdefault("chat_history", [])
    ss.setdefault("assistant_avatar", "assets/Avatar.png")
    ss.setdefault("model_name", "gemini-2.0-flash")

def _submit_form(form_vals: dict):
    """Create/refresh the system prompt + chat session when the form is submitted."""
    from google import generativeai as genai

    ss = st.session_state
    ss["form_data"] = form_vals
    ss["form_valid"] = True
    ss["editing_form"] = False

    # Build the system instruction: rules + form context
    rules = ss.get("rules_text", "")
    form_ctx = build_form_context(ss["form_data"])
    system_text = (rules or "").strip() + "\n\n" + form_ctx

    # (Re)create model + chat session and reset UI-visible history
    model_name = ss.get("model_name", "gemini-2.0-flash")
    model = genai.GenerativeModel(model_name, system_instruction=system_text)
    chat = model.start_chat(history=[])
    ss["model_name"] = model_name
    ss["model"] = model
    ss["chat"] = chat
    ss["chat_history"] = []


def render():
    _ensure_defaults()

    st.header("🌱 Key Pieces")
    st.caption("Fill this brief so InspiraBot can tailor its guidance to your project.")

    ss = st.session_state

    # Toggle back to edit mode
    if ss.get("form_valid") and not ss.get("editing_form"):
        if st.button("✏️ Modify form", help="Edit and resubmit the brief"):
            ss["editing_form"] = True

    if ss.get("editing_form", True):
        with st.form("key_pieces_form"):
            col1, col2 = st.columns(2)
            with col1:
                level = st.text_input(
                    "Targeted Educational Level",
                    value=ss["form_data"].get("level", ""),
                    placeholder="e.g., Grade 5 / Secondary / Undergraduate"
                )
                concept = st.text_input(
                    "Scientific Concept",
                    value=ss["form_data"].get("concept", ""),
                    placeholder="e.g., Photosynthesis"
                )
                genre = st.text_input(
                    "Genre",
                    value=ss["form_data"].get("genre", ""),
                    placeholder="e.g., Fantasy, Sci-Fi, Mystery"
                )
            with col2:
                setting = st.text_input(
                    "Setting",
                    value=ss["form_data"].get("setting", ""),
                    placeholder="e.g., School greenhouse, Martian colony"
                )
                goals = st.text_area(
                    "Additional goals / curricular links",
                    value=ss["form_data"].get("goals", ""),
                    height=120,
                    placeholder="e.g., SDG links, assessment goals, constraints…"
                )

            # Right-aligned Submit button
            col_empty, col_btn = st.columns([4, 1])
            with col_btn:
                submitted = st.form_submit_button("✅ Submit", use_container_width=True)

            if submitted:
                if looks_gibberish(concept):
                    st.error("Please provide a clearer *Scientific Concept* before submitting.")
                else:
                    _submit_form(
                        {
                            "level": level.strip(),
                            "concept": concept.strip(),
                            "genre": genre.strip(),
                            "setting": setting.strip(),
                            "goals": goals.strip(),
                        }
                    )
                    st.success("Key Pieces saved. **💭 Outline** is now unlocked.")
    else:
        # Read-only view
        data = ss.get("form_data", {})
        st.subheader("Brief (read-only)")
        st.markdown(
            f"""
- **Level:** {data.get("level","—")}
- **Concept:** {data.get("concept","—")}
- **Genre:** {data.get("genre","—")}
- **Setting:** {data.get("setting","—")}
- **Goals:** {data.get("goals","—")}
            """.strip()
        )
# === END FILE: ui/key_pieces.py ===
