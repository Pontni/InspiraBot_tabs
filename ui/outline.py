from ui.common import require_unlocked_for_outline, render_chat_area

def render():
    st.header("💭 Outline")
    st.write("Define your characters, setting, and central problem. Ask for nudges any time.")
    require_unlocked_for_outline()
    render_chat_area(input_key="outline_chat_input")  # <-- unique key
