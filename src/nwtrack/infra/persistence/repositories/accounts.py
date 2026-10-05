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
            if data.display_order <= 0:
                data.display_order = self._max_display_order() + 1
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
        next_slot = self._max_display_order() + 1
        for account in data:
            if account.display_order <= 0:
                account.display_order = next_slot
            next_slot = max(next_slot, account.display_order) + 1
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
        """Get all active accounts ordered by display order.

        Returns:
            List of active account objects
        """
        result = self._session.execute(
            select(Account)
            .where(Account.status == Status.ACTIVE)
            .order_by(Account.display_order, Account.id)
        ).scalars()
        return list(result)

    def get_all(self) -> list[Account]:
        """Get all accounts ordered by display order.

        Returns:
            List of account objects
        """
        result = self._session.execute(
            select(Account).order_by(Account.display_order, Account.id)
        ).scalars()
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
            self._renumber_display_order()
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

    def move(self, account_id: int, direction: int) -> bool:
        """Swap an account's display slot with its neighbour.

        Args:
            account_id: The account ID
            direction: -1 to move up (earlier), +1 to move down (later)

        Returns:
            True if the account moved, False if it is already at the edge or
            does not exist
        """
        ordered = self.get_all()
        ids = [account.id for account in ordered]
        if account_id not in ids:
            return False
        index = ids.index(account_id)
        target = index + direction
        if not 0 <= target < len(ids):
            return False
        ids[index], ids[target] = ids[target], ids[index]
        self._assign_display_order(ids)
        logger.info("Moved account %d to display slot %d.", account_id, target + 1)
        return True

    def set_hidden(self, account_id: int, hidden: bool) -> int:
        """Set the hidden flag on an account.

        Args:
            account_id: The account ID
            hidden: Whether the account should be hidden from default lists

        Returns:
            Number of updated account entries
        """
        result = self._session.execute(
            update(Account).where(Account.id == account_id).values(is_hidden=hidden)
        )
        return result.rowcount or 0  # type: ignore[attr-defined]

    def _max_display_order(self) -> int:
        return (
            self._session.execute(select(func.max(Account.display_order))).scalar() or 0
        )

    def _renumber_display_order(self) -> None:
        """Close gaps so display_order is contiguous from 1."""
        self._assign_display_order([account.id for account in self.get_all()])

    def _assign_display_order(self, ordered_ids: list[int]) -> None:
        for slot, account_id in enumerate(ordered_ids, start=1):
            self._session.execute(
                update(Account)
                .where(Account.id == account_id)
                .values(display_order=slot)
            )
        # Entities already loaded in this session must not keep stale slots.
        self._session.expire_all()

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
            display_order=int(record.get("display_order") or 0),
            is_hidden=str(record.get("is_hidden", "")).strip().lower() in ("true", "1"),
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
        accounts = [self.hydrate(record) for record in data]
        # Records without a display slot (e.g. CSVs from before display order)
        # get sequential slots after any explicit ones, in record order.
        next_slot = max((a.display_order for a in accounts), default=0) + 1
        for account in accounts:
            if account.display_order <= 0:
                account.display_order = next_slot
                next_slot += 1
        return accounts
