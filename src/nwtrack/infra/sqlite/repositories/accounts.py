"""
SQLite implementation of Accounts repository.
"""

from __future__ import annotations

import sqlite3

from nwtrack.domain.models import Account
from nwtrack.application.ports.repositories import BaseRepository


class SQLiteAccountsRepository(BaseRepository[Account]):
    """Repository for account SQLite database operations."""

    def insert(self, data: Account) -> int:
        """Insert account object in respective table.

        Args:
            data (Account): Account objects

        Returns:
            int: last row id of inserted account
        """
        query = """
        INSERT INTO accounts (name, description, category, currency, status)
        VALUES (:name, :description, :category, :currency, :status);
        """
        try:
            cur = self._db.execute(query, self._mapper.to_record(data))
        except sqlite3.IntegrityError as e:
            print(f"Account insertion failed for '{data.name}': {e}")
            raise ValueError(f"Integrity Error for '{data.name}': {e}") from e
        last_id = cur.lastrowid
        print("Inserted account with ID", last_id)
        return last_id

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
