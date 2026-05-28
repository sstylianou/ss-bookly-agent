# Bookly Support Agent — Bex

A conversational support agent for **Bookly**, a fictional online bookstore. Python, the Anthropic Claude API, and Streamlit. No agent frameworks, no orchestration, no LangChain.

> Take-home prototype. Built for readability and demo clarity over production hardening.

**Live demo:** [ss-bookly-agent.streamlit.app](https://ss-bookly-agent.streamlit.app)

---

## Quick start

```bash
git clone https://github.com/sstylianou/ss-bookly-agent
cd ss-bookly-agent
pip install -r requirements.txt

cp .env.example .env        # then paste your Anthropic key
streamlit run app.py        # http://localhost:8501
```

---

## Demo credentials

All four orders belong to one customer so the demo never has to switch email.

| Order ID  | Status     | What it shows                                              |
|-----------|------------|------------------------------------------------------------|
| `BK-1042` | Shipped    | Order lookup and a return that goes through                |
| `BK-2055` | Processing | Return blocked because the order hasn't shipped yet        |
| `BK-3011` | Delivered  | Return blocked because the 30-day window has expired       |
| `BK-0988` | Delivered  | 4th order in 45 days — triggers the subscription offer     |

Email for all of them: `alex@example.com`.

---

## What Bex can do

### 1. Look up an order
Say *"Where is my order?"*. Bex asks for the order ID and email, then calls `get_order_status` and replies with status, ETA, tracking, and return eligibility. Try `BK-1042`.

### 2. Start a return
Say *"I want to return a book"*. Bex collects the order details, verifies identity, then asks which item and why before calling `initiate_return`. Returns inside the 30-day window succeed; everything else is blocked in code, not just in the prompt.

If you look up an order first and then ask to return it, Bex reuses the email you already gave — no double prompt.

### 3. Block returns that shouldn't go through
- `BK-2055` is still processing → Bex declines and explains why.
- `BK-3011` is 38 days old → Bex declines and offers to raise a manager-exception ticket.

Both checks live in `agent.py`, not in the prompt. The model can't be talked out of them.

### 4. Answer policy questions without making things up
Ask *"What's your return policy?"* or *"How do I reset my password?"*. Bex reads from the static policy block in `config.py`. If something isn't there, it says so rather than guess (Guardrail 2).

### 5. Escalate without friction
If you're frustrated, Bex offers to raise a priority ticket on your behalf rather than leading with a phone number. Say yes and it calls `escalate_to_human`, returns a ticket ID, and tells you when to expect a reply. Say no and only then does it share the support email and phone line.

### 6. Refuse off-topic requests
Try *"Help me write a cover letter"*. Bex politely declines and redirects (Guardrail 1).

### 7. Block unauthorised access
Try looking up `BK-1042` with the wrong email. The tool verifies server-side and returns `IDENTITY_VERIFICATION_FAILED` — no order data leaks. Bex apologises and offers to escalate (Guardrail 3).

### 8. Run the subscription offer
Look up any order for `alex@example.com`. The tool flags `⭐ SUBSCRIPTION UPSELL OPPORTUNITY` because there are 4 orders in 45 days. After Bex resolves your issue and you confirm there's nothing else, it calls `present_subscription_offer`, which renders an inline 3-stage flow:

1. **Offer card** — plan summary, *"Yes, sign me up"* or *"Maybe later"*.
2. **Payment confirmation** — masked Visa card on file, confirm or cancel.
3. **Book carousel** — 6 personalised titles, pick exactly 2, then confirm.

Everything happens in chat. No app redirect.

### 9. Close the conversation properly
Say *"Thanks, that's all"*. Bex first checks there's nothing else, then asks for an NPS score:

| Score | Behaviour                                       |
|-------|-------------------------------------------------|
| 0–6   | Bex thanks you, asks up to 2 follow-up questions, then closes |
| 7–10  | Bex skips follow-ups and closes warmly          |

Either way it ends by thanking you by name.

---

## Architecture

```
app.py         Streamlit UI — chat, sidebar, subscription cards
agent.py       BooklyAgent — Anthropic API call, tool loop, tool implementations
config.py      Identity, policies, guardrails, escalation, NPS, subscription, examples, tool schemas
mock_data.py   4 simulated orders, the book catalogue, and the masked payment record
```

### Request flow

```
User types a message
  → app.py appends it to st.session_state.messages
  → agent.py calls Claude with (system prompt + history + tool schemas)
  → Claude returns text OR a tool_use block
      text     → store and render
      tool_use → execute the mock function
                 → inject the result into history
                 → call Claude again to synthesise
                 → recurse if it chains another tool
```

One class, one API, one loop.

### Tools

| Tool                          | What it does                                                              |
|-------------------------------|---------------------------------------------------------------------------|
| `get_order_status`            | Verify identity and return order details. Adds the ⭐ flag when eligible.  |
| `initiate_return`             | Re-verify identity, check eligibility in code, return a confirmation.     |
| `present_subscription_offer`  | Set `subscription_stage="offer"` so the UI renders the 3-stage flow.      |
| `escalate_to_human`           | Generate a ticket ID and a structured handoff message.                    |

---

## Guardrails

| # | Guardrail                          | Prompt | Code |
|---|------------------------------------|--------|------|
| 1 | Bookly scope only                  | ✅     | —    |
| 2 | No invented policies or details    | ✅     | ✅ Tools are the only source of dynamic data |
| 3 | No unauthorised data access        | ✅ Identity collected once, reused session-wide | ✅ Email verified server-side on every tool call |

Guardrail 3 lives in both places on purpose. The prompt can be talked around. The code can't.

---

## How the subscription trigger stays reliable

Haiku is fast but can lose track of the ⭐ flag over a long conversation. Rather than rely on the prompt alone, the agent flips a `session_state.subscription_pending` flag in Python when the flag fires. On every subsequent Claude call, the system prompt picks up an extra `⚠️ ACTIVE SUBSCRIPTION REMINDER` block from `config.SUBSCRIPTION_PENDING_REMINDER` until the offer has been presented. Once `present_subscription_offer` runs, the flag clears and the reminder disappears.

The trigger logic itself stays declarative — code computes it, the model decides when to fire — but the reminder ensures the model can't overlook it.

---

## Design decisions worth calling out

**Narrow tool schemas with required fields.** Claude can't call `get_order_status` without both an order ID and an email; the API rejects malformed calls. That keeps identity collection honest.

**Full history over RAG.** Support conversations are short. Passing everything every turn costs tokens but eliminates retrieval errors and keeps Claude's context perfect for nuanced follow-ups.

**Prompt-driven clarification, not intent routing.** Bex decides whether to clarify or act based on the system prompt and a handful of few-shot examples. No brittle decision tree to update when policy changes.

**Upsell and NPS as separate concerns.** Subscription threshold in `agent.py`. NPS rules in `config.py`. Each is independently testable, and editing one doesn't risk breaking the other.

---

## What I'd do differently in production

1. **Authenticate before the chat starts** — session token or OTP, not mid-conversation email exchange.
2. **RAG for policy docs** — replace the static context string with vector search once the knowledge base outgrows a single prompt.
3. **Streaming responses** — use the Anthropic streaming API so longer answers feel immediate.
4. **Evaluation harness** — automated regression tests covering every guardrail, every flow, every edge case before any prompt change ships.
5. **Real human handoff** — `escalate_to_human` POSTs to Zendesk / Intercom / Freshdesk with full context, not a mock ticket.
6. **Audit logging** — every tool call and response logged for GDPR, debugging, and CSAT analysis.
7. **Sliding context window** — for very long sessions, summarise older turns instead of carrying the whole transcript.

---

## File layout

```
ss-bookly-agent/
├── app.py           Streamlit UI
├── agent.py         BooklyAgent class, tool loop, tool implementations
├── config.py        Identity, policies, guardrails, NPS, subscription, examples, tool schemas
├── mock_data.py     4 orders for alex@example.com, book catalogue, masked card record
├── requirements.txt
├── .env.example
└── README.md
```
