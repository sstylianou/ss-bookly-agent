"""
app.py — Bookly Concierge UI

Clean Streamlit chat interface with an interactive subscription sign-up flow
(offer card → payment confirmation → book carousel) that fires after issue
resolution and before NPS, triggered by the present_subscription_offer tool.
"""

import streamlit as st
from agent import BooklyAgent
from config import TASK_SPECIFIC_INSTRUCTIONS
from mock_data import BOOKS_CATALOG, PAYMENT_ON_FILE


# ── Session initialisation ────────────────────────────────────────────────

def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "user",      "content": TASK_SPECIFIC_INSTRUCTIONS},
            {"role": "assistant", "content": "Understood. I'm Bex, ready to look after Bookly customers."},
        ]
    if "subscription_stage" not in st.session_state:
        st.session_state.subscription_stage = None          # offer | payment | books
    if "subscription_books_selected" not in st.session_state:
        st.session_state.subscription_books_selected = []   # list of book IDs
    if "subscription_pending" not in st.session_state:
        st.session_state.subscription_pending = False       # True once ⭐ flag fires


# ── Sidebar ───────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("# 📚 Bookly")
        st.caption("Concierge Service")
        st.divider()

        st.subheader("🧪 Demo Credentials")
        st.caption("All orders share one email: **alex@example.com**")

        with st.expander("✅ Shipped order (BK-1042)", expanded=True):
            st.code("Order ID:  BK-1042\nEmail:     alex@example.com", language=None)
            st.caption("Status: Shipped • Within return window")

        with st.expander("⏳ Processing order (BK-2055)"):
            st.code("Order ID:  BK-2055\nEmail:     alex@example.com", language=None)
            st.caption("Status: Processing • Return not yet available")

        with st.expander("❌ Expired return window (BK-3011)"):
            st.code("Order ID:  BK-3011\nEmail:     alex@example.com", language=None)
            st.caption("Status: Delivered • 37 days old — return window closed")

        with st.expander("📦 Past orders (BK-0988)"):
            st.code("Order ID:  BK-0988\nEmail:     alex@example.com", language=None)
            st.caption("Status: Delivered • 4th order in 45 days — triggers subscription offer")

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

**Guardrails**
- *Can you help me write an email?*
  → Scope guardrail (Guardrail 1)
- *Wrong email on any order*
  → Unauthorised access block (Guardrail 3)
- *BK-3011 return attempt*
  → Policy enforcement in code

**Subscription**
- Look up any order → issue resolved
  → Bex presents the subscription offer
  → book carousel to choose first 2 titles

**Closing the conversation**
- *Thanks, that's all I needed!*
  → Bex confirms no more questions
  → NPS score request
- Score ≤6 → up to 2 follow-up questions
- Score 7+ → straight to thank you
""")

        st.divider()
        if st.button("🔄 Reset conversation", use_container_width=True):
            st.session_state.clear()
            st.rerun()


# ── Chat history ──────────────────────────────────────────────────────────

def render_chat_history():
    """Render conversation — skip seed messages, tool blocks, and [SYSTEM:] injections."""
    for message in st.session_state.messages[2:]:
        content = message["content"]
        if isinstance(content, str) and not content.startswith("[SYSTEM:"):
            avatar = "👤" if message["role"] == "user" else "📚"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(content)


# ── Subscription UI ───────────────────────────────────────────────────────

def render_subscription_offer_card():
    """Stage: offer — present the plan with accept / maybe-later buttons."""
    st.markdown("""
<div style="
    background: #131B2E;
    border: 1px solid #6C63FF;
    border-radius: 12px;
    padding: 24px 28px;
    margin: 12px 0;
">
    <p style="color:#A59FFF; font-size:11px; text-transform:uppercase;
              letter-spacing:2px; margin:0 0 6px">✦ Bex recommends</p>
    <h3 style="color:white; margin:0 0 10px">📚 Bookly Subscription</h3>
    <p style="color:#8B9AB8; margin:0 0 20px; font-size:15px">
        You've been ordering regularly — our subscription plan is built for readers like you.
    </p>
    <div style="display:flex; gap:32px; margin-bottom:0">
        <div>
            <div style="color:white; font-weight:700; font-size:22px">2</div>
            <div style="color:#8B9AB8; font-size:12px">books / month</div>
        </div>
        <div>
            <div style="color:white; font-weight:700; font-size:22px">£20</div>
            <div style="color:#8B9AB8; font-size:12px">per month</div>
        </div>
        <div>
            <div style="color:white; font-weight:700; font-size:22px">🎯</div>
            <div style="color:#8B9AB8; font-size:12px">personalised</div>
        </div>
        <div>
            <div style="color:white; font-weight:700; font-size:22px">✕</div>
            <div style="color:#8B9AB8; font-size:12px">cancel anytime</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

    col1, col2, _ = st.columns([2, 2, 3])
    with col1:
        if st.button("✨ Yes, sign me up!", use_container_width=True, type="primary"):
            st.session_state.subscription_stage = "payment"
            st.rerun()
    with col2:
        if st.button("Maybe later", use_container_width=True):
            st.session_state.messages.append({
                "role": "user",
                "content": "[SYSTEM: Customer has seen and declined the Bookly Subscription offer. "
                           "Do not offer it again. Proceed with conversation closure and NPS.]"
            })
            st.session_state.subscription_stage = None
            st.session_state.pending_agent_input = "Thanks, but I'll skip the subscription for now."
            st.rerun()


