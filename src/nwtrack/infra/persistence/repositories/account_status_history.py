"""SQLAlchemy repository for account status history."""

import logging
from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from nwtrack.domain.value_objects import Month
from nwtrack.infra.persistence.orm.models import AccountStatusHistory, Status

logger = logging.getLogger(__name__)


class AccountStatusHistoryRepository:
    """Repository for AccountStatusHistory records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def insert(self, entry: AccountStatusHistory) -> int:
        """Insert one history row and return its generated id."""
        self._session.add(entry)
        self._session.flush()
        return entry.id

    def insert_many(self, entries: list[AccountStatusHistory]) -> None:
        """Insert multiple history rows in bulk."""
        for entry in entries:
            self._session.add(entry)
        self._session.flush()

    def get_all(self) -> list[AccountStatusHistory]:
        """Return all history rows ordered by account_id then effective_month."""
        return list(
            self._session.execute(
                select(AccountStatusHistory).order_by(
                    AccountStatusHistory.account_id,
                    AccountStatusHistory.effective_month,
                )
            ).scalars()
        )

    def get_effective_status(
        self, account_id: int, month: Month
    ) -> Status | None:
        """Return the effective status for an account at a given month.

        Returns the status from the row with the greatest effective_month
        that is <= the requested month, or None if no such row exists.
        """
        result = self._session.execute(
            select(AccountStatusHistory.status)
            .where(AccountStatusHistory.account_id == account_id)
            .where(AccountStatusHistory.effective_month <= month)
            .order_by(AccountStatusHistory.effective_month.desc())
            .limit(1)
        ).scalar_one_or_none()
        return result

    def hydrate(self, record: Mapping[str, Any]) -> AccountStatusHistory:
        """Convert a dict record into an AccountStatusHistory instance."""
        entry = AccountStatusHistory(
            account_id=int(record["account_id"]),
            status=Status(record["status"]),
            effective_month=Month.parse(str(record["effective_month"])),
        )
        raw_id = record.get("id")
        if raw_id is not None and int(raw_id) > 0:
            entry.id = int(raw_id)
        return entry

    def hydrate_many(
        self, records: list[Mapping[str, Any]]
    ) -> list[AccountStatusHistory]:
        """Convert a list of dict records into AccountStatusHistory instances."""
        return [self.hydrate(r) for r in records]
