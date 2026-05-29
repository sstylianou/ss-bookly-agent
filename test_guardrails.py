"""
Unit tests for BooklyAgent tool implementations.

These exercise the Python logic directly — no Claude API calls, no HTTP requests.
Run with:  pytest test_guardrails.py -v
"""
import pytest
from unittest.mock import MagicMock
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from agent import BooklyAgent


def make_agent():
    """Return a BooklyAgent wired to a minimal fresh session (no real API client needed)."""
    session = {
        "messages": [],
        "subscription_stage": None,
        "subscription_books_selected": [],
        "subscription_pending": False,
    }
    agent = BooklyAgent.__new__(BooklyAgent)
    agent.client = MagicMock()
    agent.session_state = session
    return agent, session


# ── Guardrail 3 — identity verification (get_order_status) ───────────────

class TestGetOrderStatus:
    def test_unknown_order_returns_not_found(self):
        agent, _ = make_agent()
        result = agent._get_order_status("BK-9999", "alex@example.com")
        assert "ORDER_NOT_FOUND" in result

    def test_wrong_email_is_denied(self):
        agent, _ = make_agent()
        result = agent._get_order_status("BK-1042", "hacker@evil.com")
        assert "IDENTITY_VERIFICATION_FAILED" in result

    def test_wrong_email_leaks_no_order_data(self):
        """Guardrail 3: no partial data on mismatch."""
        agent, _ = make_agent()
        result = agent._get_order_status("BK-1042", "hacker@evil.com")
        assert "Great Gatsby" not in result
        assert "TRK-" not in result

    def test_correct_credentials_return_order(self):
        agent, _ = make_agent()
        result = agent._get_order_status("BK-1042", "alex@example.com")
        assert "IDENTITY VERIFIED" in result
        assert "BK-1042" in result

    def test_subscription_flag_fires_for_frequent_buyer(self):
        agent, session = make_agent()
        agent._get_order_status("BK-0988", "alex@example.com")
        assert session["subscription_pending"] is True

    def test_recent_shipped_order_is_return_eligible(self):
        agent, _ = make_agent()
        result = agent._get_order_status("BK-1042", "alex@example.com")
        assert "Eligible" in result

    def test_processing_order_is_not_return_eligible(self):
        agent, _ = make_agent()
        result = agent._get_order_status("BK-2055", "alex@example.com")
        assert "processing" in result.lower()

    def test_expired_order_is_not_return_eligible(self):
        agent, _ = make_agent()
        result = agent._get_order_status("BK-3011", "alex@example.com")
        assert "Ineligible" in result or "expired" in result.lower()


# ── Guardrail 3 — identity re-verification + policy enforcement (initiate_return) ──

class TestInitiateReturn:
    def test_unknown_order(self):
        agent, _ = make_agent()
        result = agent._initiate_return("BK-9999", "IT-001", "wrong item", "alex@example.com")
        assert "ORDER_NOT_FOUND" in result

    def test_wrong_email_blocked(self):
        agent, _ = make_agent()
        result = agent._initiate_return("BK-1042", "IT-001", "changed mind", "hacker@evil.com")
        assert "IDENTITY_VERIFICATION_FAILED" in result

    def test_unknown_item_id(self):
        agent, _ = make_agent()
        result = agent._initiate_return("BK-1042", "IT-999", "wrong item", "alex@example.com")
        assert "ITEM_NOT_FOUND" in result

    def test_expired_return_window_blocked_in_code(self):
        """Policy enforced in code — prompt cannot override this."""
        agent, _ = make_agent()
        result = agent._initiate_return("BK-3011", "IT-004", "changed mind", "alex@example.com")
        assert "RETURN_INELIGIBLE" in result

    def test_processing_order_blocked_in_code(self):
        """Can't return an unshipped order."""
        agent, _ = make_agent()
        result = agent._initiate_return("BK-2055", "IT-002", "changed mind", "alex@example.com")
        assert "RETURN_INELIGIBLE" in result
        assert "processing" in result.lower()

    def test_successful_return_within_window(self):
        agent, _ = make_agent()
        result = agent._initiate_return("BK-1042", "IT-001", "already have a copy", "alex@example.com")
        assert "RETURN INITIATED SUCCESSFULLY" in result
        assert "RET-" in result


# ── Subscription offer ────────────────────────────────────────────────────

class TestPresentSubscriptionOffer:
    def test_sets_stage_to_offer(self):
        agent, session = make_agent()
        agent._present_subscription_offer()
        assert session["subscription_stage"] == "offer"

    def test_clears_pending_flag(self):
        agent, session = make_agent()
        session["subscription_pending"] = True
        agent._present_subscription_offer()
        assert session["subscription_pending"] is False

    def test_returns_confirmation_string(self):
        agent, _ = make_agent()
        result = agent._present_subscription_offer()
        assert "SUBSCRIPTION_OFFER_DISPLAYED" in result


# ── Escalation ────────────────────────────────────────────────────────────

class TestEscalateToHuman:
    def test_creates_ticket(self):
        agent, _ = make_agent()
        result = agent._escalate_to_human("Waiting 3 weeks", "Customer has been waiting…")
        assert "ESCALATION TICKET CREATED" in result
        assert "TKT-" in result

    def test_ticket_ids_are_unique(self):
        agent, _ = make_agent()
        r1 = agent._escalate_to_human("reason", "summary")
        r2 = agent._escalate_to_human("reason", "summary")
        t1 = next(w for w in r1.split() if w.startswith("TKT-")).rstrip()
        t2 = next(w for w in r2.split() if w.startswith("TKT-")).rstrip()
        assert t1 != t2
