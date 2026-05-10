"""SQLAlchemy implementation of Tags repository."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from sqlalchemy import delete, distinct, func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nwtrack.application.ports.repos import TagsRepository as TagsRepositoryProtocol
from nwtrack.infra.persistence.orm.models import Tag, account_tags_table

logger = logging.getLogger(__name__)


class TagsRepository(TagsRepositoryProtocol):
    """SQLAlchemy-based repository for tag operations."""

    def __init__(self, session: Session):
        """Initialize repository with SQLAlchemy session."""
        self._session = session

    def insert(self, data: Tag) -> int:
        """Insert tag object in respective table."""
        try:
            self._session.add(data)
            self._session.flush()
            last_id = data.id
            logger.info("Inserted tag with ID %d", last_id)
            return last_id
        except IntegrityError as e:
            logger.exception("Tag insertion failed for '%s': %s", data.name, e)
            raise ValueError(f"Integrity Error for '{data.name}': {e}") from e

    def insert_many(self, data: list[Tag]) -> None:
        """Insert list of tags into the tags table."""
        self._session.add_all(data)
        self._session.flush()
        logger.info("Inserted %d tag rows.", len(data))

    def get_by_id(self, tag_id: int) -> Tag | None:
        """Get tag by ID."""
        return self._session.execute(
            select(Tag).where(Tag.id == tag_id)
        ).scalar_one_or_none()

    def get_by_name(self, tag_name: str) -> Tag | None:
        """Get tag by name."""
        return self._session.execute(
            select(Tag).where(Tag.name == tag_name)
        ).scalar_one_or_none()

    def get_all(self) -> list[Tag]:
        """Get all tags."""
        result = self._session.execute(select(Tag)).scalars()
        return list(result)

    def count(self) -> int:
        """Count the number of tag records."""
        result = self._session.execute(select(func.count()).select_from(Tag)).scalar()
        return result or 0

    def delete_all(self) -> None:
        """Delete all tag records."""
        result = self._session.execute(delete(Tag))
        logger.info("Deleted %d tag records.", result.rowcount)  # type: ignore[attr-defined]

    def update(self, data: Tag) -> int:
        """Update tag record."""
        merged = self._session.merge(data)
        self._session.flush()
        logger.info("Updated tag with ID %d.", merged.id)
        return 1

    def delete_by_id(self, tag_id: int) -> int:
        """Delete tag by ID."""
        result = self._session.execute(delete(Tag).where(Tag.id == tag_id))
        rowcount = result.rowcount or 0  # type: ignore[attr-defined]
        if rowcount != 1:
            logger.warning(
                "Expected to delete 1 tag with ID %s, but deleted %s.",
                tag_id,
                rowcount,
            )
        else:
            logger.info("Deleted tag with ID %d.", tag_id)
        return rowcount

    def count_linked_accounts(self, tag_id: int) -> int:
        """Count the number of accounts linked to a tag."""
        result = self._session.execute(
            select(func.count(distinct(account_tags_table.c.account_id))).where(
                account_tags_table.c.tag_id == tag_id
            )
        ).scalar()
        return result or 0

    def get_for_account(self, account_id: int) -> list[Tag]:
        """Get all tags linked to a specific account."""
        result = self._session.execute(
            select(Tag)
            .join(account_tags_table, account_tags_table.c.tag_id == Tag.id)
            .where(account_tags_table.c.account_id == account_id)
            .order_by(Tag.id)
        ).scalars()
        return list(result)

    def replace_for_account(self, account_id: int, tag_ids: list[int]) -> None:
        """Replace all tag associations for an account."""
        normalized_tag_ids = list(dict.fromkeys(tag_ids))
        self._session.execute(
            delete(account_tags_table).where(
                account_tags_table.c.account_id == account_id
            )
        )
        if normalized_tag_ids:
            self._session.execute(
                insert(account_tags_table),
                [
                    {"account_id": account_id, "tag_id": tag_id}
                    for tag_id in normalized_tag_ids
                ],
            )
        self._session.flush()

    def hydrate(self, record: Mapping[str, Any]) -> Tag:
        """Hydrate record to Tag entity."""
        tag = Tag(
            name=record["name"],
            description=record.get("description") or None,
        )
        if "id" in record and int(record["id"]) > 0:
            tag.id = int(record["id"])
        return tag

    def hydrate_many(self, data: list[Mapping[str, Any]]) -> list[Tag]:
        """Hydrate list of records to list of Tag entities."""
        return [self.hydrate(record) for record in data]
