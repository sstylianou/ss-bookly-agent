"""
agent.py — Bookly AI Agent core

BooklyAgent class orchestrates:
  1. Conversation history management
  2. Direct Anthropic API calls (no frameworks)
  3. Tool use loop (execute → inject result → get final response)
  4. Guardrail enforcement at the tool level (auth, return eligibility)

Design decision: full conversation history passed on every turn.
Trade-off: token cost grows with conversation length.
Worth it for support use cases (typically <20 turns) — no retrieval errors,
Claude has perfect context. In production: sliding window or RAG for policy docs.
"""

import uuid
import anthropic
from datetime import datetime, date, timedelta

from config import IDENTITY, TASK_SPECIFIC_INSTRUCTIONS, TOOLS, MODEL
from mock_data import ORDERS, RETURN_WINDOW_DAYS

SUBSCRIPTION_ORDER_THRESHOLD = 3   # more than this many orders in the window triggers the upsell
SUBSCRIPTION_WINDOW_DAYS = 45


class BooklyAgent:
    def __init__(self, session_state):
        self.client = anthropic.Anthropic()
        self.session_state = session_state

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process_user_input(self, user_input: str) -> str:
        """Append user message, call Claude, handle response (including tool loops)."""
        self.session_state.messages.append({"role": "user", "content": user_input})
        response = self._call_claude(self.session_state.messages)
        return self._handle_response(response)

    # ------------------------------------------------------------------
    # Claude API call
    # ------------------------------------------------------------------

    def _call_claude(self, messages: list) -> anthropic.types.Message | dict:
        system = IDENTITY
        if (self.session_state.get("subscription_pending")
                and not self.session_state.get("subscription_stage")):
            system += (
                "\n\n⚠️ ACTIVE SUBSCRIPTION REMINDER — YOU MUST DO THIS NEXT: "
                "The ⭐ SUBSCRIPTION UPSELL OPPORTUNITY was triggered earlier in this session. "
                "The customer has more than 3 orders in 45 days. "
                "When the customer confirms they have no more questions, your VERY NEXT action "
                "is to call the `present_subscription_offer` tool — before any NPS question. "
                "Do NOT skip this. Do NOT describe the plan in text."
            )
        try:
            return self.client.messages.create(
                model=MODEL,
                system=system,
                max_tokens=1024,
                messages=messages,
                tools=TOOLS,
            )
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Response handling (recursive for tool use loops)
    # ------------------------------------------------------------------

    def _handle_response(self, response) -> str:
        if isinstance(response, dict) and "error" in response:
            return f"⚠️ Something went wrong: {response['error']}. Please try again or contact support@bookly.com."

        # --- Tool use: execute all tools, inject results, recurse ---
        if response.stop_reason == "tool_use":
            # Persist assistant's full response (includes tool_use content blocks)
            self.session_state.messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Execute every tool call in this response
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = self._execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Inject tool results as a user turn (Anthropic API pattern)
            self.session_state.messages.append({
                "role": "user",
                "content": tool_results
            })

            # Get Claude's synthesis of the tool result
            follow_up = self._call_claude(self.session_state.messages)
            return self._handle_response(follow_up)  # handles chained tool calls too

        # --- Normal text response ---
        elif response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    # Store as plain string — Streamlit displays this; tool blocks are skipped in UI
                    self.session_state.messages.append({
                        "role": "assistant",
                        "content": block.text
                    })
                    return block.text

        return "I'm sorry, I wasn't able to process that. Please try again."

    # ------------------------------------------------------------------
    # Tool dispatcher
    # ------------------------------------------------------------------

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Route tool calls to the appropriate mock implementation."""
        if tool_name == "get_order_status":
            return self._get_order_status(
                tool_input["order_id"],
                tool_input["customer_email"]
            )
        elif tool_name == "initiate_return":
            return self._initiate_return(
                tool_input["order_id"],
                tool_input["item_id"],
                tool_input["reason"],
                tool_input["customer_email"]
            )
        elif tool_name == "present_subscription_offer":
            return self._present_subscription_offer()
        elif tool_name == "escalate_to_human":
            return self._escalate_to_human(
                tool_input["reason"],
                tool_input["conversation_summary"]
            )
        else:
            return f"ERROR: Unknown tool '{tool_name}' — this tool is not registered."

    # ------------------------------------------------------------------
    # Tool implementations (mocked — simulates real integrations)
    # ------------------------------------------------------------------

    def _get_order_status(self, order_id: str, customer_email: str) -> str:
        """
        Look up an order.

        GUARDRAIL 3 — Unauthorised Data Access:
        Email is verified against the order record BEFORE any data is returned.
        A mismatch returns a hard denial — no partial data is ever leaked.
        """
        order = ORDERS.get(order_id.strip().upper())

        if not order:
            return (
                f"ORDER_NOT_FOUND: No order with ID '{order_id}' exists in our system. "
                "Please double-check the order ID and try again."
            )

        # Guardrail 3: identity check
        if order["customer_email"].lower() != customer_email.strip().lower():
            return (
                "IDENTITY_VERIFICATION_FAILED: The email address provided does not match "
                "the account associated with this order. No data has been returned. "
                "Please offer to escalate to a human agent."
            )

        # Calculate return eligibility
        order_date = datetime.strptime(order["order_date"], "%Y-%m-%d").date()
        days_since_order = (date.today() - order_date).days
        within_window = days_since_order <= RETURN_WINDOW_DAYS
        already_processing = order["status"] == "processing"

        if within_window and not already_processing:
            return_status = f"✅ Eligible (order is {days_since_order} days old — within the 30-day window)"
        elif already_processing:
            return_status = "⏳ Not yet eligible — order is still processing (must be shipped first)"
        else:
            return_status = (
                f"❌ Ineligible — order is {days_since_order} days old "
                f"(30-day return window expired {days_since_order - RETURN_WINDOW_DAYS} days ago)"
            )

        tracking = (
            f"Tracking number: {order['tracking_number']}"
            if order["tracking_number"]
            else "Tracking number: Not yet available (will be issued once shipped)"
        )

        items_str = "\n".join(
            f"  • {item['title']} by {item['author']} — £{item['price']:.2f} (Item ID: {item['id']})"
            for item in order["items"]
        )

        # Check subscription eligibility: count this customer's orders in the last 45 days
        cutoff = date.today() - timedelta(days=SUBSCRIPTION_WINDOW_DAYS)
        recent_order_count = sum(
            1 for o in ORDERS.values()
            if o["customer_email"].lower() == customer_email.strip().lower()
            and datetime.strptime(o["order_date"], "%Y-%m-%d").date() >= cutoff
        )
        subscription_note = ""
        if recent_order_count > SUBSCRIPTION_ORDER_THRESHOLD:
            self.session_state.subscription_pending = True
            subscription_note = (
                f"\n⭐ SUBSCRIPTION UPSELL OPPORTUNITY: This customer has placed "
                f"{recent_order_count} orders in the last {SUBSCRIPTION_WINDOW_DAYS} days. "
                "Once their issue is fully resolved AND they confirm they have no more questions, "
                "call the present_subscription_offer tool BEFORE asking for NPS feedback."
            )

        return f"""IDENTITY VERIFIED ✓ — Order data retrieved successfully.

