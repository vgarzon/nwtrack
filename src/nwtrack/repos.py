"""
Repository module for nwtrack database operations.
"""

from __future__ import annotations

from typing import Protocol
from nwtrack.dbmanager import DBConnectionManager
from nwtrack.models import (
    Account,
    Balance,
    Currency,
    Category,
    ExchangeRate,
    Side,
    Status,
    Month,
    NetWorth,
)
from dataclasses import asdict


class CurrencyRepository(Protocol):
    """Protocol for currency repository operations."""

    def insert_many(self, data: list[Currency]) -> None:
        """Insert list of currencies into the currencies table."""
        ...

    def get_codes(self) -> list[str]:
        """Get all currency codes."""
        ...

    def get_all(self) -> list[Currency]:
        """Get all currencies."""
        ...

    def get_dict(self) -> dict[str, Currency]:
        """Get all currencies in a dictionary indexed by code."""
        ...


class CategoryRepository(Protocol):
    """Protocol for category repository operations."""

    def insert_many(self, data: list[Category]) -> None:
        """Insert list of categories into the categories table."""
        ...

    def get_all(self) -> list[Category]:
        """Get all categories."""
        ...

    def get_dict(self) -> dict[str, Category]:
        """Get all categories in a dictionary indexed by name."""
        ...


class ExchangeRateRepository(Protocol):
    """Protocol for exchange rate repository operations."""

    def insert_many(self, data: list[ExchangeRate]) -> None:
        """Insert list of exchange rates into the exchange_rates table."""
        ...

    def get(self, month: Month, currency_code: str) -> ExchangeRate | None:
        """Get the exchange rate for a specific currency code and month."""
        ...

    def get_currency(self, currency_code: str) -> list[ExchangeRate]:
        """Get exchange rates for a given currency code."""
        ...

    def get_month(self, month: Month) -> list[ExchangeRate]:
        """Get exchange rates for all currencies for a given month."""
        ...


class AccountRepository(Protocol):
    """Protocol for account repository operations."""

    def insert_many(self, data: list[Account]) -> None:
        """Insert list of accounts into the accounts table."""
        ...

    def get_active(self) -> list[Account]:
        """Get all active accounts."""
        ...

    def get_all(self) -> list[Account]:
        """Get all accounts."""
        ...

    def get_dict_id(self) -> dict[int, Account]:
        """Get all accounts in a dictionary indexed by account id."""
        ...

    def get_dict_name(self) -> dict[str, Account]:
        """Get all accounts in a dictionary indexed by name."""
        ...


class BalanceRepository(Protocol):
    """Protocol for balance repository operations."""

    def insert_many(self, data: list[Balance]) -> None:
        """Insert list of balances into the balances table."""
        ...

    def get(self, month: Month, account_name: str) -> Balance:
        """Get all account balances on a specific month."""
        ...

    def get_month(self, month: Month, active_only: bool = True) -> list[Balance]:
        """Get all account balances on a specific month."""
        ...

    def update(self, account_id: int, month: Month, new_amount: int) -> None:
        """Update the balance for specific account and month."""
        ...

    def check_month(self, month: Month):
        """Check that there are balance entries for a given month."""
        ...

    def roll_forward(self, month: Month) -> None:
        """Roll account balances forward from one month to the next."""
        ...

    def fetch_sample(self, limit: int = 5) -> list[Balance]:
        """Fetch sample balance records for debugging."""
        ...


class NetWorthRepository(Protocol):
    """Protocol for net worth repository operations."""

    def get(self, month: Month, currency_code: str = "USD") -> NetWorth:
        """Get net worth value for given month and currency."""
        ...

    def history(self, currency_code: str = "USD") -> list[NetWorth]:
        """Get net worth history for a given currency."""
        ...


