# Bookly Support Agent — Bex

A conversational AI support agent for **Bookly**, a fictional online bookstore.
Built with Python, the Anthropic Claude API, and Streamlit.

> **This is a take-home assignment prototype.** Code is intentionally direct and readable over production-hardened.

---

## Quick Start

### 1. Clone & install

```bash
git clone <this-repo>
cd ss-bookly-agent
pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 3. Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Demo Scenarios

Use the sidebar credentials to trigger each scenario:

| Scenario | Order ID | Email | What it demos |
|---|---|---|---|
| Order status lookup | `BK-1042` | `alice@example.com` | Multi-turn auth + tool use |
| Return request | `BK-1042` | `alice@example.com` | Full multi-turn flow + tool action |
| Processing order | `BK-2055` | `bob@example.com` | Return eligibility check |
| Expired return window | `BK-3011` | `carol@example.com` | Policy enforcement in code |
| Wrong email on any order | any ID + wrong email | — | **Guardrail 3**: unauthorised access blocked |
| Off-topic question | *"Can you help me write a cover letter?"* | — | **Guardrail 1**: scope enforcement |
| Policy FAQ | *"What's your return policy?"* | — | Static context, no tool needed |
| Escalation | *"I'm very unhappy, no one is helping me"* | — | Human handoff flow |

---

## Architecture

```
app.py          → Streamlit UI (renders chat, sidebar, demo credentials)
agent.py        → BooklyAgent class: API calls, tool loop, response handling
config.py       → Identity, static policies, guardrails, examples, tool schemas
mock_data.py    → Simulated orders database (replaces real OMS in production)
```

### How a request flows

```
User types message
  → app.py appends to conversation history
  → agent.py calls Claude (model + system + full conversation + tools)
  → Claude responds with text OR a tool_use block
      → if tool_use: agent.py executes mock function
                   → injects tool_result into conversation
                   → calls Claude again for synthesis
      → if text: display response
```

No frameworks. No LangChain. No agent orchestration platforms.
One class, one API, one loop.

---

## Three Guardrails (the talk track)

| # | Guardrail | Enforced in prompt | Enforced in code |
|---|---|---|---|
| 1 | **Bookly scope only** — Bex won't answer off-topic questions | ✅ Explicit instruction + 2 examples | — |
| 2 | **Grounded responses only** — no invented policies or details | ✅ Anti-hallucination instruction | ✅ Tools are the only source of dynamic data |
| 3 | **No unauthorised data access** — email verified before any order data is returned | ✅ Must collect order ID + email first | ✅ `get_order_status` and `initiate_return` check email server-side before returning anything |

Guardrail 3 is the most important one for enterprise demos: **the prompt can be persuaded, but the code cannot.**

---

## Key Technical Decisions

### 1. Narrow, explicit tool schemas
Each tool requires specific named fields. Claude can't call `get_order_status` without both `order_id` and `customer_email` — the API will reject it.
- **Trade-off**: More tools = more schema to maintain
- **Why it's worth it**: Eliminates ambiguous tool calls; `required` fields enforce data collection before action

### 2. Full conversation history over RAG
Every Claude call receives the complete conversation history. No vector store, no retrieval step.
- **Trade-off**: Token cost grows linearly with conversation length
- **Why it's worth it**: Support conversations are short (<20 turns); zero retrieval errors; Claude has perfect context for follow-ups

### 3. Prompt-driven clarification, not rule-based routing
Claude decides when to ask for clarification vs. proceed, guided by the system prompt and few-shot examples.
- **Trade-off**: Less deterministic than a hard intent classifier
- **Why it's worth it**: Avoids brittle routing logic; handles ambiguous phrasing naturally; easier to update via prompt than code

---

## What I'd do differently in production

1. **Authentication layer** — verify customer identity against a real session/token before the conversation starts, not mid-chat
2. **RAG for policy docs** — replace static context with a vector search over a full policy knowledge base (scales to hundreds of pages)
3. **Streaming responses** — Anthropic streaming API for perceived latency improvement in the UI
4. **Evaluation harness** — systematic test cases for each guardrail and conversation flow, run on every prompt change
5. **Human handoff integration** — `escalate_to_human` POSTs to Zendesk/Intercom instead of returning a mock ticket
6. **Structured logging** — capture every tool call + result for audit trails and GDPR compliance

---

## File Structure

```
ss-bookly-agent/
├── app.py            # Streamlit UI
├── agent.py          # BooklyAgent class + tool loop
├── config.py         # Identity, guardrails, static context, tool schemas
├── mock_data.py      # Simulated orders database
├── requirements.txt
├── .env.example
└── README.md
```
