"""
Repository module for nwtrack database operations.
"""

from __future__ import annotations

from typing import Protocol, TypeVar, Generic

from nwtrack.dbmanager import DBConnectionManager
from nwtrack.models import (
    Account,
    Balance,
    Category,
    Currency,
    ExchangeRate,
    Month,
    NetWorth,
)
from nwtrack.mappers import (
    Mapper,
    NetWorthMapper,
    SQLiteRecord,
)

TEntity = TypeVar("TEntity")


class Repository(Protocol[TEntity]):
    """Generic repository protocol."""

    def insert_many(self, data: list[TEntity]) -> None: ...

    def get_all(self) -> list[TEntity]: ...

    def count(self) -> int: ...

    def delete_all(self) -> None: ...

    def hydrate(self, data: SQLiteRecord) -> TEntity: ...

    def hydrate_many(self, data: list[SQLiteRecord]) -> list[TEntity]: ...


class BaseRepository(Generic[TEntity]):
    """Base repository class implementing common methods."""

    def __init__(self, db: DBConnectionManager, mapper: Mapper[TEntity]) -> None:
        self._db: DBConnectionManager = db
        self._mapper: Mapper = mapper

    def insert_many(self, data: list[TEntity]) -> None:
        """Insert list of entities into the corresponding table.

        Args:
            data (list[Entity]): List of entity objects.
        """
        raise NotImplementedError

    def get_all(self) -> list[TEntity]:
        """Get all entities.

        Returns:
            list[Entity]: List of entity objects.
        """
        raise NotImplementedError

    def count(self) -> int:
        """Count the number of records.

        Returns:
            int: Number of records.
        """
        raise NotImplementedError

    def delete_all(self) -> None:
        """Delete all records."""
        raise NotImplementedError

    def hydrate(self, record: dict) -> TEntity:
        """Hydrate record to Entity.

        Args:
            record (dict): data dictionary

        Returns:
            Entity: Entity object.
        """
        return self._mapper.to_entity(record)

    def hydrate_many(self, data: list[dict]) -> list[TEntity]:
        """Hydrate list of records to list of Entities.

        Args:
            data (list[dict]): list of data dictionaries.

        Returns:
            list[Entity]: list of Entity objects.
        """
        return [self.hydrate(record) for record in data]


class CurrenciesRepository(Repository[Currency], Protocol):
    """Protocol for currency repository operations."""

    def get(self, code: str) -> Currency | None:
        """Get currency by code."""
        ...

    def get_codes(self) -> list[str]:
        """Get all currency codes."""
        ...

    def get_dict(self) -> dict[str, Currency]:
        """Get all currencies in a dictionary indexed by code."""
        ...


class CategoriesRepository(Repository[Category], Protocol):
    """Protocol for category repository operations."""

    def get(self, name: str) -> Category | None:
        """Get category by name."""
        ...

    def get_dict(self) -> dict[str, Category]:
        """Get all categories in a dictionary indexed by name."""
        ...


class ExchangeRatesRepository(Repository[ExchangeRate], Protocol):
    """Protocol for exchange rate repository operations."""

    def get(self, month: Month, currency_code: str) -> ExchangeRate | None:
        """Get the exchange rate for a specific currency code and month."""
        ...

    def get_currency(self, currency_code: str) -> list[ExchangeRate]:
        """Get exchange rates for a given currency code."""
        ...

    def get_month(self, month: Month) -> list[ExchangeRate]:
        """Get exchange rates for all currencies for a given month."""
        ...


class AccountsRepository(Repository[Account], Protocol):
    """Protocol for account repository operations."""

    def get_by_id(self, account_id: int) -> Account | None:
        """Get account by ID."""
        ...

    def get_by_name(self, account_name: str) -> Account | None:
        """Get account by name."""
        ...

    def get_active(self) -> list[Account]:
        """Get all active accounts."""
        ...

    def get_dict_id(self) -> dict[int, Account]:
        """Get all accounts in a dictionary indexed by account id."""
        ...

    def get_dict_name(self) -> dict[str, Account]:
        """Get all accounts in a dictionary indexed by name."""
        ...

    def insert(self, data: Account) -> Account:
        """Insert account object in respective table."""
        ...

    def delete_by_id(self, account_id: int) -> int:
        """Delete account by ID."""
        ...

    def update_name(self, account_id: int, new_name: str) -> int:
        """Update account name."""
        ...

    def update_status(self, account_id: int, new_status: str) -> int:
        """Update account status."""
        ...

    def update_currency(self, account_id: int, new_currency_code: str) -> int:
        """Update account currency."""
        ...

    def update_category(self, account_id: int, new_category_name: str) -> int:
        """Update account category."""
        ...

    def update_description(self, account_id: int, new_description: str) -> int:
        """Update account description."""
        ...


