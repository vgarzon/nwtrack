"""
SQLAlchemy implementation of Balances repository.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nwtrack.application.ports.repos import (
    BalancesRepository as BalancesRepositoryProtocol,
)
from nwtrack.domain.value_objects import Month
from nwtrack.infra.persistence.orm.models import Account, Balance, Status

logger = logging.getLogger(__name__)


class BalancesRepository(BalancesRepositoryProtocol):
    """SQLAlchemy-based repository for balances operations."""

    def __init__(self, session: Session):
        """Initialize repository with SQLAlchemy session.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self._session = session

    def insert(self, data: Balance) -> int:
        """Insert balance object in respective table.

        Args:
            data: Balance object

        Returns:
            Last row id of inserted balance
        """
        try:
            self._session.add(data)
            self._session.flush()
            last_id = data.id
            logger.info("Inserted one balance with ID %d", last_id)
            return last_id
        except IntegrityError as e:
            logger.exception(
                "Balance insertion failed for account_id '%d' on month '%s': %s",
                data.account_id,
                data.month,
                e,
            )
            raise ValueError(
                f"Integrity error for account_id '{data.account_id}' "
                f"on month '{data.month}': {e}"
            ) from e

    def insert_many(self, data: list[Balance]) -> None:
        """Insert list of balances into the balances table.

        Args:
            data: List of balance objects
        """
        self._session.add_all(data)
        self._session.flush()
        logger.info("Inserted %d balance rows.", len(data))

    def get(self, month: Month, account_name: str) -> Balance:
        """Get account balance on a specific month by account name.

        Args:
            month: Month object
            account_name: Account name

        Returns:
            Account balance record
        """
        results = list(
            self._session.execute(
                select(Balance)
                .join(Account, Balance.account_id == Account.id)
                .where(Balance.month == month, Account.name == account_name)
            ).scalars()
        )
        if len(results) > 1:
            logger.error(
                "Multiple balance records found for account '%s' on month '%s'.",
                account_name,
                month,
            )
            raise ValueError(
                f"Multiple balance records found for account '{account_name}' "
                f"on month '{month}'."
            )
        return results[0]

    def get_all(self) -> list[Balance]:
        """Get all balance records.

        Returns:
            List of all balance records
        """
        result = self._session.execute(
            select(Balance).order_by(Balance.month, Balance.account_id)
        ).scalars()
        return list(result)

    def get_by_id(self, balance_id: int) -> Balance | None:
        """Get balance by ID.

        Args:
            balance_id: Balance ID

        Returns:
            Balance object if found, else None
        """
        return self._session.execute(
            select(Balance).where(Balance.id == balance_id)
        ).scalar_one_or_none()

    def get_by_account_id(self, month: Month, account_id: int) -> Balance:
        """Get balance given account id and month.

        Args:
            month: Month object
            account_id: Account ID

        Returns:
            Account balance record
        """
        results = list(
            self._session.execute(
                select(Balance).where(
                    Balance.month == month, Balance.account_id == account_id
                )
            ).scalars()
        )
        if len(results) > 1:
            logger.error(
                "Multiple balance records found for account_id %d on month %s.",
                account_id,
                month,
            )
            raise ValueError(
                f"Multiple balance records found for account_id {account_id} "
                f"on month {month}."
            )
        return results[0]

    def get_all_by_account_id(self, account_id: int) -> list[Balance]:
        """Get all balances given account id.

        Args:
            account_id: Account ID

        Returns:
            List of account balance records
        """
        result = self._session.execute(
            select(Balance)
            .where(Balance.account_id == account_id)
            .order_by(Balance.month)
        ).scalars()
        return list(result)

    def get_month(self, month: Month, active_only: bool = True) -> list[Balance]:
        """Get all account balances on a specific month.

        Args:
            month: Month object
            active_only: Whether to include only active accounts

        Returns:
            List of account balances
        """
        query = (
            select(Balance)
            .join(Account, Balance.account_id == Account.id)
            .where(Balance.month == month)
        )
        if active_only:
            query = query.where(Account.status == Status.ACTIVE)

        result = self._session.execute(query).scalars()
        return list(result)

    def update(self, account_id: int, month: Month, new_amount: int) -> None:
        """Update the balance for specific account and month.

        Args:
            account_id: The account ID
            month: The month to the entry to update
            new_amount: The new balance amount
        """
        result = self._session.execute(
            update(Balance)
            .where(Balance.account_id == account_id, Balance.month == month)
            .values(amount=new_amount)
        )
        if result.rowcount != 1:  # type: ignore[attr-defined]
            logger.error(
                "Update affected %d rows for account_id %d on month %s.",
                result.rowcount,  # type: ignore[attr-defined]
                account_id,
                month,
            )
            raise ValueError(
                f"Update affected {result.rowcount} rows for account_id "  # type: ignore[attr-defined]
                f"{account_id} on month {month}."
            )
        else:
            logger.info(
                "Updated account_id %d on month %s with new amount %d.",
                account_id,
                month,
                new_amount,
            )

    def check_month(self, month: Month) -> bool:
        """Check that there are balance entries for a given month.

        Args:
            month: Month object

        Returns:
            True if the year and month exist, else False
        """
        result = self._session.execute(
            select(Balance.id).where(Balance.month == month).limit(1)
        ).first()
        return result is not None

    def roll_forward(self, month: Month) -> None:
        """Roll account balances forward from one month to the next.

        Args:
            month: Source Month object
        """
        next_month = month.increment()

        # Use raw SQL for INSERT OR IGNORE with SELECT
        sql = text("""
        INSERT OR IGNORE INTO balances (account_id, month, amount)
        SELECT account_id, :next_month, amount
        FROM balances
        WHERE month = :month
        """)
        result = self._session.execute(
            sql, {"month": str(month), "next_month": str(next_month)}
        )
        logger.info(
            "Rolled %d balances forward from %s to %s.",
            result.rowcount,  # type: ignore[attr-defined]
            month,
            next_month,
        )

    def copy_by_month(self, source_month: Month, target_month: Month) -> int:
        """Copy balances from one month to another.

        Args:
            source_month: Source Month object
            target_month: Target Month object

        Returns:
            Number of copied balance records
        """
        # Use raw SQL for INSERT OR IGNORE with SELECT
        sql = text("""
        INSERT OR IGNORE INTO balances (account_id, month, amount)
        SELECT account_id, :target_month, amount
        FROM balances
        WHERE month = :source_month
        """)
        result = self._session.execute(
            sql,
            {"source_month": str(source_month), "target_month": str(target_month)},
        )
        row_count = result.rowcount or 0  # type: ignore[attr-defined]
        logger.info(
            "Copied %d balances from %s to %s.", row_count, source_month, target_month
        )
        return row_count

    def fetch_sample(self, limit: int = 5) -> list[Balance]:
        """Fetch sample balance records for debugging.

        Args:
            limit: Number of sample records to fetch

        Returns:
            List of balance records
        """
        result = self._session.execute(select(Balance).limit(limit)).scalars()
        return list(result)

    def count(self) -> int:
        """Count the number of balance records.

        Returns:
            Number of balance records
        """
        result = self._session.execute(
            select(func.count()).select_from(Balance)
        ).scalar()
        return result or 0

    def count_per_month(self) -> list[tuple[Month, int]]:
        """Count the number balance entries per month.

        Returns:
            List of tuples (Month, count) for each month
        """
        results = self._session.execute(
            select(Balance.month, func.count())
            .group_by(Balance.month)
            .order_by(Balance.month)
        ).all()

        counts: list[tuple[Month, int]] = []
        for month, cnt in results:
            if month is None or cnt is None:
                logger.error("Encountered record with None values: %s, %s", month, cnt)
                continue
            counts.append((month, int(cnt)))
        return counts

    def count_for_month(self, month: Month) -> int:
        """Count the number of balance records for a specific month.

        Args:
            month: Month object

        Returns:
            Number of balance records for the month
        """
        result = self._session.execute(
            select(func.count()).select_from(Balance).where(Balance.month == month)
        ).scalar()
        return result or 0

    def delete_all(self) -> None:
        """Delete all balance records."""
        result = self._session.execute(delete(Balance))
        logger.info("Deleted %d balance records.", result.rowcount)  # type: ignore[attr-defined]

    def delete_by_account_id(self, account_id: int) -> int:
        """Delete balance records by account ID.

        Args:
            account_id: Account ID

        Returns:
            Number of deleted balance records
        """
        result = self._session.execute(
            delete(Balance).where(Balance.account_id == account_id)
        )
        rowcount = result.rowcount or 0  # type: ignore[attr-defined]
        logger.info(
            "Deleted %d balance records for account ID %d.", rowcount, account_id
        )
        return rowcount

    def delete_by_account_and_month(self, account_id: int, month: Month) -> int:
        """Delete balance record by account ID and month.

        Args:
            account_id: Account ID
            month: Month object

        Returns:
            Number of deleted rows (0 or 1 due to UNIQUE constraint)
        """
        result = self._session.execute(
            delete(Balance).where(
                Balance.account_id == account_id, Balance.month == month
            )
        )
        rowcount = result.rowcount or 0  # type: ignore[attr-defined]
        logger.info(
            "Deleted %d balance record(s) for account_id %d on month %s.",
            rowcount,
            account_id,
            month,
        )
        return rowcount

    def hydrate(self, record: Mapping[str, Any]) -> Balance:
        """Hydrate record to Balance entity.

        Args:
            record: Data dictionary

        Returns:
            Balance object
        """
        balance = Balance(
            account_id=int(record["account_id"]),
            month=Month.parse(record["month"])
            if isinstance(record["month"], str)
            else record["month"],
            amount=int(record["amount"]),
        )
        # Set id after construction (init=False in ORM model)
        # Only set id if it's present and non-zero (0 means auto-generate)
        if "id" in record and int(record["id"]) > 0:
            balance.id = int(record["id"])
        return balance

    def hydrate_many(self, data: list[Mapping[str, Any]]) -> list[Balance]:
        """Hydrate list of records to list of Balance entities.

        Args:
            data: List of data dictionaries

        Returns:
            List of Balance objects
        """
        return [self.hydrate(record) for record in data]
