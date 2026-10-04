"""Minimal, fictional sample dataset for demos and first-time exploration.

The records mirror the CSV bundle shape consumed by ``InitDataService`` so the
dataset loads through the same, already-validated import path.
"""

from dataclasses import dataclass

from nwtrack.domain.value_objects import Month

N_MONTHS = 12
INACTIVE_AFTER_INDEX = 4  # "Old Savings" is closed after its first four months


@dataclass(frozen=True)
class _SampleAccount:
    id: int
    name: str
    description: str
    category: str
    institution_id: int
    currency: str
    start: int  # opening balance, smallest currency unit
    step: int  # change per month, smallest currency unit


_CURRENCIES = [
    {"code": "USD", "description": "United States Dollar"},
    {"code": "CHF", "description": "Swiss Franc"},
]

_CATEGORIES = [
    {"name": "checking", "side": "asset"},
    {"name": "savings", "side": "asset"},
    {"name": "investment", "side": "asset"},
    {"name": "mortgage", "side": "liability"},
    {"name": "revolving_credit", "side": "liability"},
]

_INSTITUTIONS = [
    {"id": 1, "name": "Harbor Bank", "description": "Everyday banking and mortgage"},
    {"id": 2, "name": "Summit Brokerage", "description": "Investment brokerage"},
    {"id": 3, "name": "Alpine Bank", "description": "Swiss savings bank"},
]

_TAGS = [
    {"id": 1, "name": "core", "description": "Core cash position"},
    {"id": 2, "name": "long-term", "description": "Long-term holdings and debt"},
]

_ACCOUNTS = [
    _SampleAccount(
        1, "Everyday Checking", "Demo checking", "checking", 1, "USD", 420_000, 7_500
    ),
    _SampleAccount(
        2, "Rainy Day Savings", "Demo savings", "savings", 1, "USD", 1_500_000, 40_000
    ),
    _SampleAccount(
        3, "Index Fund", "Demo brokerage", "investment", 2, "USD", 6_000_000, 90_000
    ),
    _SampleAccount(
        4, "Swiss Savings", "Demo CHF savings", "savings", 3, "CHF", 900_000, 15_000
    ),
    _SampleAccount(
        5,
        "Travel Card",
        "Demo credit card",
        "revolving_credit",
        1,
        "USD",
        85_000,
        6_000,
    ),
    _SampleAccount(
        6, "Home Mortgage", "Demo mortgage", "mortgage", 1, "USD", 6_500_000, -20_000
    ),
    _SampleAccount(
        7, "Old Savings", "Demo closed account", "savings", 1, "USD", 300_000, 5_000
    ),
]

_ACCOUNT_TAGS = [(1, 1), (2, 1), (3, 2), (4, 2), (6, 2)]

_CHF_RATE_START_PERCENT = 88  # CHF per USD, in hundredths, drifting up 0.5 / month


def sample_months(today: Month) -> list[Month]:
    """Return ``N_MONTHS`` consecutive months ending at ``today`` (ascending)."""
    months = [today]
    for _ in range(N_MONTHS - 1):
        months.append(months[-1].previous())
    months.reverse()
    return months


def build_sample_records(today: Month) -> dict[str, list[dict]]:
    """Build the sample dataset as CSV-shaped records, ending at ``today``.

    Amounts are integers in the smallest currency unit; liabilities are
    positive (their side comes from the category).
    """
    months = sample_months(today)

    accounts = [
        {
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "category": a.category,
            "institution_id": a.institution_id,
            "currency": a.currency,
            "status": "inactive" if a.id == 7 else "active",
        }
        for a in _ACCOUNTS
    ]

    balances: list[dict] = []
    for account in _ACCOUNTS:
        for index, month in enumerate(months):
            if account.id == 7 and index >= INACTIVE_AFTER_INDEX:
                break
            balances.append(
                {
                    "id": len(balances) + 1,
                    "account_id": account.id,
                    "month": str(month),
                    "amount": account.start + account.step * index,
                }
            )

    status_history: list[dict] = []
    for account in _ACCOUNTS:
        status_history.append(
            {
                "id": len(status_history) + 1,
                "account_id": account.id,
                "status": "active",
                "effective_month": str(months[0]),
            }
        )
        if account.id == 7:
            status_history.append(
                {
                    "id": len(status_history) + 1,
                    "account_id": account.id,
                    "status": "inactive",
                    "effective_month": str(months[INACTIVE_AFTER_INDEX]),
                }
            )

    exchange_rates = [
        {
            "id": index + 1,
            "currency": "CHF",
            "month": str(month),
            "rate": f"{(_CHF_RATE_START_PERCENT * 10 + 5 * index) / 1000:.3f}",
        }
        for index, month in enumerate(months)
    ]

    return {
        "currencies": [dict(r) for r in _CURRENCIES],
        "categories": [dict(r) for r in _CATEGORIES],
        "institutions": [dict(r) for r in _INSTITUTIONS],
        "tags": [dict(r) for r in _TAGS],
        "accounts": accounts,
        "account_tags": [
            {"account_id": account_id, "tag_id": tag_id}
            for account_id, tag_id in _ACCOUNT_TAGS
        ],
        "balances": balances,
        "exchange_rates": exchange_rates,
        "account_status_history": status_history,
    }
