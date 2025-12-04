"""
`nwtrack`: Networth tracker app.
Initialize reference tables.
"""

import sqlite3

from nwtrack.config import settings
from nwtrack.fileio import csv_file_to_list_dict


def init_currencies(data: list[dict]) -> None:
    conn = sqlite3.connect(settings.db_file_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    cursor.executemany(
        "INSERT INTO currencies (code, name) VALUES (:code, :name);",
        data,
    )
    print(cursor.rowcount, "currencies inserted.")

    conn.commit()
    conn.close()


def init_account_types(data: list[dict]) -> None:
    conn = sqlite3.connect(settings.db_file_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    cursor.executemany(
        "INSERT INTO account_types (type, kind) VALUES (:type, :kind);",
        data,
    )
    print(cursor.rowcount, "account types inserted.")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    currencies_file = "data/reference/currencies.csv"
    account_types_file = "data/reference/account_types.csv"
    print(f"Initializing currency table from {currencies_file}.")
    currencies_data = csv_file_to_list_dict(currencies_file)
    init_currencies(currencies_data)
    print(f"Initializing account types table from {account_types_file}.")
    account_types_data = csv_file_to_list_dict(account_types_file)
    init_account_types(account_types_data)
