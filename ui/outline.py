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

# ---------- One-time hidden nudges for the assistant (ground in rules.txt + Key Pieces) ----------
KICKOFF_HIDDEN = {
    "characters": (
        "We are now beginning the *Characters* stage of an educational story. "
        "Ground all guidance in the background knowledge and teaching guidelines from rules.txt "
        "(creativity strategies, narrative writing moves, possibility thinking, science centrality). "
        "Also use the Key Pieces brief (educational level, scientific concept, genre, setting, goals). "
        "Drive possibility thinking with short, encouraging nudges. Ask ONE focused question at a time. "
        "Do not re-ask the form; build on the student's last message."
    ),
    "scenario": (
        "We are now beginning the *Scenario* stage. "
        "Ground all guidance in rules.txt (creativity scaffolds, narrative craft, age-appropriateness, "
        "keeping science central) and in the Key Pieces brief. "
        "Help the student define world, time, and key places; encourage realistic constraints/resources "
        "that make the science necessary (e.g., equipment limits, safety, context). "
        "Ask ONE focused question at a time. Keep replies concise and supportive."
    ),
    "conflict": (
        "We are now beginning the *Conflict* stage. "
        "Ground all guidance in rules.txt (creativity strategies, possibility thinking, narrative creativity) "
        "and in the Key Pieces brief. "
        "Guide toward an inner or external conflict that drives the characters to resolve the problem. "
        "Focus on clarifying the core science-grounded problem without spoilers. "
        "Ask ONE focused question at a time, briefly."
    ),
}

# ---------- Consolidation (short lines only, no new ideas) ----------
CONS_PROMPT = {
    "characters": "Reframe the student's ideas for **Characters** as 2–4 short lines that summarize the characters. Do not invent new ideas.",
    "scenario":   "Reframe the student's ideas for **Scenario** as 2–4 short lines that summarize the scenario. Do not invent new ideas.",
    "conflict":   "Reframe the student's ideas for **Conflict** as 2–4 short lines that summarize the conflict. Do not invent new ideas.",
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

    # Basic sanity: don't accept gibberish or empty
    if looks_gibberish(user_text):
        ss["outline_feedback"] = f"Please provide a clearer idea for **{label}** before completing."
        return

    # Consolidate; if model returns empty, we keep a minimal fallback in the helper
    bullets = consolidate_outline_item(CONS_PROMPT[item]).strip()
    if not bullets:
        bullets = f"- {user_text.strip()}"

    ss["outline_summary"][item] = bullets
    ss["outline_done"][item] = True
    ss["outline_feedback"] = f"Great — **{label}** saved. You can move on."

    # Advance stage (Characters → Scenario → Conflict → done)
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

    # Visual wrapper so each section is clearly separated
    with st.container(border=True):
        st.subheader(f"{'👤' if item=='characters' else '🗺️' if item=='scenario' else '⚡'} {label}")
        st.info(KICKOFFS[item])

        # 🔼 Button first → keeps chat input at the very bottom of the page
        btn_label = f"✅ Complete {label}" if not ss['outline_done'][item] else f"🔄 Re-consolidate {label}"
        if st.button(btn_label, use_container_width=True, key=f"btn_{item}"):
            _complete_item(item, label)

        # Feedback (shows immediately after click)
        fb = ss.get("outline_feedback", "")
        if fb:
            (st.success if ss["outline_done"][item] else st.error)(fb)

        # 🔽 Chat area last → st.chat_input() will render at page bottom
        render_chat_area(input_key=input_key)


def render():
    require_unlocked_for_outline()
    _init_outline_state()

    st.header("💭 Outline")
    st.write("Define your characters, setting, and the central problem. Ask for nudges any time.")

    # Two-column layout: summary (narrow) | workbench (wide)
    colL, colR = st.columns([1, 2.2], vertical_alignment="top")

    # Left: collapsible outline summary
    with colL:
        _summary_block()

    # Right: only the current stage workbench
    with colR:
        stage = st.session_state.get("outline_stage", "characters")

        if stage == "characters":
            _workbench("characters", "Characters", "outline_characters_input")

        elif stage == "scenario":
            # show a small green reminder that Characters was saved
            if st.session_state["outline_done"].get("characters"):
                st.success("Characters completed. You can refine in chat or continue anytime.")
            _workbench("scenario", "Scenario", "outline_scenario_input",
                       gate_msg="Complete **Characters** first to unlock Scenario.")

        elif stage == "conflict":
            if st.session_state["outline_done"].get("scenario"):
                st.success("Scenario completed. You can refine in chat or continue anytime.")
            _workbench("conflict", "Conflict", "outline_conflict_input",
                       gate_msg="Complete **Scenario** first to unlock Conflict.")

        else:  # stage == "done"
            st.success("🎉 Outline complete! You can proceed to **📝 Synopsis** when ready.")