class BalancesRepository(Repository[Balance], Protocol):
    """Protocol for balance repository operations."""

    def get(self, month: Month, account_name: str) -> Balance:
        """Get all account balances on a specific month."""
        ...

    def get_by_account_id(self, month: Month, account_id: int) -> Balance:
        """Get all balances given account id and month."""
        ...

    def get_all_by_account_id(self, account_id: int) -> list[Balance]:
        """Get all balances given account id."""
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

    def delete_by_account_id(self, account_id: int) -> int:
        """Delete balance records by account ID."""
        ...


class NetWorthRepository(Protocol):
    """Protocol for net worth repository operations."""

    def get(self, month: Month, currency_code: str = "USD") -> NetWorth:
        """Get net worth value for given month and currency."""
        ...

    def history(self, currency_code: str = "USD") -> list[NetWorth]:
        """Get net worth history for a given currency."""
        ...


class SQLiteCurrenciesRepository(BaseRepository[Currency]):
    """Repository for currencies SQLite database operations."""

    def insert_many(self, data: list[Currency]) -> None:
        """Insert list of currencies into the currencies table.

        Args:
            data (list[Currency]): List of Currency objects.
        """
        rowcount = self._db.execute_many(
            "INSERT INTO currencies (code, description) VALUES (:code, :description);",
            [self._mapper.to_record(entity) for entity in data],
        )
        print("Inserted", rowcount, "currency rows.")

    def get(self, code: str) -> Currency | None:
        """Get currency by code.

        Args:
            code (str): Currency code.

        Returns:
            Currency | None: Currency record if found, else None.
        """
        query = "SELECT code, description FROM currencies WHERE code = :code;"
        result = self._db.fetch_one(query, {"code": code})
        if result:
            return self._mapper.to_entity(result)
        else:
            return None

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
        currencies = [self._mapper.to_entity(record) for record in results]
        return currencies

    def get_dict(self) -> dict[str, Currency]:
        """Get all currencies in a dictionary indexed by code.

        Returns:
            dict[str, Currency]: Dictionary of currency records indexed by code.
        """
        results = self.get_all()
        currencies = {result.code: result for result in results}
        return currencies

    def count(self) -> int:
        """Count the number of currency records.

        Returns:
            int: Number of currency records.
        """
        query = "SELECT COUNT(*) AS cnt FROM currencies;"
        result = self._db.fetch_one(query)
        return result["cnt"] if result else 0

    def delete_all(self) -> None:
        """Delete all currency records."""
        query = "DELETE FROM currencies;"
        cur = self._db.execute(query)
        print(f"Deleted {cur.rowcount} currency records.")


class SQLiteCategoriesRepository(BaseRepository[Category]):
    """Repository for category SQLite database operations."""

    def insert_many(self, data: list[Category]) -> None:
        """Insert list of categories into SQLite database.

        Args:
            data (list[Category]): List of category data dictionaries.
        """
        rowcount = self._db.execute_many(
            "INSERT INTO categories (name, side) VALUES (:name, :side);",
            [self._mapper.to_record(record) for record in data],
        )
        print("Inserted", rowcount, "category rows.")

    def get(self, name: str) -> Category | None:
        """Get category by name.

        Args:
            name (str): Category name.

        Returns:
            Category | None: Category object if found, else None.
        """
        query = "SELECT name, side FROM categories WHERE name = :name;"
        result = self._db.fetch_one(query, {"name": name})
        if result:
            return self._mapper.to_entity(result)
        else:
            return None

    def get_all(self) -> list[Category]:
        """Get all Categories.

        Returns:
            list[Category]: List of category objects.
        """
        query = "SELECT name, side FROM categories;"
        results = self._db.fetch_all(query)
        return [self._mapper.to_entity(record) for record in results]

    def get_dict(self) -> dict[str, Category]:
        """Get all categories in a dictionary indexed by code.

        Returns:
            dict[str, Category]: Dictionary of categories records indexed by name.
        """
        results = self.get_all()
        categories = {result.name: result for result in results}
        return categories

    def count(self) -> int:
        """Count the number of category records.

        Returns:
            int: Number of category records.
        """
        query = "SELECT COUNT(*) AS cnt FROM categories;"
        result = self._db.fetch_one(query)
        return result["cnt"] if result else 0

    def delete_all(self) -> None:
        """Delete all category records."""
        query = "DELETE FROM categories;"
        cur = self._db.execute(query)
        print(f"Deleted {cur.rowcount} category records.")


