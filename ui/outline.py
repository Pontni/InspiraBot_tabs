# === BEGIN FILE: ui/outline.py ===
import streamlit as st
from ui.common import (
    require_unlocked_for_outline,
    render_chat_area,
    looks_gibberish,
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

# ---------- Hidden one-time nudges (grounded in rules + brief) ----------
KICKOFF_HIDDEN = {
    "characters": (
        "We are now beginning the *Characters* stage of an educational story. "
        "Ground guidance in rules.txt (creativity strategies, narrative moves, possibility thinking, science centrality) "
        "and in the Key Pieces brief (level, concept, genre, setting, goals). "
        "Ask ONE focused question at a time. Do not re-ask the form."
    ),
    "scenario": (
        "We are now beginning the *Scenario* stage. Ground in rules.txt and Key Pieces. "
        "Help define world/time/places and constraints that keep the science necessary. "
        "Ask ONE focused question at a time; keep replies concise and encouraging."
    ),
    "conflict": (
        "We are now beginning the *Conflict* stage. Ground in rules.txt and Key Pieces. "
        "Guide toward a clear, age-appropriate central problem (outer or inner) that drives inquiry. "
        "Ask ONE focused question at a time; no spoilers."
    ),
}

# ---------- Local helpers (kept in this tab) ----------
def _send_hidden(text: str) -> None:
    chat = st.session_state.get("chat")
    if not chat or not text:
        return
    try:
        _ = chat.send_message(text)  # hidden—no bubbles
    except Exception:
        pass

def _consolidate(instruction: str) -> str:
    """Ask the model to reframe into 2–4 short lines; never block if empty."""
    chat = st.session_state.get("chat")
    if not chat:
        return ""
    try:
        resp = chat.send_message(instruction)
        txt = (getattr(resp, "text", "") or "").strip()
        if txt:
            return txt
    except Exception:
        pass
    # Safe fallback: last user turn
    for m in reversed(st.session_state.get("chat_history", [])):
        if m.get("role") == "user":
            return f"- {m.get('parts','').strip()}"
    return ""

# 2–4 lines, no new ideas
CONS_PROMPT = {
    "characters": "Reframe the student's ideas for **Characters** as 2–4 short lines. Do not invent new ideas.",
    "scenario":   "Reframe the student's ideas for **Scenario** as 2–4 short lines. Do not invent new ideas.",
    "conflict":   "Reframe the student's ideas for **Conflict** as 2–4 short lines. Do not invent new ideas.",
}

def _init_state():
    ss = st.session_state
    ss.setdefault("outline_stage", "characters")  # characters → scenario → conflict → done
    ss.setdefault("outline_started", {"characters": False, "scenario": False, "conflict": False})
    ss.setdefault("outline_done", {"characters": False, "scenario": False, "conflict": False})
    ss.setdefault("outline_summary", {"characters": "", "scenario": "", "conflict": ""})
    ss.setdefault("outline_start_idx", {
        "characters": len(ss.get("chat_history", [])),
        "scenario": 0,
        "conflict": 0,
    })
    ss.setdefault("outline_feedback", "")

def _kickoff_once(item: str):
    ss = st.session_state
    if not ss["outline_started"][item]:
        _send_hidden(KICKOFF_HIDDEN[item])
        ss["outline_started"][item] = True
        ss["outline_start_idx"][item] = len(ss.get("chat_history", []))

def _latest_user_since(item: str) -> str:
    ss = st.session_state
    start = ss["outline_start_idx"].get(item, 0)
    latest = ""
    for i, m in enumerate(ss.get("chat_history", [])):
        if i >= start and m.get("role") == "user":
            latest = m.get("parts", "")
    return latest.strip()

def _complete(item: str, label: str):
    ss = st.session_state
    user_text = _latest_user_since(item)
    if looks_gibberish(user_text):
        ss["outline_feedback"] = f"Please provide a clearer idea for **{label}** before completing."
        return

    bullets = _consolidate(CONS_PROMPT[item]).strip() or f"- {user_text}"
    ss["outline_summary"][item] = bullets
    ss["outline_done"][item] = True
    ss["outline_feedback"] = f"Great — **{label}** saved. You can move on."

    # advance
    ss["outline_stage"] = (
        "scenario" if item == "characters" else
        "conflict" if item == "scenario" else
        "done"
    )

def _summary():
    with st.expander("🗒️ Outline Summary", expanded=True):
        for key, label in [("characters","Characters"),("scenario","Scenario"),("conflict","Conflict")]:
            done = st.session_state["outline_done"].get(key, False)
            st.markdown(f"**{label}** {'✅' if done else '•'}")
            text = st.session_state["outline_summary"].get(key, "").strip()
            if text:
                st.markdown(text)
            else:
                st.caption("No summary yet.")

def _stage_ui(item: str, label: str, input_key: str):
    # one-time steer
    _kickoff_once(item)

    st.subheader(f"{'👤' if item=='characters' else '🗺️' if item=='scenario' else '⚡'} {label}")
    st.info(KICKOFFS[item])

    # chat (input above messages – old feel)
    render_chat_area(input_key=input_key)

    # complete button (below chat – old app behavior)
    btn_label = f"✅ Complete {label}" if not st.session_state['outline_done'][item] else f"🔄 Re-consolidate {label}"
    if st.button(btn_label, use_container_width=True, key=f"btn_{item}"):
        _complete(item, label)

    fb = st.session_state.get("outline_feedback", "")
    if fb:
        (st.success if st.session_state["outline_done"][item] else st.error)(fb)

def render():
    require_unlocked_for_outline()
    _init_state()

    st.header("💭 Outline")
    st.write("Define your characters, setting, and the central problem. Ask for nudges any time.")

    _summary()
    st.divider()

    stage = st.session_state.get("outline_stage", "characters")
    if stage == "characters":
        _stage_ui("characters", "Characters", "outline_char_input")
    elif stage == "scenario":
        _stage_ui("scenario", "Scenario", "outline_scn_input")
    elif stage == "conflict":
        _stage_ui("conflict", "Conflict", "outline_cfl_input")
    else:
        st.success("🎉 Outline complete! You can proceed to **📝 Synopsis** when ready.")
# === END FILE ===
