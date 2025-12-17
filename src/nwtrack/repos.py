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
            INSERT INTO balances (account_id, month, amount)
            VALUES (:account_id, :month, :amount);
            """,
            data,
        )
        print(rowcount, "balance rows inserted.")

    def insert_exchange_rates(self, data: list[dict]) -> None:
        """Insert exchange rate data into the exchange_rates table.

        Args:
            data (list[dict]): List o exchange rate data dictionaries.
        """
        rowcount = self._db.execute_many(
            """
            INSERT INTO exchange_rates (currency, month, rate)
            VALUES (:currency, :month, :rate);
            """,
            data,
        )
        print("Inserted", rowcount, "exchange rate rows.")

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

    def get_net_worth_on_month(self, month: str, currency: str = "USD") -> list[dict]:
        """Get net worth at a specific year and month

        Args:
            month (str): The month to query net worth for in "YYYY-MM" format.
            currency (str, optional): The currency code. Defaults to "USD".

        Returns:
            list[dict]: List of net worth records for the specified year, month and currency.
        """
        query = """
            SELECT total_assets, total_liabilities, net_worth FROM networth_history
            WHERE month = :month AND currency = :currency;
            """
        results = self._db.fetch_all(query, {"month": month, "currency": currency})
        return results

    def get_net_worth_history(self, currency: str = "USD") -> list[dict]:
        """Get net worth history.
        Args:
            currency (str, optional): The currency code. Defaults to "USD".

        Returns:
            list[dict]: List of net worth records over time for the specified currency.
        """
        query = """
        SELECT month, total_assets, total_liabilities, net_worth FROM networth_history
        WHERE currency = :currency
        ORDER BY month;
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

    def get_balances_on_month(self, month: str, active_only: bool = True) -> list[dict]:
        """Get all account balances at a specific month.

        Args:
            month (): Month in "YYYY-MM" format
            active_only (bool): Whether to include only active accounts

        Returns:
            list[dict]: List of account balances.
        """
        if active_only:
            query = """
            SELECT a.id, a.name, b.amount
            FROM accounts a
            JOIN balances b ON a.id = b.account_id
            WHERE b.month = :month AND a.status = 'active';
            """
        else:
            query = """
            SELECT a.id, a.name, b.amount
            FROM accounts a
            JOIN balances b ON a.id = b.account_id
            WHERE b.month = :month;
            """
        results = self._db.fetch_all(query, {"month": month})
        balances = [
            {
                "account_id": account_id,
                "account_name": name,
                "month": month,
                "amount": amount,
            }
            for account_id, name, amount in results
        ]
        return balances

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
        self, account_id: int, month: str, new_amount: int
    ) -> None:
        """Update the balance for a specific account on a specific date.

        Args:
            account_id (int): The account ID.
            month (str): The month to the entry to update, in "YYYY-MM" format.
            new_amount (int): The new balance amount.
        """
        update_query = """
        UPDATE balances
        SET amount = :amount
        WHERE account_id = :account_id AND month = :month;
        """
        params: dict[str, str | int | None] = {
            "amount": new_amount,
            "account_id": account_id,
            "month": month,
        }
        cur = self._db.execute(update_query, params)
        assert cur.rowcount == 1, "Expected exactly one row to be updated."
        print(f"Updated account {account_id} on {month}.")

    def get_all_currency_codes(self) -> list[str]:
        """Get all currency codes.

        Returns:
            list[str]: List of currency codes.
        """
        query = "SELECT code FROM currencies;"
        results = self._db.fetch_all(query)
        currency_codes = [code for (code,) in results]
        return currency_codes

    def get_exchange_rate(self, currency: str, month: str) -> float | None:
        """Get the exchange rate for a specific currency code and month

        Args:
            currency (str): Currency code
            month (str): Month

        Returns:
            float | None: Exchange rate if found, else None
        """
        query = """
        SELECT rate FROM exchange_rates
        WHERE currency = :currency AND month = :month;
        """
        result = self._db.fetch_one(query, {"currency": currency, "month": month})
        if result:
            return float(result[0])
        return None

    def get_exchange_rate_history(self, currency: str) -> list[dict]:
        """Get exchange rate history.

        Args:
            currency (str): Currency code

        Returns:
            list[dict]: List of exchange rate records over time.
        """
        query = """
        SELECT month, rate FROM exchange_rates
        WHERE currency = :currency
        ORDER BY currency, month;
        """
        results = self._db.fetch_all(query, {"currency": currency})
        exchange_rates = [
            {
                "currency": currency,
                "month": month,
                "rate": float(rate),
            }
            for month, rate in results
        ]
        return exchange_rates

    def check_month_exists_in_balances(self, month: str):
        """Check if a specific month exists in the balances table.

        Args:
            month (str): Month in "YYYY-MM" format

        Returns:
            bool: True if the year and month exist, else False.
        """
        query = """
        SELECT 1 FROM balances
        WHERE month = :month
        LIMIT 1;
        """
        result = self._db.fetch_one(query, {"month": month})
        return result is not None

    def copy_balances_to_next_month(self, month: str) -> None:
        """Roll account balances forward from one month to the next.

        Args:
            month (str): Month of the source month in "YYYY-MM" format.
        """
        insert_query = """
        INSERT OR IGNORE INTO balances (account_id, month, amount)
        SELECT account_id, :next_month, amount
        FROM balances
        WHERE month = :month;
        """
        year_int, month_int = map(int, month.split("-"))
        if month_int < 1 or month_int > 12:
            raise ValueError(f"Invalid month: {month_int}. Must be between 1 and 12.")
        next_month = (
            f"{year_int + 1}-01"
            if month_int == 12
            else f"{year_int}-{month_int + 1:02d}"
        )
        params = {
            "month": month,
            "next_month": next_month,
        }
        cur = self._db.execute(insert_query, params)
        print(f"Copied {cur.rowcount} balances from {month} to {next_month}.")

    def close_db_connection(self) -> None:
        self._db.close_connection()
