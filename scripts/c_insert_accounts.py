"""
`nwtrack`: Net worth tracker app.
Prototype inserting sample accounts data into the database.
"""

import sqlite3

from nwtrack.config import settings
from nwtrack.fileio import csv_file_to_list_dict


def insert_accounts(data: list[dict]) -> None:
    conn = sqlite3.connect(settings.db_file_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    cursor.executemany(
        """
        INSERT INTO accounts (id, name, description, type, currency, status)
        VALUES (:id, :name, :description, :type, :currency, :status);
        """,
        data,
    )
    print(cursor.rowcount, "account rows inserted.")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    accounts_file = "data/sample/accounts.csv"
    accounts_data = csv_file_to_list_dict(accounts_file)
    print(f"Loaded {len(accounts_data)} accounts from {accounts_file}.")
    insert_accounts(accounts_data)