class SQLiteAccountsRepository(BaseRepository[Account]):
    """Repository for account SQLite database operations."""

    def insert(self, data: Account) -> None:
        """Insert account object in respective table.

        Args:
            data (Account): Account objects
        """
        query = """
        INSERT INTO accounts (name, description, category, currency, status)
        VALUES (:name, :description, :category, :currency, :status);
        """
        cur = self._db.execute(query, self._mapper.to_record(data))
        print("Inserted", cur.rowcount, "account")
        return cur.rowcount

    def insert_many(self, data: list[Account]) -> None:
        """Insert list of accounts into the accounts table.

        Args:
            data (list[Account]): List of Account objects
        """
        query = """
        INSERT INTO accounts (name, description, category, currency, status)
        VALUES (:name, :description, :category, :currency, :status);
        """
        rowcount = self._db.execute_many(
            query,
            [self._mapper.to_record(acc) for acc in data],
        )
        print("Inserted", rowcount, "account rows.")

    def get_by_id(self, account_id: int) -> Account | None:
        """Get account by ID.

        Args:
            account_id (int): Account ID

        Returns:
            Account | None: Account object if found, else None
        """
        query = """
        SELECT id, name, description, category, currency, status
        FROM accounts
        WHERE id = :account_id;
        """
        result = self._db.fetch_one(query, {"account_id": account_id})
        if result:
            return self._mapper.to_entity(dict(result))
        else:
            return None

    def get_by_name(self, account_name: str) -> Account | None:
        """Get account by name.

        Args:
            account_name (str): Account name

        Returns:
            Account | None: Account object if found, else None
        """
        query = """
        SELECT id, name, description, category, currency, status
        FROM accounts
        WHERE name = :account_name;
        """
        result = self._db.fetch_one(query, {"account_name": account_name})
        if result:
            return self._mapper.to_entity(dict(result))
        else:
            return None

    def get_active(self) -> list[Account]:
        """Get all active accounts."""
        query = """
        SELECT id, name, description, category, currency, status
        FROM accounts
        WHERE status = 'active';
        """
        results = self._db.fetch_all(query)
        return [self._mapper.to_entity(dict(record)) for record in results]

    def get_all(self) -> list[Account]:
        """Get all accounts.

        Returns:
            list[Account]: List of account objects.
        """
        query = """
        SELECT id, name, description, category, currency, status
        FROM accounts;
        """
        results = self._db.fetch_all(query)
        return [self._mapper.to_entity(dict(record)) for record in results]

    def get_dict_id(self) -> dict[int, Account]:
        """Get all accounts in a dictionary indexed by accoun id.

        Returns:
            dict[int, Account]: Dictionary of account records indexed by id.
        """
        results = self.get_all()
        return {result.id: result for result in results}

    def get_dict_name(self) -> dict[str, Account]:
        """Get all accounts in a dictionary indexed by name.

        Returns:
            dict[str, Account]: Dictionary of account records indexed by name.
        """
        results = self.get_all()
        return {result.name: result for result in results}

    def count(self) -> int:
        """Count the number of account records.

        Returns:
            int: Number of account records.
        """
        query = "SELECT COUNT(*) AS cnt FROM accounts;"
        result = self._db.fetch_one(query)
        return result["cnt"] if result else 0

    def delete_all(self) -> None:
        """Delete all account records."""
        query = "DELETE FROM accounts;"
        cur = self._db.execute(query)
        print(f"Deleted {cur.rowcount} account records.")

    def delete_by_id(self, account_id: int) -> int:
        """Delete account by ID.

        Args:
            account_id (int): Account ID
        Returns:
            int: Number of deleted account entries.
        """
        query = "DELETE FROM accounts WHERE id = :account_id;"
        cur = self._db.execute(query, {"account_id": account_id})
        rowcount = cur.rowcount
        print(f"Deleted {rowcount} account entry with ID {account_id}.")
        return rowcount

    def update_name(self, account_id: int, new_name: str) -> int:
        """Update account name.

        Args:
            account_id (int): The account ID.
            new_name (str): The new name value.

        Returns:
            int: Number of updated account entries.
        """
        update_query = """
        UPDATE accounts
        SET name = :name
        WHERE id = :account_id;
        """
        params: dict[str, str | int] = {
            "name": new_name,
            "account_id": account_id,
        }
        cur = self._db.execute(update_query, params)
        rowcount = cur.rowcount
        assert rowcount == 1, "Expected exactly one row to be updated."
        print(f"Updated account {account_id} to name '{new_name}'.")
        return rowcount

    def update_status(self, account_id: int, new_status: str) -> int:
        """Update account status.

        Args:
            account_id (int): The account ID.
            new_status (str): The new status value.

        Returns:
            int: Number of updated account entries.
        """
        update_query = """
        UPDATE accounts
        SET status = :status
        WHERE id = :account_id;
        """
        params: dict[str, str | int] = {
            "status": new_status,
            "account_id": account_id,
        }
        cur = self._db.execute(update_query, params)
        rowcount = cur.rowcount
        assert rowcount == 1, "Expected exactly one row to be updated."
        print(f"Updated account {account_id} to status '{new_status}'.")
        return rowcount

    def update_currency(self, account_id: int, new_currency_code: str) -> int:
        """Update account currency.

        Args:
            account_id (int): The account ID.
            new_currency_code (str): The new currency code.

        Returns:
            int: Number of updated account entries.
        """
        update_query = """
        UPDATE accounts
        SET currency = :currency
        WHERE id = :account_id;
        """
        params: dict[str, str | int] = {
            "currency": new_currency_code,
            "account_id": account_id,
        }
        cur = self._db.execute(update_query, params)
        rowcount = cur.rowcount
        assert rowcount == 1, "Expected exactly one row to be updated."
        print(f"Updated account {account_id} to currency '{new_currency_code}'.")
        return rowcount

    def update_category(self, account_id: int, new_category_name: str) -> int:
        """Update account category.

        Args:
            account_id (int): The account ID.
            new_category_name (str): The new category name.

        Returns:
            int: Number of updated account entries.
        """
        update_query = """
        UPDATE accounts
        SET category = :category
        WHERE id = :account_id;
        """
        params: dict[str, str | int] = {
            "category": new_category_name,
            "account_id": account_id,
        }
        cur = self._db.execute(update_query, params)
        rowcount = cur.rowcount
        assert rowcount == 1, "Expected exactly one row to be updated."
        print(f"Updated account {account_id} to category '{new_category_name}'.")
        return rowcount

    def update_description(self, account_id: int, new_description: str) -> int:
        """Update account description.

        Args:
            account_id (int): The account ID.
            new_description (str): The new description.

        Returns:
            int: Number of updated account entries.
        """
        update_query = """
        UPDATE accounts
        SET description = :description
        WHERE id = :account_id;
        """
        params: dict[str, str | int] = {
            "description": new_description,
            "account_id": account_id,
        }
        cur = self._db.execute(update_query, params)
        rowcount = cur.rowcount
        assert rowcount == 1, "Expected exactly one row to be updated."
        print(f"Updated account {account_id} description.")
        return rowcount


