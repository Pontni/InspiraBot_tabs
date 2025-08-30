import streamlit as st
from ui.common import (
    require_unlocked_for_outline,
    render_chat_area,
    looks_gibberish,
    send_hidden,
    consolidate_outline_item,
    lock_card,
)

# ---------- Visible student instructions (hard-coded) ----------
KICKOFFS = {
    "characters": (
        "Let’s bring your story to life 👥✨. Imagine at least two characters with names and roles, "
        "and give each a trait or twist that makes them memorable. Share your ideas with me and we can "
        "keep brainstorming together as long as you’d like. When you feel ready, press **Complete Characters**."
    ),
    "scenario": (
        "Time to picture the world where everything unfolds 🌱✨. Describe the place, the time, and a detail "
        "that makes the setting unique. Share your thoughts here and I’ll help you explore new possibilities. "
        "When you’re ready, press **Complete Scenario**."
    ),
    "conflict": (
        "Every great story needs tension ⚔️🔥. Imagine what stands in the way—an outer struggle or an inner "
        "dilemma that drives decisions. Share your ideas with me and we can develop them further. "
        "When you feel ready, press **Complete Conflict**."
    ),
}

# ---------- One-time hidden nudges for the assistant ----------
KICKOFF_HIDDEN = {
    "characters": (
        "We are now beginning the Characters stage of an educational story. "
        "Use the Key Pieces brief and the rules to guide creative, possibility-thinking ideation. "
        "Ask ONE focused question at a time. Keep replies short and encouraging."
    ),
    "scenario": (
        "We are now beginning the Scenario stage. Help the student define world, time, and key places; "
        "encourage constraints that keep science central. Ask ONE focused question at a time."
    ),
    "conflict": (
        "We are now beginning the Conflict stage. Guide toward a science-grounded central problem or tension. "
        "Ensure it’s age-appropriate and invites inquiry. Ask ONE focused question at a time."
    ),
}

# ---------- Consolidation (bullets only) ----------
CONS_PROMPT = {
    "characters": "Reframe the student's ideas for **Characters** as 3–6 short bullet points. Bullets only.",
    "scenario":   "Reframe the student's ideas for **Scenario** as 3–6 short bullet points. Bullets only.",
    "conflict":   "Reframe the student's ideas for **Conflict** as 3–6 short bullet points. Bullets only.",
}


def _init_outline_state():
    ss = st.session_state
    ss.setdefault("outline_stage", "characters")
    ss.setdefault("outline_started", {"characters": False, "scenario": False, "conflict": False})
    ss.setdefault("outline_done", {"characters": False, "scenario": False, "conflict": False})
    ss.setdefault("outline_summary", {"characters": "", "scenario": "", "conflict": ""})
    # Chat index where each item started (to validate latest user turn for that item)
    ss.setdefault("outline_start_idx", {
        "characters": len(ss.get("chat_history", [])),
        "scenario": 0,
        "conflict": 0
    })
    ss.setdefault("outline_feedback", "")


def _kickoff_once(item: str):
    """Send the one-time hidden kickoff and remember where this section started."""
    ss = st.session_state
    if not ss["outline_started"][item]:
        send_hidden(KICKOFF_HIDDEN[item])  # hidden instruction (no UI bubble)
        ss["outline_started"][item] = True
        ss["outline_start_idx"][item] = len(ss.get("chat_history", []))


def _latest_user_since(item: str) -> str:
    """Return the most recent user message since this item started."""
    ss = st.session_state
    start = ss["outline_start_idx"].get(item, 0)
    latest = ""
    for i, m in enumerate(ss.get("chat_history", [])):
        if i >= start and m.get("role") == "user":
            latest = m.get("parts", "")
    return latest


def _complete_item(item: str, label: str):
    ss = st.session_state
    user_text = _latest_user_since(item)
    if looks_gibberish(user_text):
        ss["outline_feedback"] = f"Please provide a clearer idea for **{label}** before completing."
        return

    bullets = consolidate_outline_item(CONS_PROMPT[item])
    ss["outline_summary"][item] = bullets
    ss["outline_done"][item] = True
    ss["outline_feedback"] = f"Great — **{label}** saved. You can move on."

    # Advance stage
    if item == "characters":
        ss["outline_stage"] = "scenario"
    elif item == "scenario":
        ss["outline_stage"] = "conflict"
    else:
        ss["outline_stage"] = "done"


def _summary_block():
    ss = st.session_state
    with st.expander("🗒️ Outline Summary", expanded=True):
        for key, label in [("characters", "Characters"), ("scenario", "Scenario"), ("conflict", "Conflict")]:
            done = ss["outline_done"].get(key, False)
            head = f"**{label}** {'✅' if done else '•'}"
            st.markdown(head)
            text = ss["outline_summary"].get(key, "").strip()
            if text:
                st.markdown(text)
            else:
                st.caption("No summary yet.")


def _workbench(item: str, label: str, input_key: str, gate_msg: str = ""):
    ss = st.session_state

    # Gate by sequence
    if gate_msg:
        if (item == "scenario" and not ss["outline_done"]["characters"]) or \
           (item == "conflict" and not ss["outline_done"]["scenario"]):
            lock_card(gate_msg)
            return

    # One-time hidden kickoff to steer the assistant
    _kickoff_once(item)

    # Visible task for the student (hard-coded)
    st.subheader(f"{'👤' if item=='characters' else '🗺️' if item=='scenario' else '⚡'} {label}")
    st.info(KICKOFFS[item])

    # Chat area (input below messages)
    render_chat_area(input_key=input_key)

    # Complete / Reconsolidate
    btn_label = f"✅ Complete {label}" if not ss['outline_done'][item] else f"🔄 Re-consolidate {label}"
    if st.button(btn_label, use_container_width=True, key=f"btn_{item}"):
        _complete_item(item, label)

    # Feedback
    fb = ss.get("outline_feedback", "")
    if fb:
        if ss["outline_done"][item]:
            st.success(fb)
        else:
            st.error(fb)


def render():
    require_unlocked_for_outline()
    _init_outline_state()

    st.header("💭 Outline")
    st.write("Define your characters, setting, and the central problem. Ask for nudges any time.")

    # Section A: Summary (top)
    _summary_block()
    st.divider()

    # Section B: Workbench (sequential)
    _workbench("characters", "Characters", "outline_characters_input")
    _workbench("scenario", "Scenario", "outline_scenario_input",
               gate_msg="Complete **Characters** first to unlock Scenario.")
    _workbench("conflict", "Conflict", "outline_conflict_input",
               gate_msg="Complete **Scenario** first to unlock Conflict.")

    if st.session_state.get("outline_stage") == "done":
        st.info("Outline complete. You can proceed to **📝 Synopsis** when ready.")