class SQLiteCurrencyRepository:
    """Repository for currencies SQLite database operations."""

    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db

    def insert_many(self, data: list[Currency]) -> None:
        """Insert list of currencies into the currencies table.

        Args:
            data (list[Currency]): List of Currency objects.
        """
        rowcount = self._db.execute_many(
            "INSERT INTO currencies (code, description) VALUES (:code, :description);",
            [asdict(currency) for currency in data],
        )
        print("Inserted", rowcount, "currency rows.")

    def get_codes(self) -> list[str]:
        """Get all currency codes.

        Returns:
            list[str]: List of currency codes.
        """
        query = "SELECT code FROM currencies;"
        results = self._db.fetch_all(query)
        currency_codes = [code for (code,) in results]
        return currency_codes

    def get_all(self) -> list[Currency]:
        """Get all currencies.

        Returns:
            list[Currency]: List of currency records.
        """
        query = "SELECT code, description FROM currencies;"
        results = self._db.fetch_all(query)
        currencies = [
            Currency(code=code, description=description)
            for code, description in results
        ]
        return currencies

    def get_dict(self) -> dict[str, Currency]:
        """Get all currencies in a dictionary indexed by code.

        Returns:
            dict[str, Currency]: Dictionary of currency records indexed by code.
        """
        results = self.get_all()
        currencies = {result.code: result for result in results}
        return currencies


class SQLiteCategoryRepository:
    """Repository for category SQLite database operations."""

    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db

    def insert_many(self, data: list[Category]) -> None:
        """Insert list of categories into SQLite database.

        Args:
            data (list[Category]): List of category data dictionaries.
        """
        rowcount = self._db.execute_many(
            "INSERT INTO categories (name, side) VALUES (:name, :side);",
            [asdict(category) for category in data],
        )
        print("Inserted", rowcount, "category rows.")

    def get_all(self) -> list[Category]:
        """Get all Categories.

        Returns:
            list[Category]: List of category objects.
        """
        query = "SELECT name, side FROM categories;"
        results = self._db.fetch_all(query)
        categories = [Category(name=r["name"], side=Side(r["side"])) for r in results]
        return categories

    def get_dict(self) -> dict[str, Category]:
        """Get all categories in a dictionary indexed by code.

        Returns:
            dict[str, Category]: Dictionary of categories records indexed by name.
        """
        results = self.get_all()
        categories = {result.name: result for result in results}
        return categories


class SQLiteExchangeRateRepository:
    """Repository for exchange rates SQLite database operations."""

    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db

    def insert_many(self, data: list[ExchangeRate]) -> None:
        """Insert list of exchange rates into the exchange_rates table.

        Args:
            data (list[ExchangeRate]): List of ExchangeRate objects.
        """
        rowcount = self._db.execute_many(
            """
            INSERT INTO exchange_rates (currency, month, rate)
            VALUES (:currency, :month, :rate);
            """,
            [
                {
                    "currency": r.currency_code,
                    "month": str(r.month),
                    "rate": r.rate,
                }
                for r in data
            ],
        )
        print("Inserted", rowcount, "exchange rate rows.")

    def get(self, month: Month, currency_code: str) -> ExchangeRate | None:
        """Get the exchange rate for a specific currency code and month

        Args:
            month (Month): Month object
            currency_code (str): Currency code

        Returns:
            ExchangeRate | None: Exchange rate record if found, else None
        """
        query = """
        SELECT rate FROM exchange_rates
        WHERE currency = :currency AND month = :month;
        """
        result = self._db.fetch_one(
            query, {"currency": currency_code, "month": str(month)}
        )
        if result:
            return ExchangeRate(
                currency_code=currency_code, month=month, rate=result["rate"]
            )
        return None

    def get_currency(self, currency_code: str) -> list[ExchangeRate]:
        """Get exchange rates for a given currency code

        Args:
            currency_code (str): Currency code

        Returns:
            list[ExchangeRate]: List of exchange rate records
        """
        query = """
        SELECT month, rate FROM exchange_rates
        WHERE currency = :currency;
        """
        results = self._db.fetch_all(query, {"currency": currency_code})
        exchange_rates = [
            ExchangeRate(
                currency_code=currency_code,
                month=Month.parse(res["month"]),
                rate=res["rate"],
            )
            for res in results
        ]
        return exchange_rates

    def get_month(self, month: Month) -> list[ExchangeRate]:
        """Get exchange rates for all currencies for a given month

        Args:
            month (Month): Month object

        Returns:
            list[ExchangeRate]: List of exchange rate records
        """
        query = """
        SELECT currency, rate FROM exchange_rates
        WHERE month = :month;
        """
        results = self._db.fetch_all(query, {"month": str(month)})
        exchange_rates = [
            ExchangeRate(
                currency_code=res["currency"],
                month=month,
                rate=res["rate"],
            )
            for res in results
        ]
        return exchange_rates


