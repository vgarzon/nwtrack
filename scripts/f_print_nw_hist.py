"""
`nwtrack`: Net worth tracker app.
Prototype calculating net worth from account balances.
"""

import sqlite3

from nwtrack.config import settings


def get_net_worth_at_date(date: str, currency: str = "USD") -> list[dict]:
    conn = sqlite3.connect(settings.db_file_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT total_assets, total_liabilities, net_worth FROM networth_history
    WHERE date = ? AND currency = ?;
    """

    cursor.execute(query, (date, currency))
    results = cursor.fetchall()
    conn.close()

    return results


def get_net_worth_history(currency: str = "USD") -> list[dict]:
    conn = sqlite3.connect(settings.db_file_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT date, total_assets, total_liabilities, net_worth FROM networth_history
    WHERE currency = ?
    ORDER BY date;
    """

    cursor.execute(query, (currency,))
    results = cursor.fetchall()
    conn.close()

    return results


if __name__ == "__main__":
    as_of_date = "2024-02-01"
    rows = get_net_worth_at_date(as_of_date)
    assert len(rows) == 1, "Expected exactly one record for the given date."
    res = rows[0]
    print(
        f"Date: {as_of_date}, assets: {res['total_assets']}, "
        f"liabilities: {res['total_liabilities']}, "
        f"net worth: {res['net_worth']}"
    )
    rows = get_net_worth_history()
    for res in rows:
        print(
            f"Date: {res['date']}, assets: {res['total_assets']}, "
            f"liabilities: {res['total_liabilities']}, "
            f"net worth: {res['net_worth']}"
        )
