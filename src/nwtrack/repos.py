"""
Repository module for nwtrack database operations.
"""

from __future__ import annotations

from nwtrack.dbmanager import DBConnectionManager


class NwTrackRepository:
    """Repository for nwtrack database operations."""

    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db
        self._account_id_map: dict[str, int] | None = None

    def init_database_ddl(self, ddl_script: str) -> None:
        """Initialize the database schema from a DDL script file.

        Args:
            ddl_script (str): DDL script
        """
        print("Initializing database tables.")
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
            INSERT INTO accounts (name, description, type, currency, status)
            VALUES (:name, :description, :type, :currency, :status);
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
            INSERT INTO balances (account_id, year, month, amount)
            VALUES (:account_id, :year, :month, :amount);
            """,
            data,
        )
        print(rowcount, "balance rows inserted.")

    def get_active_accounts(self) -> list[dict]:
        """Get all active accounts."""
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

    def get_all_accounts(self) -> list[dict]:
        """Get all accounts.

        Returns:
            list[dict]: List of account records.
        """
        query = """
        SELECT id, name, description, type, currency, status FROM accounts;
        """
        results = self._db.fetch_all(query)
        accounts = [
            {
                "id": account_id,
                "name": name,
                "description": description,
                "type": type_,
                "currency": currency,
                "status": status,
            }
            for account_id, name, description, type_, currency, status in results
        ]
        return accounts

    def get_net_worth_at_year_month(
        self, year: int, month: int, currency: str = "USD"
    ) -> list[dict]:
        """Get net worth at a specific year and month

        Args:
            year (int): The year to query net worth for.
            month (int): The month to query net worth for.
            currency (str, optional): The currency code. Defaults to "USD".

        Returns:
            list[dict]: List of net worth records for the specified year, month and currency.
        """
        query = """
            SELECT total_assets, total_liabilities, net_worth FROM networth_history
            WHERE year = :year AND month = :month AND currency = :currency;
            """
        results = self._db.fetch_all(
            query, {"year": year, "month": month, "currency": currency}
        )
        return results

    def get_net_worth_history(self, currency: str = "USD") -> list[dict]:
        """Get net worth history.
        Args:
            currency (str, optional): The currency code. Defaults to "USD".

        Returns:
            list[dict]: List of net worth records over time for the specified currency.
        """
        query = """
        SELECT year, month, total_assets, total_liabilities, net_worth FROM networth_history
        WHERE currency = :currency
        ORDER BY year, month;
        """
        results = self._db.fetch_all(query, {"currency": currency})
        return results

    def init_account_id_map(self) -> None:
        """Initialize a mapping of account names to their IDs.

        Returns:
            dict[str, int]: A dictionary mapping account names to IDs.
        """
        # account_id_map = {acc["name"]: acc["id"] for acc in accounts}
        query = "SELECT id, name FROM accounts;"
        results = self._db.fetch_all(query)
        self._account_id_map: dict[str, int] = {
            name: account_id for account_id, name in results
        }

    def get_account_id_by_name(self, account_name: str) -> int | None:
        """Get the account ID for a given account name.

        Args:
            account_name (str): The name of the account.

        Returns:
            int | None: The account ID if found, else None.
        """
        if self._account_id_map is None:
            self.init_account_id_map()
        return self._account_id_map.get(account_name, None)

    def update_account_balance(
        self, account_id: int, year: int, month: int, new_amount: int
    ) -> None:
        """Update the balance for a specific account on a specific date.

        Args:
            account_id (int): The account ID.
            year (int): The year of the entry to update.
            month (int): The month to the entry to update.
            new_amount (int): The new balance amount.
        """
        update_query = """
        UPDATE balances
        SET amount = :amount
        WHERE account_id = :account_id AND year = :year AND month = :month;
        """
        params: dict[str, str | int | None] = {
            "amount": new_amount,
            "account_id": account_id,
            "year": year,
            "month": month,
        }
        cur = self._db.execute(update_query, params)
        assert cur.rowcount == 1, "Expected exactly one row to be updated."
        print(f"Updated account {account_id} on {year}-{month}.")

    def close_db_connection(self) -> None:
        self._db.close_connection()
