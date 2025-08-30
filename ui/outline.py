# === BEGIN FILE: ui/outline.py ===
import streamlit as st
from ui.common import require_unlocked_for_outline, looks_gibberish, lock_card

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

# ---------- One-time hidden nudges for the assistant (ground in rules + Key Pieces) ----------
KICKOFF_HIDDEN = {
    "characters": (
        "We are now beginning the *Characters* stage of an educational story. "
        "Ground all guidance in the background knowledge and teaching guidelines from rules.txt "
        "(creativity strategies, narrative moves, possibility thinking, science centrality), "
        "and in the Key Pieces brief (level, concept, genre, setting, goals). "
        "Ask ONE focused question at a time. Keep replies short and encouraging. Do not re-ask the form."
    ),
    "scenario": (
        "We are now beginning the *Scenario* stage. "
        "Ground all guidance in rules.txt and the Key Pieces brief. "
        "Help the student define world, time, and key places; encourage realistic constraints/resources "
        "that keep the science central. Ask ONE focused question at a time. Be concise and supportive."
    ),
    "conflict": (
        "We are now beginning the *Conflict* stage. "
        "Ground guidance in rules.txt and the Key Pieces brief. "
        "Guide toward a clear, age-appropriate core problem or tension (outer or inner) with a science link. "
        "Ask ONE focused question at a time, briefly. Avoid spoilers."
    ),
}

# ---------- Consolidation prompts (2–4 lines, no new ideas) ----------
CONS_PROMPT = {
    "characters": "Reframe the student's ideas for Characters as 2–4 short lines. Do not invent new ideas.",
    "scenario":   "Reframe the student's ideas for Scenario as 2–4 short lines. Do not invent new ideas.",
    "conflict":   "Reframe the student's ideas for Conflict as 2–4 short lines. Do not invent new ideas.",
}


# ========== Local helpers (tab-specific) ==========
def _ensure_outline_state():
    ss = st.session_state
    ss.setdefault("outline_stage", "characters")  # characters -> scenario -> conflict -> done
    ss.setdefault("outline_started", {"characters": False, "scenario": False, "conflict": False})
    ss.setdefault("outline_done", {"characters": False, "scenario": False, "conflict": False})
    ss.setdefault("outline_summary", {"characters": "", "scenario": "", "conflict": ""})
    ss.setdefault("outline_start_idx", {
        "characters": len(ss.get("chat_history", [])),
        "scenario": 0,
        "conflict": 0
    })
    ss.setdefault("outline_feedback", "")


def _send_hidden_once(item: str):
    """Send a one-time hidden kickoff message to the assistant (not shown in UI)."""
    ss = st.session_state
    if ss["outline_started"][item]:
        return
    try:
        # We don't echo this into chat_history, so it's invisible to the student UI.
        ss["chat"].send_message(
            f"(Hidden instruction for assistant. Acknowledge internally only.)\n{KICKOFF_HIDDEN[item]}"
        )
    except Exception:
        pass
    ss["outline_started"][item] = True
    ss["outline_start_idx"][item] = len(ss.get("chat_history", []))


def _latest_user_since(item: str) -> str:
    """Most recent user message since this item started (for consolidation)."""
    ss = st.session_state
    start = ss["outline_start_idx"].get(item, 0)
    latest = ""
    for i, m in enumerate(ss.get("chat_history", [])):
        if i >= start and m.get("role") == "user":
            latest = m.get("parts", "")
    return latest


def _consolidate_to_lines(item: str, user_text: str) -> str:
    """Ask the model for a 2–4 line reframe of the student's latest ideas (no new ideas)."""
    from google import generativeai as genai
    ss = st.session_state
    model_name = ss.get("model_name", "gemini-2.0-flash")
    # Light system context to stay aligned with rules, while keeping it a one-off call
    rules = (ss.get("rules_text", "") or "") + "\n\nBe concise, accurate, and do not add new ideas."
    model = genai.GenerativeModel(model_name, system_instruction=rules)
    prompt = (
        f"{CONS_PROMPT[item]}\n\n"
        f"Student's most recent ideas:\n\"\"\"\n{user_text}\n\"\"\"\n\n"
        "Return 2–4 short lines. No bullets."
    )
    try:
        return (model.generate_content(prompt).text or "").strip()
    except Exception as e:
        return f"_Could not generate summary: {e}_"


