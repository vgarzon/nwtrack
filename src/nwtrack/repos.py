"""
Repository module for nwtrack database operations.
"""

from __future__ import annotations

from nwtrack.config import Config
from nwtrack.dbmanager import DBConnectionManager


class NwTrackRepository:
    """Repository for nwtrack database operations."""

    def __init__(self, config: Config, db: DBConnectionManager) -> None:
        self._db = db
        self._db_ddl_path = config.db_ddl_path
        self.init_database(self._db_ddl_path)

    def init_database(self, ddl_script_path: str) -> None:
        """Initialize the database schema from a DDL script file.

        Args:
            ddl_script_path (str): Path to the DDL script file.
        """
        print(f"Initializing database tables with script {ddl_script_path}.")
        with open(ddl_script_path, "r") as f:
            ddl_script = f.read()
        self._db.execute_script(ddl_script)

    def init_currencies(self, data: list[dict]) -> None:
        """Initialize the currencies table with data.

        Args:
            data (list[dict]): List of currency data dictionaries.
        """
        rowcount = self._db.execute_many(
            "INSERT INTO currencies (code, name) VALUES (:code, :name);",
            data,
        )
        print(rowcount, "currencies inserted.")

    def init_account_types(self, data: list[dict]) -> None:
        """Initialize the account_types table with data.

        Args:
            data (list[dict]): List of account type data dictionaries.
        """
        rowcount = self._db.execute_many(
            "INSERT INTO account_types (type, kind) VALUES (:type, :kind);",
            data,
        )
        print(rowcount, "account types inserted.")

    def insert_accounts(self, data: list[dict]) -> None:
        """Insert account data into the accounts table.

        Args:
            data (list[dict]): List of account data dictionaries.
        """
        rowcount = self._db.execute_many(
            """
            INSERT INTO accounts (id, name, description, type, currency, status)
            VALUES (:id, :name, :description, :type, :currency, :status);
            """,
            data,
        )
        print(rowcount, "account rows inserted.")

    def insert_balances(self, data: list[dict]) -> None:
        """Insert balance data into the balances table.

        Args:
            data (list[dict]): List of balance data dictionaries.
        """
        rowcount = self._db.execute_many(
            """
            INSERT INTO balances (id, account_id, date, amount)
            VALUES (:id, :account_id, :date, :amount);
            """,
            data,
        )
        print(rowcount, "balance rows inserted.")

    def find_active_accounts(self) -> list[dict]:
        """Find all active accounts."""
        results = self._db.fetch_all(
            """
            SELECT id, name
            FROM accounts
            WHERE status = 'active';
            """
        )
        active_accounts = [
            {"id": account_id, "name": name} for account_id, name in results
        ]
        return active_accounts

    def get_net_worth_at_date(self, date: str, currency: str = "USD") -> list[dict]:
        """Get net worth at a specific date.

        Args:
            date (str): The date to query net worth for.
            currency (str, optional): The currency code. Defaults to "USD".

        Returns:
            list[dict]: List of net worth records for the specified date and currency.
        """
        query = """
            SELECT total_assets, total_liabilities, net_worth FROM networth_history
            WHERE date = :date AND currency = :currency;
            """
        results = self._db.fetch_all(query, {"date": date, "currency": currency})
        return results

    def get_net_worth_history(self, currency: str = "USD") -> list[dict]:
        """Get net worth history.
        Args:
            currency (str, optional): The currency code. Defaults to "USD".

        Returns:
            list[dict]: List of net worth records over time for the specified currency.
        """
        query = """
        SELECT date, total_assets, total_liabilities, net_worth FROM networth_history
        WHERE currency = :currency
        ORDER BY date;
        """
        results = self._db.fetch_all(query, {"currency": currency})
        return results

    def update_account_balance(
        self, account_id: int, date: str, new_amount: int
    ) -> None:
        """Update the balance for a specific account on a specific date.

        Args:
            account_id (int): The account ID.
            date (str): The date of the balance to update.
            new_amount (int): The new balance amount.
        """
        update_query = """
        UPDATE balances
        SET amount = :amount
        WHERE account_id = :account_id AND date = :date;
        """
        params: dict[str, str | int | None] = {
            "amount": new_amount,
            "account_id": account_id,
            "date": date,
        }
        cur = self._db.execute(update_query, params)
        rowcount = cur.rowcount
        print(f"{rowcount} row(s) updated for account_id {account_id} on {date}.")

    def print_net_worth_at_date(self, as_of_date: str, currency: str = "USD") -> None:
        results = self.get_net_worth_at_date(as_of_date, currency)
        assert len(results) == 1, "Expected exactly one record for the given date."

        for row in results:
            assets, liabilities, net_worth = row
            print(
                f"Date: {as_of_date}, Currency: {currency}, "
                f"Assets: {assets}, Liabilities: {liabilities}, "
                f"Net Worth: {net_worth}"
            )

    def close_db_connection(self) -> None:
        self._db.close_connection()
