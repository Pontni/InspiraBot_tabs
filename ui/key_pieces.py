# === BEGIN FILE: ui/key_pieces.py ===
import streamlit as st
from .common import looks_gibberish, build_form_context

def render():
    st.header("🌱 Set up your Story Brief")
    st.write("Tell the bot your context so guidance fits your class.")

    # --- FORM --------------------------------------------------------------
    with st.form("story_form"):
        educational_level = st.text_input(
            "Educational level",
            placeholder="e.g., Elementary school, Primary school, Secondary school, University",
        )
        topic = st.text_input(
            "Scientific concept or topic",
            placeholder="e.g., Photosynthesis, Human digestion, Renewable energy, Chemical reactions",
        )
        genre = st.text_input(
            "Genre",
            placeholder="e.g., Fantasy, Detective story, Science fiction",
        )
        setting = st.text_input(
            "Story setting",
            placeholder="e.g., Imaginary world, Real World, Blended",
        )
        goals = st.text_area(
            "Additional curricular goals or SDG link (optional)",
            placeholder="e.g., SDG 7 Affordable and Clean Energy; inquiry skills; collaboration",
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("✅ Submit", use_container_width=True)
        with col2:
            modify = st.form_submit_button("✏️ Modify", use_container_width=True)

    # --- STATE DEFAULTS ----------------------------------------------------
    st.session_state.setdefault("form_data", {})
    st.session_state.setdefault("form_feedback", "")
    st.session_state.setdefault("form_valid", False)
    st.session_state.setdefault("form_context_sent", False)

    # --- SUBMIT HANDLER ----------------------------------------------------
    if submitted:
        st.session_state["form_data"] = {
            "Educational level": educational_level.strip(),
            "Scientific concept or topic": topic.strip(),
            "Genre": genre.strip(),
            "Story setting": setting.strip(),
            "Additional information": goals.strip(),
        }

        problems = []
        for label, value in st.session_state["form_data"].items():
            if label in ("Educational level", "Scientific concept or topic", "Genre", "Story setting"):
                if looks_gibberish(value):
                    problems.append(f"Please clarify **{label}** (avoid random strings).")

        if problems:
            st.session_state["form_feedback"] = " ".join(problems) or "Please fix the highlighted fields."
            st.session_state["form_valid"] = False
        else:
            st.session_state["form_feedback"] = "Good start! Let’s move on to the outline of your story."
            st.session_state["form_valid"] = True

            # One-time: silently prime the chat with the validated brief
            if not st.session_state.get("form_context_sent", False):
                try:
                    context_msg = build_form_context(st.session_state["form_data"])
                    st.session_state.chat.send_message(context_msg)  # hidden message (no UI echo)
                    st.session_state["form_context_sent"] = True
                except Exception as e:
                    st.warning(f"Could not send form context to the assistant: {e}")

    elif modify:
        st.info("✏️ You can adjust your answers above and submit again when ready.")

    # --- FEEDBACK ----------------------------------------------------------
    if st.session_state["form_feedback"]:
        if st.session_state["form_valid"]:
            st.success(st.session_state["form_feedback"])
        else:
            st.error(st.session_state["form_feedback"])
# === END FILE ===
