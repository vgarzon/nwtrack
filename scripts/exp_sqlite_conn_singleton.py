"""
nwtracK: Net worth tracker app experimental script

Prototype SQLite connection singleton and database initialization
"""

import sqlite3

from nwtrack.config import settings
from nwtrack.fileio import csv_file_to_list_dict


# SQLite database from DDL script.
class SQLiteConnection:
    def __init__(self, db_file_path: str = ":memory:") -> None:
        self._db_file_path = db_file_path
        self._connection = None

    def get_connection(self):
        if self._connection is None:
            self._create_connection()
        return self._connection

    def _create_connection(self):
        self._connection = sqlite3.connect(self._db_file_path)
        self._connection.execute("PRAGMA foreign_keys = ON;")
        self._connection.row_factory = sqlite3.Row

    def execute(self, query: str, params: dict = {}) -> list[dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rowcount = cursor.rowcount
        conn.commit()
        return rowcount

    def execute_many(self, query: str, params: dict = {}) -> list[dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executemany(query, params)
        rowcount = cursor.rowcount
        conn.commit()
        return rowcount

    def fetch_all(self, query: str, params: dict = {}) -> list[dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        return results

    def close_connection(self):
        if self._connection:
            self._connection.close()
            self._connection = None


def init_db_from_ddl_script(db: SQLiteConnection, ddl_script_path: str) -> None:
    conn = db.get_connection()
    with open(ddl_script_path, "r") as f:
        ddl_script = f.read()
    conn.executescript(ddl_script)
    conn.commit()


# Initialize reference tables.


def init_currencies(db: SQLiteConnection, data: list[dict]) -> None:
    rowcount = db.execute_many(
        "INSERT INTO currencies (code, name) VALUES (:code, :name);",
        data,
    )
    print(rowcount, "currencies inserted.")


def init_account_types(db: SQLiteConnection, data: list[dict]) -> None:
    rowcount = db.execute_many(
        "INSERT INTO account_types (type, kind) VALUES (:type, :kind);",
        data,
    )
    print(rowcount, "account types inserted.")


# Insert sample account data


def insert_accounts(db: SQLiteConnection, data: list[dict]) -> None:
    rowcount = db.execute_many(
        """
        INSERT INTO accounts (id, name, description, type, currency, status)
        VALUES (:id, :name, :description, :type, :currency, :status);
        """,
        data,
    )
    print(rowcount, "account rows inserted.")


# Insert sample balances ata


def insert_balances(db: SQLiteConnection, data: list[dict]) -> None:
    rowcount = db.execute_many(
        """
        INSERT INTO balances (id, account_id, date, amount)
        VALUES (:id, :account_id, :date, :amount);
        """,
        data,
    )
    print(rowcount, "balance rows inserted.")


# Retrieve active accounts from the database


def find_active_accounts(db: SQLiteConnection) -> list[dict]:
    results = db.fetch_all(
        """
        SELECT id, name
        FROM accounts
        WHERE status = 'active';
        """
    )
    active_accounts = [{"id": account_id, "name": name} for account_id, name in results]

    return active_accounts


# Calculate net worth from account balances.


def get_net_worth_at_date(
    db: SQLiteConnection, date: str, currency: str = "USD"
) -> list[dict]:
    query = """
        SELECT total_assets, total_liabilities, net_worth FROM networth_history
        WHERE date = :date AND currency = :currency;
        """
    results = db.fetch_all(query, {"date": date, "currency": currency})
    return results


def get_net_worth_history(db: SQLiteConnection, currency: str = "USD") -> list[dict]:
    query = """
    SELECT date, total_assets, total_liabilities, net_worth FROM networth_history
    WHERE currency = :currency
    ORDER BY date;
    """
    results = db.fetch_all(query, {"currency": currency})
    return results


# Update account balance value.


def update_account_balance(
    db: SQLiteConnection, account_id: int, date: str, new_amount: int
) -> None:
    update_query = """
    UPDATE balances
    SET amount = :amount
    WHERE account_id = :account_id AND date = :date;
    """
    params = {"amount": new_amount, "account_id": account_id, "date": date}
    rowcount = db.execute(update_query, params)
    print(f"{rowcount} row(s) updated for account_id {account_id} on {date}.")


def print_net_worth_at_date(
    db: SQLiteConnection, as_of_date: str, currency: str = "USD"
) -> None:
    query = """
    SELECT total_assets, total_liabilities, net_worth FROM networth_history
    WHERE date = :date AND currency = :currency;
    """
    results = db.fetch_all(query, {"date": as_of_date, "currency": currency})

    for row in results:
        assets, liabilities, net_worth = row
        print(
            f"Date: {as_of_date}, Currency: {currency}, "
            f"Assets: {assets}, Liabilities: {liabilities}, "
            f"Net Worth: {net_worth}"
        )


def main():
    ddl_script = "sql/nwtrack_ddl.sql"
    currencies_file = "data/reference/currencies.csv"
    account_types_file = "data/reference/account_types.csv"
    accounts_file = "data/sample/accounts.csv"
    balances_file = "data/sample/balances.csv"
    as_of_date = "2024-02-01"

    print(f"Initializing database {settings.db_file_path}.")
    db = SQLiteConnection(settings.db_file_path)

    print(f"DDL script: {ddl_script}.")
    init_db_from_ddl_script(db, ddl_script)

    print(f"Initializing currency table from {currencies_file}.")
    currencies_data = csv_file_to_list_dict(currencies_file)
    init_currencies(db, currencies_data)

    print(f"Initializing account types table from {account_types_file}.")
    account_types_data = csv_file_to_list_dict(account_types_file)
    init_account_types(db, account_types_data)

    accounts_data = csv_file_to_list_dict(accounts_file)
    print(f"Loaded {len(accounts_data)} accounts from {accounts_file}.")
    insert_accounts(db, accounts_data)

    balances_data = csv_file_to_list_dict(balances_file)
    print(f"Loaded {len(balances_data)} balance records from {balances_file}.")
    insert_balances(db, balances_data)

    accounts = find_active_accounts(db)
    for account in accounts:
        print(f"Account ID: {account['id']}, Name: {account['name']}")

    rows = get_net_worth_at_date(db, as_of_date)
    assert len(rows) == 1, "Expected exactly one record for the given date."
    res = rows[0]
    print(
        f"Date: {as_of_date}, assets: {res['total_assets']}, "
        f"liabilities: {res['total_liabilities']}, "
        f"net worth: {res['net_worth']}"
    )
    rows = get_net_worth_history(db)
    for res in rows:
        print(
            f"Date: {res['date']}, assets: {res['total_assets']}, "
            f"liabilities: {res['total_liabilities']}, "
            f"net worth: {res['net_worth']}"
        )

    # update balance for account_id 1 on 2024-02-01 to 530
    print("Before update:")
    print_net_worth_at_date(db, as_of_date=as_of_date)
    update_account_balance(db, account_id=1, date=as_of_date, new_amount=530)
    print("After update:")
    print_net_worth_at_date(db, as_of_date=as_of_date)


if __name__ == "__main__":
    main()