class SQLiteAccountRepository:
    """Repository for account SQLite database operations."""

    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db

    def insert_many(self, data: list[Account]) -> None:
        """Insert list of accounts into the accounts table.

        Args:
            data (list[Account]): List of Account objects
        """
        rowcount = self._db.execute_many(
            """
            INSERT INTO accounts (name, description, category, currency, status)
            VALUES (:name, :description, :category, :currency, :status);
            """,
            [
                {
                    "name": acc.name,
                    "description": acc.description,
                    "category": acc.category_name,
                    "currency": acc.currency_code,
                    "status": str(acc.status),
                }
                for acc in data
            ],
        )
        print("Inserted", rowcount, "account rows.")

    def get_active(self) -> list[Account]:
        """Get all active accounts."""
        results = self._db.fetch_all(
            """
            SELECT id, name, description, category, currency, status
            FROM accounts
            WHERE status = 'active';
            """
        )
        active_accounts = [
            Account(
                id=account_id,
                name=name,
                description=description,
                category_name=category,
                currency_code=currency,
                status=Status(status),
            )
            for account_id, name, description, category, currency, status in results
        ]
        return active_accounts

    def get_all(self) -> list[Account]:
        """Get all accounts.

        Returns:
            list[Account]: List of account objects.
        """
        query = """
        SELECT id, name, description, category, currency, status FROM accounts;
        """
        results = self._db.fetch_all(query)
        accounts = [
            Account(
                id=account_id,
                name=name,
                description=description,
                category_name=category,
                currency_code=currency,
                status=Status(status),
            )
            for account_id, name, description, category, currency, status in results
        ]
        return accounts

    def get_dict_id(self) -> dict[int, Account]:
        """Get all accounts in a dictionary indexed by accoun id.

        Returns:
            dict[int, Account]: Dictionary of account records indexed by id.
        """
        results = self.get_all()
        accounts = {result.id: result for result in results}
        return accounts

    def get_dict_name(self) -> dict[str, Account]:
        """Get all accounts in a dictionary indexed by name.

        Returns:
            dict[str, Account]: Dictionary of account records indexed by name.
        """
        results = self.get_all()
        accounts = {result.name: result for result in results}
        return accounts