Order ID:           {order['order_id']}
Customer:           {order['customer_name']}
Status:             {order['status'].upper()}
Order date:         {order['order_date']}
Estimated delivery: {order['estimated_delivery']}
Shipping method:    {order['shipping_method']}
{tracking}

Items ordered:
{items_str}

Return eligibility: {return_status}{subscription_note}
"""

    def _initiate_return(
        self, order_id: str, item_id: str, reason: str, customer_email: str
    ) -> str:
        """
        Process a return request.

        GUARDRAIL 3 — Identity re-verified before any action is taken.
        Return eligibility (30-day window, shipped status) is enforced in code,
        not just in the prompt — the prompt cannot be talked out of it.
        """
        order = ORDERS.get(order_id.strip().upper())

        if not order:
            return f"ORDER_NOT_FOUND: No order with ID '{order_id}' found."

        # Guardrail 3: re-verify identity before taking any action
        if order["customer_email"].lower() != customer_email.strip().lower():
            return (
                "IDENTITY_VERIFICATION_FAILED: Email does not match this order. "
                "Return request blocked. Please escalate."
            )

        # Find the specific item
        item = next(
            (i for i in order["items"] if i["id"].upper() == item_id.strip().upper()),
            None
        )
        if not item:
            return (
                f"ITEM_NOT_FOUND: Item '{item_id}' was not found in order '{order_id}'. "
                f"Valid item IDs for this order: {[i['id'] for i in order['items']]}"
            )

        # Enforce return window in code (belt-and-suspenders with the prompt guardrail)
        order_date = datetime.strptime(order["order_date"], "%Y-%m-%d").date()
        days_since_order = (date.today() - order_date).days

        if days_since_order > RETURN_WINDOW_DAYS:
            return (
                f"RETURN_INELIGIBLE: This order is {days_since_order} days old. "
                f"The 30-day return window closed {days_since_order - RETURN_WINDOW_DAYS} days ago. "
                "Offer to escalate for a manager exception."
            )

        if order["status"] == "processing":
            return (
                "RETURN_INELIGIBLE: This order is still processing and hasn't shipped yet. "
                "Returns can only be initiated after the item has been shipped. "
                "Advise customer to wait for shipping confirmation."
            )

        # Generate return confirmation
        return_id = f"RET-{uuid.uuid4().hex[:6].upper()}"

        return f"""RETURN INITIATED SUCCESSFULLY ✓

Return ID:    {return_id}
Order:        {order_id}
Item:         {item['title']} by {item['author']} — £{item['price']:.2f}
Reason:       {reason}

Next steps for customer:
1. A prepaid Royal Mail return label has been emailed to {customer_email}
2. Pack the book securely in its original condition
3. Drop off at any Royal Mail location within 14 days
4. Refund of £{item['price']:.2f} will be processed within 5–7 business days of receipt

Note: Refund will be returned to the original payment method.
"""

    def _present_subscription_offer(self) -> str:
        """
        Trigger the interactive subscription sign-up UI in the Streamlit frontend.
        Sets subscription_stage so app.py renders the offer card immediately after this response.
        """
        self.session_state.subscription_stage = "offer"
        self.session_state.subscription_pending = False
        return (
            "SUBSCRIPTION_OFFER_DISPLAYED ✓ — The Bookly Subscription Plan offer has been "
            "presented to the customer with an interactive sign-up experience. "
            "Introduce it warmly and wait for the customer to interact with the UI."
        )

    def _escalate_to_human(self, reason: str, conversation_summary: str) -> str:
        """
        Create a support ticket for human agent handoff.

        In production: would POST to Zendesk / Intercom / Freshdesk API.
        Passing conversation_summary ensures the human agent has full context
        without needing to re-read the entire transcript.
        """
        ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"

        return f"""ESCALATION TICKET CREATED ✓

Ticket ID:  {ticket_id}
Reason:     {reason}
Summary:    {conversation_summary}

A human support agent has been notified and will respond within 2 business hours.
Confirmation will be sent to the customer's registered email address.
Support hours: Monday–Friday, 9 AM – 6 PM GMT
"""
