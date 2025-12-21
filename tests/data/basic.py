"""
Basic test data
"""

TEST_DATA: dict[str, list[dict]] = {
    "currencies": [
        {"code": "USD", "description": "United States Dollar"},
        {"code": "CNY", "description": "Chinese Yuan"},
        {"code": "CHF", "description": "Swiss Franc"},
    ],
    "categories": [
        {"name": "checking", "side": "asset"},
        {"name": "savings", "side": "asset"},
        {"name": "mortgage", "side": "liability"},
    ],
    "accounts": [
        {
            "id": 1,
            "name": "checking_1",
            "description": "checking account",
            "category": "checking",
            "currency": "USD",
            "status": "active",
        },
        {
            "id": 2,
            "name": "savings_2",
            "description": "savings account",
            "category": "savings",
            "currency": "USD",
            "status": "active",
        },
        {
            "id": 3,
            "name": "mortgage_3",
            "description": "primary home morgage",
            "category": "mortgage",
            "currency": "USD",
            "status": "active",
        },
    ],
    "balances": [
        {"account_id": 1, "month": "2024-01", "amount": 500},
        {"account_id": 1, "month": "2024-02", "amount": 520},
        {"account_id": 1, "month": "2024-03", "amount": 480},
        {"account_id": 2, "month": "2024-01", "amount": 1500},
        {"account_id": 2, "month": "2024-02", "amount": 1550},
        {"account_id": 2, "month": "2024-03", "amount": 1600},
        {"account_id": 3, "month": "2024-01", "amount": 2500},
        {"account_id": 3, "month": "2024-02", "amount": 2400},
        {"account_id": 3, "month": "2024-03", "amount": 2300},
    ],
    "exchange_rates": [
        {"currency": "CNY", "month": "2024-01", "rate": 0.71},
        {"currency": "CNY", "month": "2024-02", "rate": 0.72},
        {"currency": "CNY", "month": "2024-03", "rate": 0.73},
        {"currency": "CHF", "month": "2024-01", "rate": 1.10},
        {"currency": "CHF", "month": "2024-02", "rate": 1.11},
        {"currency": "CHF", "month": "2024-03", "rate": 1.09},
    ],
}
