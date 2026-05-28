"""
mock_data.py — Simulated Bookly backend data

In a production system, this would be replaced by a database query
(PostgreSQL, DynamoDB), an internal orders API, or an OMS integration.

Order timing (relative to demo date 2026-05-30):
  BK-1042: ordered  8 days ago  → within  30-day return window
  BK-2055: ordered  3 days ago  → still processing, not yet shipped
  BK-3011: ordered 38 days ago  → outside 30-day return window (edge case)
  BK-0988: ordered 18 days ago  → 4th order in 45 days → triggers subscription
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
        "order_date": "2026-05-22",
        "estimated_delivery": "2026-05-30",
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
        "order_date": "2026-05-27",
        "estimated_delivery": "2026-06-03",
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
        "order_date": "2026-04-22",       # 38 days ago — outside return window
        "estimated_delivery": "2026-04-27",
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
        "order_date": "2026-05-12",       # 18 days ago — 4th order in 45 days → triggers subscription upsell
        "estimated_delivery": "2026-05-17",
        "tracking_number": "TRK-7751002",
        "shipping_method": "Standard Delivery"
    }
}

# Bookly return policy constants
RETURN_WINDOW_DAYS = 30

# Mock book catalogue for the subscription selection carousel
BOOKS_CATALOG = [
    {"id": "B001", "title": "Atomic Habits",                        "author": "James Clear",         "genre": "Self-Development", "emoji": "🧠"},
    {"id": "B002", "title": "The Midnight Library",                 "author": "Matt Haig",           "genre": "Fiction",          "emoji": "🌙"},
    {"id": "B003", "title": "Thinking, Fast and Slow",              "author": "Daniel Kahneman",     "genre": "Psychology",       "emoji": "💡"},
    {"id": "B004", "title": "Normal People",                        "author": "Sally Rooney",        "genre": "Fiction",          "emoji": "❤️"},
    {"id": "B005", "title": "A Short History of Nearly Everything", "author": "Bill Bryson",         "genre": "Science",          "emoji": "🔬"},
    {"id": "B006", "title": "Project Hail Mary",                    "author": "Andy Weir",           "genre": "Sci-Fi",           "emoji": "🚀"},
]

# Mock payment method on file (displayed masked — last 4 digits only)
PAYMENT_ON_FILE = {
    "type":    "Visa",
    "last4":   "4242",
    "expires": "03/28",
}