class SQLiteBalancesRepository(BaseRepository[Balance]):
    """Repository for balances SQLite database operations."""

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
            [self._mapper.to_record(bal) for bal in data],
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
        # TODO: Rename to get_by_account_name
        query = """
        SELECT b.id, b.account_id, b.month, a.name, b.amount
        FROM accounts a
        JOIN balances b ON a.id = b.account_id
        WHERE b.month = :month AND a.name = :account_name;
        """
        results = self._db.fetch_all(
            query, {"month": str(month), "account_name": account_name}
        )
        assert len(results) <= 1, "Expected at most one balance record."
        return self._mapper.to_entity(dict(results[0]))

    def get_by_account_id(self, month: Month, account_id: int) -> Balance:
        """Get all balances given account id and month.

        Args:
            month (Month): Month object
            account_d (int): Account int

        Returns:
            Balance: Account balance record
        """
        query = """
        SELECT id, account_id, month, amount
        FROM balances
        WHERE month = :month AND account_id = :account_id;
        """
        results = self._db.fetch_all(
            query, {"month": str(month), "account_id": account_id}
        )
        assert len(results) <= 1, "Expected at most one balance record."
        return self._mapper.to_entity(dict(results[0]))

    def get_all_by_account_id(self, account_id: int) -> list[Balance]:
        """Get all balances given account id.

        Args:
            account_id (int): Account int

        Returns:
            list[Balance]: List of account balance records
        """
        query = """
        SELECT id, account_id, month, amount
        FROM balances
        WHERE account_id = :account_id
        ORDER BY month;
        """
        results = self._db.fetch_all(query, {"account_id": account_id})
        return [self._mapper.to_entity(dict(res)) for res in results]

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
            SELECT b.id, b.account_id, b.month, a.name, b.amount
            FROM accounts a
            JOIN balances b ON a.id = b.account_id
            WHERE b.month = :month AND a.status = 'active';
            """
        else:
            query = """
            SELECT b.id, b.account_id, b.month, a.name, b.amount
            FROM accounts a
            JOIN balances b ON a.id = b.account_id
            WHERE b.month = :month;
            """
        results = self._db.fetch_all(query, {"month": str(month)})
        return [self._mapper.to_entity(dict(res)) for res in results]

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
        return [self._mapper.to_entity(dict(res)) for res in results]

    def count(self) -> int:
        """Count the number of balance records.

        Returns:
            int: Number of balance records.
        """
        query = "SELECT COUNT(*) AS cnt FROM balances;"
        result = self._db.fetch_one(query)
        return result["cnt"] if result else 0

    def delete_all(self) -> None:
        """Delete all balance records."""
        query = "DELETE FROM balances;"
        cur = self._db.execute(query)
        print(f"Deleted {cur.rowcount} balance records.")

    def delete_by_account_id(self, account_id: int) -> int:
        """Delete balance records by account ID.

        Args:
            account_id (int): Account ID
        Returns:
            int: Number of deleted balance records.
        """
        query = "DELETE FROM balances WHERE account_id = :account_id;"
        cur = self._db.execute(query, {"account_id": account_id})
        rowcount = cur.rowcount
        print(f"Deleted {rowcount} balance records for account ID {account_id}.")
        return rowcount


class SQLiteExchangeRatesRepository(BaseRepository[ExchangeRate]):
    """Repository for exchange rates SQLite database operations."""

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
            [self._mapper.to_record(record) for record in data],
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
        SELECT currency, month, rate FROM exchange_rates
        WHERE currency = :currency AND month = :month;
        """
        result = self._db.fetch_one(
            query, {"currency": currency_code, "month": str(month)}
        )
        if result:
            return self._mapper.to_entity(dict(result))
        else:
            return None

    def get_currency(self, currency_code: str) -> list[ExchangeRate]:
        """Get exchange rates for a given currency code

        Args:
            currency_code (str): Currency code

        Returns:
            list[ExchangeRate]: List of exchange rate records
        """
        query = """
        SELECT currency, month, rate FROM exchange_rates
        WHERE currency = :currency;
        """
        results = self._db.fetch_all(query, {"currency": currency_code})
        return [self._mapper.to_entity(dict(res)) for res in results]

    def get_month(self, month: Month) -> list[ExchangeRate]:
        """Get exchange rates for all currencies for a given month

        Args:
            month (Month): Month object

        Returns:
            list[ExchangeRate]: List of exchange rate records
        """
        query = """
        SELECT currency, month, rate FROM exchange_rates
        WHERE month = :month;
        """
        results = self._db.fetch_all(query, {"month": str(month)})
        return [self._mapper.to_entity(dict(res)) for res in results]

    def count(self) -> int:
        """Count the number of exchange rate records.

        Returns:
            int: Number of exchange rage records.
        """
        query = "SELECT COUNT(*) AS cnt FROM exchange_rates;"
        result = self._db.fetch_one(query)
        return result["cnt"] if result else 0

    def delete_all(self) -> None:
        """Delete all category records."""
        query = "DELETE FROM exchange_rates;"
        cur = self._db.execute(query)
        print(f"Deleted {cur.rowcount} exchange rate records.")


