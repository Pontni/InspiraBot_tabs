# === BEGIN FILE: ui/outline.py ===
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

# ---------- Hidden assistant nudges (ground in rules.txt + Key Pieces) ----------
KICKOFF_HIDDEN = {
    "characters": (
        "We are beginning the Characters stage of an educational story. "
        "Ground guidance in rules.txt (creativity strategies, narrative craft, possibility thinking, science centrality) "
        "and in the Key Pieces brief supplied earlier. "
        "Ask ONE focused question at a time. Be concise and encouraging."
    ),
    "scenario": (
        "We are beginning the Scenario stage. Ground guidance in rules.txt + Key Pieces. "
        "Help define world/time/key places and constraints that keep the science central. "
        "Ask ONE focused question at a time. Keep replies brief."
    ),
    "conflict": (
        "We are beginning the Conflict stage. Ground guidance in rules.txt + Key Pieces. "
        "Guide toward a clear central tension (outer or inner) that propels inquiry. "
        "Ask ONE focused question at a time; no spoilers."
    ),
}

# ---------- Consolidation prompts (2–4 plain lines, no bullets) ----------
CONS_PROMPT = {
    "characters": "Reframe the student's ideas for **Characters** as 2–4 short plain-text lines (no bullets). Do not invent new ideas.",
    "scenario":   "Reframe the student's ideas for **Scenario** as 2–4 short plain-text lines (no bullets). Do not invent new ideas.",
    "conflict":   "Reframe the student's ideas for **Conflict** as 2–4 short plain-text lines (no bullets). Do not invent new ideas.",
}

def _init_outline_state():
    ss = st.session_state
    ss.setdefault("outline_stage", "characters")  # characters -> scenario -> conflict -> done
    ss.setdefault("outline_started", {"characters": False, "scenario": False, "conflict": False})
    ss.setdefault("outline_done", {"characters": False, "scenario": False, "conflict": False})
    ss.setdefault("outline_summary", {"characters": "", "scenario": "", "conflict": ""})
    # Remember the index in chat_history where each stage started
    ss.setdefault("outline_start_idx", {
        "characters": len(ss.get("chat_history", [])),
        "scenario": 0,
        "conflict": 0
    })
    ss.setdefault("outline_feedback", "")

def _kickoff_once(item: str):
    """Hidden kickoff to steer assistant; record where this stage started."""
    ss = st.session_state
    if not ss["outline_started"][item]:
        send_hidden(KICKOFF_HIDDEN[item])
        ss["outline_started"][item] = True
        ss["outline_start_idx"][item] = len(ss.get("chat_history", []))

def _latest_user_since(item: str) -> str:
    """Most recent user message since the stage began."""
    ss = st.session_state
    start = ss["outline_start_idx"].get(item, 0)
    latest = ""
    for i, m in enumerate(ss.get("chat_history", [])):
        if i >= start and m.get("role") == "user":
            latest = m.get("parts", "")
    return latest

def _complete_item(item: str, label: str):
    """Validate, consolidate (2–4 lines), save, advance stage, then rerun."""
    ss = st.session_state
    user_text = _latest_user_since(item)
    if looks_gibberish(user_text):
        ss["outline_feedback"] = f"Please provide a clearer idea for **{label}** before completing."
        return

    summary = consolidate_outline_item(CONS_PROMPT[item])
    ss["outline_summary"][item] = summary
    ss["outline_done"][item] = True
    ss["outline_feedback"] = f"Great — **{label}** saved. You can move on."

    # Advance sequence
    if item == "characters":
        ss["outline_stage"] = "scenario"
    elif item == "scenario":
        ss["outline_stage"] = "conflict"
    else:
        ss["outline_stage"] = "done"

    st.rerun()

def _summary_block():
    ss = st.session_state
    with st.expander("🗒️ Outline Summary", expanded=False):  # collapsed by default
        for key, label in [("characters", "Characters"), ("scenario", "Scenario"), ("conflict", "Conflict")]:
            done = ss["outline_done"].get(key, False)
            st.markdown(f"**{label}** {'✅' if done else '•'}")
            text = ss["outline_summary"].get(key, "").strip()
            if text:
                st.markdown(text)
            else:
                st.caption("No summary yet.")

def _workbench(item: str, label: str, input_key: str):
    """Single-stage work area with kickoff, chat, and complete button."""
    _kickoff_once(item)

    st.subheader(f"{'👤' if item=='characters' else '🗺️' if item=='scenario' else '⚔️'} {label}")
    st.info(KICKOFFS[item])

    # Chat (history above, input below)
    render_chat_area(input_key=input_key)

    # Complete / reconsolidate
    btn_label = f"✅ Complete {label}"
    if st.button(btn_label, use_container_width=True, key=f"btn_{item}"):
        _complete_item(item, label)

    # Feedback after click
    fb = st.session_state.get("outline_feedback", "")
    if fb:
        # show success only if this stage is already marked done
        if st.session_state["outline_done"].get(item, False):
            st.success(fb)
        else:
            st.error(fb)

def render():
    require_unlocked_for_outline()
    _init_outline_state()

    st.header("💭 Outline")
    st.write("Define your characters, setting, and the central problem. Ask for nudges any time.")

    # Summary up top (collapsed by default)
    _summary_block()
    st.divider()

    stage = st.session_state.get("outline_stage", "characters")

    if stage == "characters":
        _workbench("characters", "Characters", "outline_characters_input")
    elif stage == "scenario":
        _workbench("scenario", "Scenario", "outline_scenario_input")
    elif stage == "conflict":
        _workbench("conflict", "Conflict", "outline_conflict_input")
    else:
        st.info("🎉 Outline complete. You can proceed to **📝 Synopsis** when ready.")
# === END FILE ===