def render_payment_confirmation():
    """Stage: payment — show masked card details and confirm button."""
    st.markdown("""
<div style="
    background: #131B2E;
    border: 1px solid #6C63FF;
    border-radius: 12px;
    padding: 24px 28px;
    margin: 12px 0;
">
    <p style="color:#A59FFF; font-size:11px; text-transform:uppercase;
              letter-spacing:2px; margin:0 0 6px">💳 Confirm payment</p>
    <h3 style="color:white; margin:0 0 16px">One last step</h3>
    <p style="color:#8B9AB8; margin:0 0 8px; font-size:14px">Payment method on file:</p>
    <div style="
        background:#0B0F1A; border-radius:8px; padding:14px 18px;
        display:inline-block; margin-bottom:20px;
    ">
        <span style="color:white; font-size:16px; font-weight:600; letter-spacing:2px">
            {type} &nbsp;••••&nbsp;••••&nbsp;••••&nbsp;{last4}
        </span>
        <span style="color:#8B9AB8; font-size:13px; margin-left:16px">
            Exp {expires}
        </span>
    </div>
    <p style="color:#8B9AB8; margin:0; font-size:13px">
        £20.00 will be charged today · renews monthly · cancel anytime
    </p>
</div>
""".format(**PAYMENT_ON_FILE), unsafe_allow_html=True)

    col1, col2, _ = st.columns([2.5, 1.5, 3])
    with col1:
        if st.button("✓ Confirm & subscribe", use_container_width=True, type="primary"):
            st.session_state.subscription_stage = "books"
            st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.subscription_stage = "offer"
            st.rerun()


def render_book_selection():
    """Stage: books — 6-book carousel, pick exactly 2, then confirm."""
    selected = st.session_state.subscription_books_selected

    st.markdown("""
<div style="
    background: #131B2E;
    border: 1px solid #6C63FF;
    border-radius: 12px;
    padding: 24px 28px 16px;
    margin: 12px 0;
">
    <p style="color:#A59FFF; font-size:11px; text-transform:uppercase;
              letter-spacing:2px; margin:0 0 6px">📖 Choose your first two books</p>
    <p style="color:#8B9AB8; margin:0; font-size:14px">
        Pick any two from your personalised shortlist — based on your reading history.
    </p>
</div>
""", unsafe_allow_html=True)

    cols = st.columns(3)
    for i, book in enumerate(BOOKS_CATALOG):
        is_selected  = book["id"] in selected
        max_reached  = len(selected) >= 2
        with cols[i % 3]:
            st.markdown(
                f"{'✓ ' if is_selected else ''}{book['emoji']} **{book['title']}**  \n"
                f"*{book['author']}* · `{book['genre']}`"
            )
            btn_label    = "✓ Selected" if is_selected else "Select"
            btn_disabled = max_reached and not is_selected
            if st.button(
                btn_label,
                key=f"book_{book['id']}",
                disabled=btn_disabled,
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                if is_selected:
                    st.session_state.subscription_books_selected.remove(book["id"])
                else:
                    st.session_state.subscription_books_selected.append(book["id"])
                st.rerun()
            st.markdown("")

    if len(selected) == 2:
        names = [b["title"] for b in BOOKS_CATALOG if b["id"] in selected]
        st.success(f"**Your selection:** {names[0]} and {names[1]}")
        if st.button("Confirm my choices →", type="primary"):
            book_str = " and ".join(names)
            st.session_state.pending_agent_input = (
                f"I'd love to go ahead! I've chosen {book_str} as my first two books."
            )
            st.session_state.subscription_stage          = None
            st.session_state.subscription_books_selected = []
            st.rerun()


def render_subscription_ui():
    """Route to the correct subscription stage UI."""
    stage = st.session_state.get("subscription_stage")
    if stage == "offer":
        render_subscription_offer_card()
    elif stage == "payment":
        render_payment_confirmation()
    elif stage == "books":
        render_book_selection()


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Bookly Concierge — Bex",
        page_icon="📚",
        layout="centered",
        initial_sidebar_state="expanded"
    )

    init_session()
    render_sidebar()

    # Process any pending message from subscription UI button interactions
    if "pending_agent_input" in st.session_state:
        pending = st.session_state.pop("pending_agent_input")
        agent   = BooklyAgent(st.session_state)
        agent.process_user_input(pending)

    # Header
    col1, col2 = st.columns([1, 6])
    with col1:
        st.markdown("## 📚")
    with col2:
        st.markdown("## Bookly Concierge")
        st.caption("Powered by Bex · Your personal book concierge")

    st.divider()

    render_chat_history()

    # Normal chat input
    if user_input := st.chat_input("How can Bex help you today?"):
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
        agent = BooklyAgent(st.session_state)
        with st.chat_message("assistant", avatar="📚"):
            with st.spinner("Bex is with you..."):
                response = agent.process_user_input(user_input)
            st.markdown(response)

    # Subscription UI renders after chat content so it appears inline
    render_subscription_ui()


if __name__ == "__main__":
    main()