def _render_messages_then_input(input_key: str):
    """Replay message bubbles, then show chat input at the bottom (natural chat layout)."""
    ss = st.session_state
    # 1) Messages
    for msg in ss.get("chat_history", []):
        avatar = "👩🏼‍💻" if msg["role"] == "user" else ss.get("assistant_avatar", "assets/Avatar.png")
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["parts"])

    # 2) Input
    user_prompt = st.chat_input("Message InspiraBot…", key=input_key)
    if not user_prompt:
        return

    # Save & echo user turn
    ss["chat_history"].append({"role": "user", "parts": user_prompt})
    with st.chat_message("user", avatar="👩🏼‍💻"):
        st.markdown(user_prompt)

    # Stream assistant reply
    with st.chat_message("assistant", avatar=ss.get("assistant_avatar", "assets/Avatar.png")):
        placeholder = st.empty()
        parts = []
        try:
            for chunk in ss["chat"].send_message_stream(user_prompt):
                if getattr(chunk, "text", None):
                    parts.append(chunk.text)
                    placeholder.markdown("".join(parts) + "▌")
            full = "".join(parts) if parts else ""
            placeholder.markdown(full or "_No response text received._")
        except Exception as e:
            full = f"❌ Error from Gemini (streaming): {e}"
            placeholder.error(full)
    ss["chat_history"].append({"role": "assistant", "parts": full})


def _complete_item(item: str, label: str):
    ss = st.session_state
    user_text = _latest_user_since(item)
    if looks_gibberish(user_text):
        ss["outline_feedback"] = f"Please provide a clearer idea for **{label}** before completing."
        return

    lines = _consolidate_to_lines(item, user_text)
    ss["outline_summary"][item] = lines
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
    with st.expander("🗒️ Outline Summary", expanded=False):  # collapsed by default
        for key, label in [("characters", "Characters"), ("scenario", "Scenario"), ("conflict", "Conflict")]:
            done = ss["outline_done"].get(key, False)
            head = f"**{label}** {'✅' if done else '•'}"
            st.markdown(head)
            text = ss["outline_summary"].get(key, "").strip()
            if text:
                st.markdown(text)
            else:
                st.caption("No summary yet.")


def _render_stage(item: str, label: str, input_key: str):
    """Render the active stage only."""
    _send_hidden_once(item)
    st.subheader(f"{'👤' if item=='characters' else '🗺️' if item=='scenario' else '⚡'} {label}")
    st.info(KICKOFFS[item])

    _render_messages_then_input(input_key=input_key)

    btn_label = f"✅ Complete {label}"
    if st.button(btn_label, use_container_width=True, key=f"btn_{item}"):
        _complete_item(item, label)

    fb = st.session_state.get("outline_feedback", "")
    if fb:
        if st.session_state["outline_done"][item]:
            st.success(fb)
        else:
            st.error(fb)


# ========== Public render ==========
def render():
    require_unlocked_for_outline()
    _ensure_outline_state()

    st.header("💭 Outline")
    st.write("Define your characters, setting, and the central problem. Ask for nudges any time.")

    # Summary always available at top (collapsed by default)
    _summary_block()
    st.divider()

    stage = st.session_state.get("outline_stage", "characters")
    if stage == "characters":
        _render_stage("characters", "Characters", "outline_input")
    elif stage == "scenario":
        _render_stage("scenario", "Scenario", "outline_input")
    elif stage == "conflict":
        _render_stage("conflict", "Conflict", "outline_input")
    else:
        st.info("Outline complete. You can proceed to **📝 Synopsis** when ready.")
# === END FILE: ui/outline.py ===
