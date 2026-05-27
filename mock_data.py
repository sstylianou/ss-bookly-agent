"""
mock_data.py — Simulated Bookly backend data

In a production system, this would be replaced by:
  - A database query (PostgreSQL, DynamoDB, etc.)
  - An internal orders API
  - An OMS (Order Management System) integration

Dates are relative to today (2026-05-27):
  BK-1042: ordered 7 days ago  → within 30-day return window ✓
  BK-2055: ordered 2 days ago  → processing, not yet shipped ✓
  BK-3011: ordered 37 days ago → OUTSIDE 30-day return window ✗  (good demo edge case)
"""

ORDERS = {
    "BK-1042": {
        "order_id": "BK-1042",
        "customer_email": "alex@example.com",
        "customer_name": "Alex",
        "status": "shipped",
        "items": [
            {
                "id": "IT-001",
                "title": "The Great Gatsby",
                "author": "F. Scott Fitzgerald",
                "price": 12.99,
                "type": "physical"
            }
        ],
        "order_date": "2026-05-20",
        "estimated_delivery": "2026-05-28",
        "tracking_number": "TRK-9923344",
        "shipping_method": "Standard Delivery"
    },
    "BK-2055": {
        "order_id": "BK-2055",
        "customer_email": "alex@example.com",
        "customer_name": "Alex",
        "status": "processing",
        "items": [
            {
                "id": "IT-002",
                "title": "1984",
                "author": "George Orwell",
                "price": 9.99,
                "type": "physical"
            },
            {
                "id": "IT-003",
                "title": "Brave New World",
                "author": "Aldous Huxley",
                "price": 11.99,
                "type": "physical"
            }
        ],
        "order_date": "2026-05-25",
        "estimated_delivery": "2026-06-01",
        "tracking_number": None,
        "shipping_method": "Express Delivery"
    },
    "BK-3011": {
        "order_id": "BK-3011",
        "customer_email": "alex@example.com",
        "customer_name": "Alex",
        "status": "delivered",
        "items": [
            {
                "id": "IT-004",
                "title": "To Kill a Mockingbird",
                "author": "Harper Lee",
                "price": 10.99,
                "type": "physical"
            }
        ],
        "order_date": "2026-04-20",       # 37 days ago — outside return window
        "estimated_delivery": "2026-04-25",
        "tracking_number": "TRK-8812211",
        "shipping_method": "Standard Delivery"
    },
    "BK-0988": {
        "order_id": "BK-0988",
        "customer_email": "alex@example.com",
        "customer_name": "Alex",
        "status": "delivered",
        "items": [
            {
                "id": "IT-005",
                "title": "Sapiens: A Brief History of Humankind",
                "author": "Yuval Noah Harari",
                "price": 14.99,
                "type": "physical"
            }
        ],
        "order_date": "2026-05-10",       # 17 days ago — 4th order in 45 days → triggers subscription upsell
        "estimated_delivery": "2026-05-15",
        "tracking_number": "TRK-7751002",
        "shipping_method": "Standard Delivery"
    }
}

# Bookly return policy constants
RETURN_WINDOW_DAYS = 30