class SQLiteBalanceRepository:
    """Repository for balances SQLite database operations."""

    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db

    def insert_many(self, data: list[Balance]) -> None:
        """Insert list of balances into the balances table.

        Args:
            data (list[Balance]): List of balance objects
        """
        query = """
        INSERT INTO balances (account_id, month, amount)
        VALUES (:account_id, :month, :amount);
        """
        rowcount = self._db.execute_many(
            query,
            [
                {
                    "account_id": bal.account_id,
                    "month": str(bal.month),
                    "amount": bal.amount,
                }
                for bal in data
            ],
        )
        print("Inserted", rowcount, "balance rows.")

    def get(self, month: Month, account_name: str) -> Balance:
        """Get all account balances on a specific month.

        Args:
            month (Month): Month object
            account_name (str): Account name

        Returns:
            Balance: Account balance record
        """
        query = """
        SELECT b.id, b.account_id, a.name, b.amount
        FROM accounts a
        JOIN balances b ON a.id = b.account_id
        WHERE b.month = :month AND a.name = :account_name;
        """
        results = self._db.fetch_all(
            query, {"month": str(month), "account_name": account_name}
        )
        assert len(results) <= 1, "Expected at most one balance record."
        res = results[0]
        balance = Balance(
            id=res["id"],
            account_id=res["account_id"],
            month=month,
            amount=res["amount"],
        )
        return balance

    def get_month(self, month: Month, active_only: bool = True) -> list[Balance]:
        """Get all account balances on a specific month.

        Args:
            month (Month): Month object
            active_only (bool): Whether to include only active accounts

        Returns:
            list[Balance]: List of account balances.
        """
        if active_only:
            query = """
            SELECT b.id, b.account_id, a.name, b.amount
            FROM accounts a
            JOIN balances b ON a.id = b.account_id
            WHERE b.month = :month AND a.status = 'active';
            """
        else:
            query = """
            SELECT b.id, b.account_id, a.name, b.amount
            FROM accounts a
            JOIN balances b ON a.id = b.account_id
            WHERE b.month = :month;
            """
        results = self._db.fetch_all(query, {"month": str(month)})
        balances = [
            Balance(
                id=res["id"],
                account_id=res["account_id"],
                month=month,
                amount=res["amount"],
            )
            for res in results
        ]
        return balances

    def update(self, account_id: int, month: Month, new_amount: int) -> None:
        """Update the balance for specific account and month.

        Args:
            account_id (int): The account ID.
            month (Month): The month to the entry to update.
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
            "month": str(month),
        }
        cur = self._db.execute(update_query, params)
        assert cur.rowcount == 1, "Expected exactly one row to be updated."
        print(f"Updated account {account_id} on {month}.")

    def check_month(self, month: Month):
        """Check that there are balance entries for a given month.

        Args:
            month (Month): Month object

        Returns:
            bool: True if the year and month exist, else False.
        """
        query = """
        SELECT 1 FROM balances
        WHERE month = :month
        LIMIT 1;
        """
        result = self._db.fetch_one(query, {"month": str(month)})
        return result is not None

    def roll_forward(self, month: Month) -> None:
        """Roll account balances forward from one month to the next.

        Args:
            month (Month): Source Month object
        """
        insert_query = """
        INSERT OR IGNORE INTO balances (account_id, month, amount)
        SELECT account_id, :next_month, amount
        FROM balances
        WHERE month = :month;
        """
        next_month = month.increment()
        params = {
            "month": str(month),
            "next_month": str(next_month),
        }
        cur = self._db.execute(insert_query, params)
        print(f"Rolled {cur.rowcount} balances forward to {next_month}.")

    def fetch_sample(self, limit: int = 5) -> list[Balance]:
        """Fetch sample balance records for debugging.

        Args:
            limit (int, optional): Number of sample records to fetch. Defaults to 5.
        Returns:
            list[Balance]: List of balance records.
        """
        query = """
        SELECT id, account_id, month, amount
        FROM balances
        LIMIT :limit;
        """
        results = self._db.fetch_all(query, {"limit": limit})
        balances = [
            Balance(
                id=res["id"],
                account_id=res["account_id"],
                month=Month.parse(res["month"]),
                amount=res["amount"],
            )
            for res in results
        ]
        return balances


class SQLiteNetWorthRepository:
    """Repository net worth operations."""

    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db

    def get(self, month: Month, currency_code: str = "USD") -> NetWorth:
        """Get net worth value for given month and currency

        Args:
            month (Month): The month to query net worth.
            currency_code (str, optional): The currency code. Defaults to "USD".

        Returns:
            NetWorth: Net worth record.
        """
        query = """
        SELECT total_assets, total_liabilities, net_worth FROM networth_history
        WHERE month = :month AND currency = :currency;
        """
        results = self._db.fetch_all(
            query, {"month": str(month), "currency": currency_code}
        )
        assert len(results) <= 1, "Expected at most one net worth record."
        result = results[0]
        nw = NetWorth(
            month=month,
            assets=result["total_assets"],
            liabilities=result["total_liabilities"],
            net_worth=result["net_worth"],
        )
        return nw

    def history(self, currency_code: str = "USD") -> list[NetWorth]:
        """Get net worth history for a given currency.
        Args:
            currency_code (str, optional): The currency code. Defaults to "USD".

        Returns:
            list[NetWorth]: List of Net Worth records.
        """
        query = """
        SELECT month, total_assets, total_liabilities, net_worth
        FROM networth_history
        WHERE currency = :currency
        ORDER BY month;
        """
        results = self._db.fetch_all(query, {"currency": currency_code})
        net_worths = [
            NetWorth(
                month=Month.parse(month),
                assets=total_assets,
                liabilities=total_liabilities,
                net_worth=net_worth,
            )
            for month, total_assets, total_liabilities, net_worth in results
        ]
        return net_worths

    def close_db_connection(self) -> None:
        self._db.close_connection()
