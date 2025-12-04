"""
`nwtrack`: Net worth tracker app.
Prototype updating account balance value
"""

import sqlite3

from nwtrack.config import settings


def update_account_balance(account_id: int, date: str, new_amount: int) -> None:
    conn = sqlite3.connect(settings.db_file_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    update_query = """
    UPDATE balances
    SET amount = ?
    WHERE account_id = ? AND date = ?;
    """

    cursor.execute(update_query, (new_amount, account_id, date))
    print(f"{cursor.rowcount} row(s) updated for account_id {account_id} on {date}.")

    conn.commit()
    conn.close()


def print_net_worth_at_date(as_of_date: str, currency: str = "USD") -> None:
    conn = sqlite3.connect(settings.db_file_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # load net worth history from networth_history view
    query = """
    SELECT total_assets, total_liabilities, net_worth FROM networth_history
    WHERE date = ? AND currency = ?;
    """

    cursor.execute(query, (as_of_date, currency))
    results = cursor.fetchall()
    conn.close()

    for row in results:
        assets, liabilities, net_worth = row
        print(
            f"Date: {as_of_date}, Currency: {currency}, "
            f"Assets: {assets}, Liabilities: {liabilities}, "
            f"Net Worth: {net_worth}"
        )


if __name__ == "__main__":
    # Example usage: update balance for account_id 1 on 2024-02-01 to 530
    print("Before update:")
    print_net_worth_at_date(as_of_date="2024-02-01")
    update_account_balance(account_id=1, date="2024-02-01", new_amount=530)
    print("After update:")
    print_net_worth_at_date(as_of_date="2024-02-01")
