"""
SQLAlchemy implementation of Accounts repository.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nwtrack.application.ports.repos import (
    AccountsRepository as AccountsRepositoryProtocol,
)
from nwtrack.infra.persistence.orm.models import Account, Status

logger = logging.getLogger(__name__)


class AccountsRepository(AccountsRepositoryProtocol):
    """SQLAlchemy-based repository for accounts operations."""

    def __init__(self, session: Session):
        """Initialize repository with SQLAlchemy session.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self._session = session

    def insert(self, data: Account) -> int:
        """Insert account object in respective table.

        Args:
            data: Account object

        Returns:
            Last row id of inserted account
        """
        try:
            self._session.add(data)
            self._session.flush()
            last_id = data.id
            logger.info("Inserted account with ID %d", last_id)
            return last_id
        except IntegrityError as e:
            logger.exception(f"Account insertion failed for '{data.name}': {e}")
            raise ValueError(f"Integrity Error for '{data.name}': {e}") from e

    def insert_many(self, data: list[Account]) -> None:
        """Insert list of accounts into the accounts table.

        Args:
            data: List of Account objects
        """
        self._session.add_all(data)
        self._session.flush()
        logger.info("Inserted %d account rows.", len(data))

    def get_by_id(self, account_id: int) -> Account | None:
        """Get account by ID.

        Args:
            account_id: Account ID

        Returns:
            Account object if found, else None
        """
        return self._session.execute(
            select(Account).where(Account.id == account_id)
        ).scalar_one_or_none()

    def get_by_name(self, account_name: str) -> Account | None:
        """Get account by name.

        Args:
            account_name: Account name

        Returns:
            Account object if found, else None
        """
        return self._session.execute(
            select(Account).where(Account.name == account_name)
        ).scalar_one_or_none()

    def get_active(self) -> list[Account]:
        """Get all active accounts.

        Returns:
            List of active account objects
        """
        result = self._session.execute(
            select(Account).where(Account.status == Status.ACTIVE)
        ).scalars()
        return list(result)

    def get_all(self) -> list[Account]:
        """Get all accounts.

        Returns:
            List of account objects
        """
        result = self._session.execute(select(Account)).scalars()
        return list(result)

    def get_without_institution(self) -> list[Account]:
        """Get all accounts where institution_id is NULL, ordered by name.

        Returns:
            List of account objects with no institution assigned
        """
        result = self._session.execute(
            select(Account).where(Account.institution_id == None).order_by(Account.name)  # noqa: E711
        ).scalars()
        return list(result)

    def get_dict_id(self) -> dict[int, Account]:
        """Get all accounts in a dictionary indexed by account id.

        Returns:
            Dictionary of account records indexed by id
        """
        accounts = self.get_all()
        return {account.id: account for account in accounts}

    def get_dict_name(self) -> dict[str, Account]:
        """Get all accounts in a dictionary indexed by name.

        Returns:
            Dictionary of account records indexed by name
        """
        accounts = self.get_all()
        return {account.name: account for account in accounts}

    def count(self) -> int:
        """Count the number of account records.

        Returns:
            Number of account records
        """
        result = self._session.execute(
            select(func.count()).select_from(Account)
        ).scalar()
        return result or 0

    def delete_all(self) -> None:
        """Delete all account records."""
        result = self._session.execute(delete(Account))
        logger.info("Deleted %d account records.", result.rowcount)  # type: ignore[attr-defined]

    def delete_by_id(self, account_id: int) -> int:
        """Delete account by ID.

        Args:
            account_id: Account ID

        Returns:
            Number of deleted account entries
        """
        result = self._session.execute(delete(Account).where(Account.id == account_id))
        rowcount = result.rowcount or 0  # type: ignore[attr-defined]
        if rowcount != 1:
            logger.warning(
                "Expected to delete 1 account with ID %s, but deleted %s.",
                account_id,
                rowcount,
            )
        else:
            logger.info(f"Deleted account with ID {account_id}.")
        return rowcount

    def update(self, data: Account) -> int:
        """Update account record.

        Args:
            data: Account object with updated data

        Returns:
            Number of updated account entries
        """
        # Merge the detached entity back into the session
        merged = self._session.merge(data)
        self._session.flush()
        logger.info(f"Updated account with ID {merged.id}.")
        return 1

    def update_name(self, account_id: int, new_name: str) -> int:
        """Update account name.

        Args:
            account_id: The account ID
            new_name: The new name value

        Returns:
            Number of updated account entries
        """
        result = self._session.execute(
            update(Account).where(Account.id == account_id).values(name=new_name)
        )
        rowcount = result.rowcount or 0  # type: ignore[attr-defined]
        if rowcount != 1:
            logger.warning(
                "Expected to update 1 account with ID %s, but updated %s.",
                account_id,
                rowcount,
            )
        else:
            logger.info(f"Updated account {account_id} to name '{new_name}'.")
        return rowcount

    def update_status(self, account_id: int, new_status: str) -> int:
        """Update account status.

        Args:
            account_id: The account ID
            new_status: The new status value

        Returns:
            Number of updated account entries
        """
        result = self._session.execute(
            update(Account)
            .where(Account.id == account_id)
            .values(status=Status(new_status))
        )
        rowcount = result.rowcount or 0  # type: ignore[attr-defined]
        if rowcount != 1:
            logger.warning(
                "Expected to update 1 account with ID %s, but updated %s.",
                account_id,
                rowcount,
            )
        else:
            logger.info(f"Updated account {account_id} to status '{new_status}'.")
        return rowcount

    def update_currency(self, account_id: int, new_currency_code: str) -> int:
        """Update account currency.

        Args:
            account_id: The account ID
            new_currency_code: The new currency code

        Returns:
            Number of updated account entries
        """
        result = self._session.execute(
            update(Account)
            .where(Account.id == account_id)
            .values(currency_code=new_currency_code)
        )
        rowcount = result.rowcount or 0  # type: ignore[attr-defined]
        if rowcount != 1:
            logger.warning(
                "Expected to update 1 account with ID %s, but updated %s.",
                account_id,
                rowcount,
            )
        else:
            logger.info(
                f"Updated account {account_id} to currency '{new_currency_code}'."
            )
        return rowcount

    def update_category(self, account_id: int, new_category_name: str) -> int:
        """Update account category.

        Args:
            account_id: The account ID
            new_category_name: The new category name

        Returns:
            Number of updated account entries
        """
        result = self._session.execute(
            update(Account)
            .where(Account.id == account_id)
            .values(category_name=new_category_name)
        )
        rowcount = result.rowcount or 0  # type: ignore[attr-defined]
        if rowcount != 1:
            logger.warning(
                "Expected to update 1 account with ID %d, but updated %d.",
                account_id,
                rowcount,
            )
        else:
            logger.info(
                "Updated account %d to category '%s'.", account_id, new_category_name
            )
        return rowcount

    def update_description(self, account_id: int, new_description: str) -> int:
        """Update account description.

        Args:
            account_id: The account ID
            new_description: The new description

        Returns:
            Number of updated account entries
        """
        result = self._session.execute(
            update(Account)
            .where(Account.id == account_id)
            .values(description=new_description)
        )
        rowcount = result.rowcount or 0  # type: ignore[attr-defined]
        if rowcount != 1:
            logger.warning(
                "Expected to update 1 account with ID %d, but updated %d.",
                account_id,
                rowcount,
            )
        else:
            logger.info("Updated account %d description.", account_id)
        return rowcount

    def hydrate(self, record: Mapping[str, Any]) -> Account:
        """Hydrate record to Account entity.

        Args:
            record: Data dictionary

        Returns:
            Account object
        """
        account = Account(
            name=record["name"],
            description=record["description"],
            category_name=record["category"],
            institution_id=(
                int(record["institution_id"])
                if record.get("institution_id") not in (None, "")
                else None
            ),
            currency_code=record["currency"],
            status=Status(record["status"]),
        )
        # Set id after construction (init=False in ORM model)
        # Only set id if it's present and non-zero (0 means auto-generate)
        if "id" in record and int(record["id"]) > 0:
            account.id = int(record["id"])
        return account

    def hydrate_many(self, data: list[Mapping[str, Any]]) -> list[Account]:
        """Hydrate list of records to list of Account entities.

        Args:
            data: List of data dictionaries

        Returns:
            List of Account objects
        """
        return [self.hydrate(record) for record in data]