class SQLiteNetWorthRepository:
    """Repository net worth operations."""

    def __init__(self, db: DBConnectionManager, mapper: NetWorthMapper) -> None:
        self._db: DBConnectionManager = db
        self._mapper: NetWorthMapper = mapper

    def get(self, month: Month, currency_code: str = "USD") -> NetWorth:
        """Get net worth value for given month and currency

        Args:
            month (Month): The month to query net worth.
            currency_code (str, optional): The currency code. Defaults to "USD".

        Returns:
            NetWorth: Net worth record.
        """
        query = """
        SELECT month, total_assets, total_liabilities, net_worth, currency
        FROM networth_history
        WHERE month = :month AND currency = :currency;
        """
        results = self._db.fetch_all(
            query, {"month": str(month), "currency": currency_code}
        )
        assert len(results) <= 1, "Expected at most one net worth record."
        return self._mapper.to_entity(dict(results[0]))

    def history(self, currency_code: str = "USD") -> list[NetWorth]:
        """Get net worth history for a given currency.
        Args:
            currency_code (str, optional): The currency code. Defaults to "USD".

        Returns:
            list[NetWorth]: List of Net Worth records.
        """
        query = """
        SELECT month, total_assets, total_liabilities, net_worth, currency
        FROM networth_history
        WHERE currency = :currency
        ORDER BY month;
        """
        results = self._db.fetch_all(query, {"currency": currency_code})
        return [self._mapper.to_entity(dict(record)) for record in results]
