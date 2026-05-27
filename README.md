# Bookly Support Agent — Bex

A conversational AI support agent for **Bookly**, a fictional online bookstore.
Built with Python, the Anthropic Claude API, and Streamlit — no agent frameworks, no orchestration platforms.

> **Take-home assignment prototype.** Code is intentionally direct and readable over production-hardened.

🌐 **Live demo:** [ss-bookly-agent.streamlit.app](https://ss-bookly-agent.streamlit.app)

---

## Quick Start

### 1. Clone & install
```bash
git clone https://github.com/sstylianou/ss-bookly-agent
cd ss-bookly-agent
pip install -r requirements.txt
```

### 2. Set your API key
```bash
cp .env.example .env
# Add your Anthropic API key to .env
```

### 3. Run
```bash
streamlit run app.py
# Opens at http://localhost:8501
```

---

## Demo Credentials

All orders belong to one customer — no email-switching mid-demo.

| Order ID | Email | Status | Key scenario |
|---|---|---|---|
| `BK-1042` | `alex@example.com` | Shipped | Order lookup, return request |
| `BK-2055` | `alex@example.com` | Processing | Return blocked (not yet shipped) |
| `BK-3011` | `alex@example.com` | Delivered | Return blocked (outside 30-day window) |
| `BK-0988` | `alex@example.com` | Delivered | 4th order — triggers subscription upsell |

> All four orders are available whenever you look up any order for `alex@example.com` — the subscription flag fires automatically.

---

## Use Cases

### 1. Order Status Lookup
**What to say:** *"Where is my order?"*

Bex asks for the order ID and email before looking anything up. Once provided, it calls `get_order_status` and returns status, estimated delivery, tracking number, and return eligibility.

- Demonstrates: **multi-turn identity collection → tool use**
- Try with: `BK-1042` / `alex@example.com`

---

### 2. Return Request
**What to say:** *"I'd like to return a book"*

Bex collects order ID and email, looks up the order, then asks which item to return and the reason — all before calling `initiate_return`. On success, returns a prepaid label confirmation and refund timeline.

If the customer already provided their email earlier in the conversation (e.g. during an order lookup), Bex reuses it and skips asking again.

- Demonstrates: **multi-step multi-turn flow → tool action; context retention across turns**
- Try with: `BK-1042` / `alex@example.com` — within the 30-day window ✅
- **Tip for demo:** Look up the order first, then say *"actually I'd like to return it"* — Bex will go straight to asking which item, not the email again

---

### 3. Return Blocked — Order Still Processing
**What to say:** *"I want to return my order"*

Bex looks up the order and finds it hasn't shipped yet. Politely explains returns can only be started once the item has been dispatched.

- Demonstrates: **eligibility check enforced in code, not just prompt**
- Try with: `BK-2055` / `alex@example.com`

---

### 4. Return Blocked — Outside 30-Day Window
**What to say:** *"I want to return a book I ordered a while back"*

Bex looks up the order, calculates days since purchase (37 days), and declines the return. Offers to escalate to a human agent for a manager exception.

- Demonstrates: **policy enforcement in code** — the 30-day check runs server-side regardless of how the request is phrased
- Try with: `BK-3011` / `alex@example.com`

---

### 5. Policy FAQ — No Tool Required
**What to say:** *"What is your return policy?"* / *"How long does shipping take?"* / *"How do I reset my password?"*

Bex answers directly from the static context in its prompt — no tool call needed. If a policy detail isn't in the context, Bex says so rather than guessing.

- Demonstrates: **grounded responses (Guardrail 2)** — Bex only states what it knows

---

### 6. Escalation to Human Agent
**What to say:** *"I've been waiting 3 weeks and nobody is helping me!"*

Bex recognises frustration, validates the customer's experience, and calls `escalate_to_human` — generating a ticket ID, summary, and expected response time.

- Demonstrates: **empathetic tone + structured handoff**
- Also triggered when: identity verification fails, issue is out of scope, or an exception to policy is needed

---

### 7. Guardrail 1 — Scope Enforcement
**What to say:** *"Can you help me write a cover letter?"* / *"What's the weather like in London?"*

Bex declines politely and redirects back to Bookly topics.

- Demonstrates: **Guardrail 1** — Bex is scoped exclusively to Bookly support

---

### 8. Guardrail 3 — Unauthorised Data Access Blocked
**What to say:** Ask for any order with a wrong email, e.g. `BK-1042` + `wrong@email.com`

Bex calls the tool, which verifies the email server-side and returns `IDENTITY_VERIFICATION_FAILED`. No order data is returned. Bex apologises and offers escalation.

- Demonstrates: **Guardrail 3 enforced in code** — the prompt cannot be talked out of this check

---

### 9. Subscription Upsell
**What to say:** Look up any order for `alex@example.com`

The tool sees 4 orders in 45 days and flags `⭐ SUBSCRIPTION UPSELL OPPORTUNITY`. After resolving the customer's issue, Bex naturally mentions the Bookly Subscription Plan: **£20/month, 2 curated books, managed in the Bookly app**. If the customer isn't interested, Bex drops it immediately.

- Demonstrates: **contextual upsell driven by tool data, not hardcoded prompts**
- The threshold (>3 orders / 45 days) and the flag live in `agent.py` — the prompt only defines how to act on it

---

### 10. NPS & Conversation Closure
**What to say:** *"Thanks, that's everything I needed!"*

Bex first asks: *"Is there anything else I can help you with today?"* — confirming the customer is done before requesting feedback. Once confirmed, asks for an NPS score (0–10).

| Score | What happens |
|---|---|
| **0–6** | Bex thanks the customer, then asks up to 2 targeted follow-up questions |
| **7–10** | Bex skips follow-up and closes with a warm thank you |

Bex always ends the conversation with a personalised thank you by name.

- Demonstrates: **structured conversation lifecycle** — support → upsell → feedback → close

---

## Architecture

```
app.py          → Streamlit UI: chat interface, demo sidebar, reset button
agent.py        → BooklyAgent: Anthropic API calls, tool loop, tool implementations
config.py       → Identity, static policies, guardrails, NPS rules, upsell rules, few-shot examples, tool schemas
mock_data.py    → Simulated orders database (4 orders, all for alex@example.com)
```

### Request flow

```
User types message
  → app.py appends to conversation history
  → agent.py calls Claude with (system prompt + full conversation history + tool schemas)
  → Claude returns text OR a tool_use block
      → text: store in history, display to user
      → tool_use: agent.py executes mock function
                  → injects tool_result into conversation history
                  → calls Claude again for synthesis
                  → repeat if Claude chains another tool call
```

No frameworks. No LangChain. No agent orchestration platforms. One class, one API, one loop.

---

## Guardrails

| # | Guardrail | In prompt | In code |
|---|---|---|---|
| 1 | **Bookly scope only** — off-topic questions redirected | ✅ Instruction + 2 examples | — |
| 2 | **Grounded responses** — no invented policies or details | ✅ Anti-hallucination instruction | ✅ Tools are the only source of dynamic data |
| 3 | **No unauthorised data access** — identity verified before any order data returned | ✅ Collect order ID + email before any lookup; reuse email already given — never ask twice | ✅ `get_order_status` and `initiate_return` verify email server-side; mismatch = hard denial |

> **Key point for demos:** Guardrail 3 lives in both the prompt *and* the code. The prompt can be persuaded — the code cannot.

---

## Key Technical Decisions

### 1. Narrow, explicit tool schemas
Each tool has named required fields. Claude cannot call `get_order_status` without both `order_id` and `customer_email` — the Anthropic API enforces it at the schema level.
- **Trade-off:** More schemas to maintain as tools grow
- **Why it's worth it:** Eliminates ambiguous calls; forces identity collection before action; makes tool behaviour predictable

### 2. Full conversation history over RAG
Every Claude call gets the full conversation history. No vector store, no retrieval step.
- **Trade-off:** Token cost grows with conversation length
- **Why it's worth it:** Support conversations are short (<20 turns); no retrieval errors; Claude has complete context for nuanced follow-ups. RAG makes sense at scale — not here.

### 3. Prompt-driven clarification, not rule-based routing
Claude decides when to ask for clarification vs. proceed, guided by the system prompt and few-shot examples — not an explicit intent classifier.
- **Trade-off:** Slightly less deterministic than hard routing logic
- **Why it's worth it:** Handles ambiguous phrasing naturally; no brittle decision trees; update behaviour by editing the prompt, not the code

### 4. Upsell and NPS logic separated by concern
The subscription threshold and NPS scoring rules are defined in `agent.py` and `config.py` respectively — not tangled together in the prompt. The tool result carries the flag; the prompt defines what to do with it.
- **Trade-off:** Slightly more surface area across files
- **Why it's worth it:** Each concern is independently testable and adjustable — change the threshold in one line without touching the conversational instructions

---

## What I'd do differently in production

1. **Authentication before the chat starts** — verify the customer via session token or OTP before the conversation, not mid-chat via email
2. **RAG for policy docs** — replace the static context string with vector search over a full knowledge base (scales to hundreds of policy pages without bloating every prompt)
3. **Streaming responses** — use the Anthropic streaming API so responses appear progressively; critical for latency perception on longer answers
4. **Evaluation harness** — systematic test cases for every guardrail, flow, and edge case; run automatically on every prompt change before deploying
5. **Real human handoff integration** — `escalate_to_human` would POST to Zendesk / Intercom / Freshdesk with full conversation context, not return a mock ticket
6. **Structured logging + audit trail** — every tool call, tool result, and model response logged for GDPR compliance, debugging, and CSAT analysis
7. **Sliding context window** — for very long sessions, summarise older turns rather than passing unbounded history

---

## File Structure

```
ss-bookly-agent/
├── app.py            # Streamlit UI
├── agent.py          # BooklyAgent class, tool loop, tool implementations
├── config.py         # Identity, static context, guardrails, NPS, upsell, tool schemas
├── mock_data.py      # 4 simulated orders (all for alex@example.com)
├── requirements.txt
├── .env.example      # API key template
└── README.md
```
