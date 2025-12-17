"""
Repository module for nwtrack database operations.
"""

from __future__ import annotations

from nwtrack.dbmanager import DBConnectionManager


class SQLiteCurrencyRepository:
    """Repository for currencies SQLite database operations."""

    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db

    def insert_many(self, data: list[dict]) -> None:
        """Insert list of currencies into the currencies table.

        Args:
            data (list[dict]): List of currency data dictionaries.
        """
        rowcount = self._db.execute_many(
            "INSERT INTO currencies (code, name) VALUES (:code, :name);",
            data,
        )
        print(rowcount, "currencies inserted.")

    def get_codes(self) -> list[str]:
        """Get all currency codes.

        Returns:
            list[str]: List of currency codes.
        """
        query = "SELECT code FROM currencies;"
        results = self._db.fetch_all(query)
        currency_codes = [code for (code,) in results]
        return currency_codes


class SQLiteAccountTypeRepository:
    """Repository for account types SQLite database operations."""

    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db

    def insert_many(self, data: list[dict]) -> None:
        """Insert list of account types into the account_types table.

        Args:
            data (list[dict]): List of account type data dictionaries.
        """
        rowcount = self._db.execute_many(
            "INSERT INTO account_types (type, kind) VALUES (:type, :kind);",
            data,
        )
        print(rowcount, "account types inserted.")


class SQLiteExchangeRateRepository:
    """Repository for exchange rates SQLite database operations."""

    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db

    def insert_many(self, data: list[dict]) -> None:
        """Insert list of exchange rates into the exchange_rates table.

        Args:
            data (list[dict]): List of exchange rate data dictionaries.
        """
        rowcount = self._db.execute_many(
            """
            INSERT INTO exchange_rates (currency, month, rate)
            VALUES (:currency, :month, :rate);
            """,
            data,
        )
        print("Inserted", rowcount, "exchange rate rows.")

    def get(self, currency: str, month: str) -> float | None:
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

    def history(self, currency: str) -> list[dict]:
        """Get exchange rate history for a given currency.

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


class SQLiteAccountRepository:
    """Repository for account SQLite database operations."""

    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db
        self._id_map: dict[str, int] | None = None

    def insert_many(self, data: list[dict]) -> None:
        """Insert list of accounts into the accounts table.

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
        print("Inserted", rowcount, "account rows.")

    def get_active(self) -> list[dict]:
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

    def get_all(self) -> list[dict]:
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

    def init_id_map(self) -> None:
        """Initialize a mapping of account names to their IDs.

        Returns:
            dict[str, int]: A dictionary mapping account names to IDs.
        """
        # account_id_map = {acc["name"]: acc["id"] for acc in accounts}
        query = "SELECT id, name FROM accounts;"
        results = self._db.fetch_all(query)
        self._id_map: dict[str, int] = {
            name: account_id for account_id, name in results
        }

    def get_id(self, account_name: str) -> int | None:
        """Get the account ID for a given account name.

        Args:
            account_name (str): The name of the account.

        Returns:
            int | None: The account ID if found, else None.
        """
        if self._id_map is None:
            self.init_id_map()
        return self._id_map.get(account_name, None)


class SQLiteBalanceRepository:
    """Repository for balances SQLite database operations."""

    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db

    def insert_many(self, data: list[dict]) -> None:
        """Insert list of balances into the balances table.

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
        print("Inserted", rowcount, "balance rows.")

    def get_month(self, month: str, active_only: bool = True) -> list[dict]:
        """Get all account balances on a specific month.

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

    def update(self, account_id: int, month: str, new_amount: int) -> None:
        """Update the balance for specific account and month.

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

    def check_month(self, month: str):
        """Check that there are balance entries for a given month.

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

    def roll_forward(self, month: str) -> None:
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


class NetWorthRepository:
    """Repository net worth operations."""

    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db

    def get(self, month: str, currency: str = "USD") -> list[dict]:
        """Get net worth value for given month and currency

        Args:
            month (str): The month to query net worth for in "YYYY-MM" format.
            currency (str, optional): The currency code. Defaults to "USD".

        Returns:
            list[dict]: List of net worth records.
        """
        query = """
        SELECT total_assets, total_liabilities, net_worth FROM networth_history
        WHERE month = :month AND currency = :currency;
        """
        results = self._db.fetch_all(query, {"month": month, "currency": currency})
        return results

    def history(self, currency: str = "USD") -> list[dict]:
        """Get net worth history for a given currency.
        Args:
            currency (str, optional): The currency code. Defaults to "USD".

        Returns:
            list[dict]: List of net worth records.
        """
        query = """
        SELECT month, total_assets, total_liabilities, net_worth FROM networth_history
        WHERE currency = :currency
        ORDER BY month;
        """
        results = self._db.fetch_all(query, {"currency": currency})
        return results

    def close_db_connection(self) -> None:
        self._db.close_connection()
