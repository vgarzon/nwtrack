"""
Prototype retrieving active accounts from the database.
"""

import sqlite3

from nwtrack.config import settings


def find_active_accounts() -> list[dict]:
    conn = sqlite3.connect(settings.db_file_path)
    cursor = conn.cursor()

    query = """
    SELECT id, name
    FROM accounts
    WHERE status = 'active';
    """

    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    active_accounts = []
    for row in results:
        account_id, name = row
        active_accounts.append(
            {
                "id": account_id,
                "name": name,
            }
        )

    return active_accounts


if __name__ == "__main__":
    accounts = find_active_accounts()
    for account in accounts:
        print(f"Account ID: {account['id']}, Name: {account['name']}")
