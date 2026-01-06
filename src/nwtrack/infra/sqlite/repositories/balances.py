"""
SQLite implementation of Balances repository.
"""

from __future__ import annotations

import sqlite3

from nwtrack.domain.models import Balance
from nwtrack.domain.value_objects import Month
from nwtrack.application.ports.repositories import BaseRepository


class SQLiteBalancesRepository(BaseRepository[Balance]):
    """Repository for balances SQLite database operations."""

    def insert(self, data: Balance) -> int:
        """Insert balance object in respective table.

        Args:
            data (Balance): Balance object

        Returns:
            int: last row id of inserted balance
        """
        query = """
        INSERT INTO balances (account_id, month, amount)
        VALUES (:account_id, :month, :amount);
        """
        try:
            cur = self._db.execute(query, self._mapper.to_record(data))
        except sqlite3.IntegrityError as e:
            print(
                f"Balance insertion failed for account_id '{data.account_id}' "
                f"on month '{data.month}': {e}"
            )
            raise ValueError(
                f"Integrity error for account_id '{data.account_id}' "
                f"on month '{data.month}': {e}"
            ) from e
        last_id = cur.lastrowid
        print("Inserted one balance with ID", last_id)
        return last_id

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

    def get_by_id(self, balance_id: int) -> Balance | None:
        """Get balance by ID.

        Args:
            balance_id (int): Balance ID

        Returns:
            Balance | None: Balance object if found, else None
        """
        query = """
        SELECT id, account_id, month, amount
        FROM balances
        WHERE id = :balance_id;
        """
        result = self._db.fetch_one(query, {"balance_id": balance_id})
        if result:
            return self._mapper.to_entity(dict(result))
        else:
            return None

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

    def copy_by_month(self, source_month: Month, target_month: Month) -> int:
        """Copy balances from one month to another.

        Args:
            source_month (Month): Source Month object
            target_month (Month): Target Month object

        Returns:
            int: Number of copied balance records.
        """
        insert_query = """
        INSERT OR IGNORE INTO balances (account_id, month, amount)
        SELECT account_id, :target_month, amount
        FROM balances
        WHERE month = :source_month;
        """
        params = {
            "source_month": str(source_month),
            "target_month": str(target_month),
        }
        cur = self._db.execute(insert_query, params)
        row_count = cur.rowcount
        print(f"Copied {row_count} balances from {source_month} to {target_month}.")
        return row_count

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

    def count_per_month(self) -> list[tuple[Month, int]]:
        """Count the number balance entries per month.

        Returns:
            tuple(Month, int): Month and number of balance entries for that month.
        """
        query = """
        SELECT month, COUNT(*) AS cnt
        FROM balances
        GROUP BY month
        ORDER BY month;
        """
        results = self._db.fetch_all(query)
        return [(Month.parse(record["month"]), record["cnt"]) for record in results]

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
