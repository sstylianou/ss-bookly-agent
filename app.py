"""
app.py — Bookly AI Agent Streamlit UI

Minimal, clean chat interface. The demo sidebar shows test credentials
so you can run scenarios without memorising order IDs.

Run:
    streamlit run app.py
"""

import streamlit as st
from agent import BooklyAgent
from config import TASK_SPECIFIC_INSTRUCTIONS


def init_session():
    """Initialise conversation history with injected context on first load."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            # First user turn injects all static context, guardrails, and examples.
            # This keeps the system prompt lean (identity/role only) while giving
            # Claude the full knowledge base it needs — following Anthropic's
            # recommended prompt structure.
            {"role": "user", "content": TASK_SPECIFIC_INSTRUCTIONS},
            {"role": "assistant", "content": "Understood. I'm Bex, ready to assist Bookly customers."},
        ]


def render_sidebar():
    with st.sidebar:
        st.image(
            "https://via.placeholder.com/200x60/1a1a2e/FFFFFF?text=📚+Bookly",
            use_container_width=True
        )
        st.divider()

        st.subheader("🧪 Demo Credentials")
        st.caption("Copy these to test each scenario")

        with st.expander("✅ Shipped order (BK-1042)", expanded=True):
            st.code("Order ID:  BK-1042\nEmail:     alice@example.com", language=None)
            st.caption("Status: Shipped • Within return window")

        with st.expander("⏳ Processing order (BK-2055)"):
            st.code("Order ID:  BK-2055\nEmail:     bob@example.com", language=None)
            st.caption("Status: Processing • Return not yet available")

        with st.expander("❌ Expired return window (BK-3011)"):
            st.code("Order ID:  BK-3011\nEmail:     carol@example.com", language=None)
            st.caption("Status: Delivered • 37 days old — return window closed")

        st.divider()
        st.subheader("💬 Suggested prompts")
        st.markdown("""
**Order & returns**
- *Where is my order?*
- *I want to return a book*

**Policy FAQ**
- *What is your return policy?*
- *How do I reset my password?*
- *How long does shipping take?*

**Guardrails demo**
- *Can you help me write an email?*
  → Scope guardrail (Guardrail 1)
- *Wrong email on BK-1042*
  → Unauthorised access block (Guardrail 3)
- *BK-3011 return attempt*
  → Policy enforcement in code (not just prompt)
""")

        st.divider()
        if st.button("🔄 Reset conversation", use_container_width=True):
            st.session_state.clear()
            st.rerun()


def render_chat_history():
    """Display conversation — skip seed messages and tool use/result blocks."""
    for message in st.session_state.messages[2:]:
        # Only render plain text content; skip tool_use/tool_result content blocks
        if isinstance(message["content"], str):
            avatar = "👤" if message["role"] == "user" else "📚"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])


def main():
    st.set_page_config(
        page_title="Bookly Support — Bex",
        page_icon="📚",
        layout="centered",
        initial_sidebar_state="expanded"
    )

    init_session()
    render_sidebar()

    # Header
    col1, col2 = st.columns([1, 6])
    with col1:
        st.markdown("## 📚")
    with col2:
        st.markdown("## Bookly Customer Support")
        st.caption("Powered by Bex · AI support assistant")

    st.divider()

    # Chat history
    render_chat_history()

    # Input
    if user_input := st.chat_input("How can Bex help you today?"):
        # Show user message immediately
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        # Generate and show Bex's response
        agent = BooklyAgent(st.session_state)
        with st.chat_message("assistant", avatar="📚"):
            with st.spinner("Bex is looking into that..."):
                response = agent.process_user_input(user_input)
            st.markdown(response)


if __name__ == "__main__":
    main()
