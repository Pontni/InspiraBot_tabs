
import streamlit as st
from ui.common import looks_gibberish, build_form_context

def render():
    # Heading + short explainer
    st.header("🌱 Key Pieces")
    st.write(
        "Set the key details for your story"
    )

    # --- FORM --------------------------------------------------------------
    with st.form("story_form"):
        educational_level = st.text_input(
            "Educational level",
            placeholder="e.g., Elementary school, Primary school, Secondary school, University",
            value=st.session_state.get("form_data", {}).get("Educational level", ""),
        )
        topic = st.text_input(
            "Scientific concept or topic",
            placeholder="e.g., Photosynthesis, Human digestion, Renewable energy, Chemical reactions",
            value=st.session_state.get("form_data", {}).get("Scientific concept or topic", ""),
        )
        genre = st.text_input(
            "Genre",
            placeholder="e.g., Fantasy, Adventures, Science fiction, Romance",
            value=st.session_state.get("form_data", {}).get("Genre", ""),
        )
        setting = st.text_input(
            "Story setting",
            placeholder="e.g., Imaginary World, Real World, Blended",
            value=st.session_state.get("form_data", {}).get("Story setting", ""),
        )
        goals = st.text_area(
            "Additional information",
            placeholder="e.g., Specific teaching goals, transdisciplinar connections, SDG integration",
            value=st.session_state.get("form_data", {}).get("Additional information", ""),
        )

        # Buttons row: Modify (left) | Submit (right)
        left, right = st.columns([1, 1])
        with left:
            modify = st.form_submit_button("✏️ Modify", use_container_width=True)
        with right:
            submitted = st.form_submit_button("✅ Submit", use_container_width=True)

    # --- STATE DEFAULTS ----------------------------------------------------
    st.session_state.setdefault("form_data", {})
    st.session_state.setdefault("form_feedback", "")
    st.session_state.setdefault("form_valid", False)
    st.session_state.setdefault("form_context_sent", False)

    # --- SUBMIT HANDLER ----------------------------------------------------
    if submitted:
        st.session_state["form_data"] = {
            "Educational level": (educational_level or "").strip(),
            "Scientific concept or topic": (topic or "").strip(),
            "Genre": (genre or "").strip(),
            "Story setting": (setting or "").strip(),
            "Additional information": (goals or "").strip(),
        }

        problems = []
        # Basic “looks like real text” validation for key fields
        for label in ("Educational level", "Scientific concept or topic", "Genre", "Story setting"):
            value = st.session_state["form_data"][label]
            if looks_gibberish(value):
                problems.append(f"Please clarify **{label}** (avoid random strings).")

        if problems:
            st.session_state["form_feedback"] = " ".join(problems)
            st.session_state["form_valid"] = False
        else:
            st.session_state["form_feedback"] = "Great — form saved. You can now go to **💭 Outline**."
            st.session_state["form_valid"] = True

            # One-time: silently prime the chat with the validated brief
            if not st.session_state.get("form_context_sent", False):
                try:
                    context_msg = build_form_context(st.session_state["form_data"])
                    # Hidden priming message (no UI echo)
                    st.session_state.chat.send_message(context_msg)
                    st.session_state["form_context_sent"] = True
                except Exception as e:
                    st.warning(f"Could not send form context to the assistant: {e}")

    elif modify:
        st.info("✏️ Adjust any field above and press **Submit** when ready.")

    # --- FEEDBACK ----------------------------------------------------------
    if st.session_state["form_feedback"]:
        if st.session_state["form_valid"]:
            st.success(st.session_state["form_feedback"])
        else:
            st.error(st.session_state["form_feedback"])
