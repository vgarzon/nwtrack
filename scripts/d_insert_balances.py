"""
`nwtrack`: Net worth tracker app.
Prototype inserting sample balances data into the database.
"""

import sqlite3

from nwtrack.config import settings
from nwtrack.fileio import csv_file_to_list_dict


def insert_balances(data: list[dict]) -> None:
    conn = sqlite3.connect(settings.db_file_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    cursor.executemany(
        """
        INSERT INTO balances (id, account_id, date, amount)
        VALUES (:id, :account_id, :date, :amount);
        """,
        data,
    )
    print(cursor.rowcount, "balance rows inserted.")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    balances_file = "data/sample/balances.csv"
    balances_data = csv_file_to_list_dict(balances_file)
    print(f"Loaded {len(balances_data)} balance records from {balances_file}.")
    insert_balances(balances_data)
