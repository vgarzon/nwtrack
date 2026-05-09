"""SQLAlchemy implementation of Institutions repository."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nwtrack.application.ports.repos import (
    InstitutionsRepository as InstitutionsRepositoryProtocol,
)
from nwtrack.infra.persistence.orm.models import Institution

logger = logging.getLogger(__name__)


class InstitutionsRepository(InstitutionsRepositoryProtocol):
    """SQLAlchemy-based repository for institution operations."""

    def __init__(self, session: Session):
        """Initialize repository with SQLAlchemy session."""
        self._session = session

    def insert(self, data: Institution) -> int:
        """Insert institution object in respective table."""
        try:
            self._session.add(data)
            self._session.flush()
            last_id = data.id
            logger.info("Inserted institution with ID %d", last_id)
            return last_id
        except IntegrityError as e:
            logger.exception("Institution insertion failed for '%s': %s", data.name, e)
            raise ValueError(f"Integrity Error for '{data.name}': {e}") from e

    def insert_many(self, data: list[Institution]) -> None:
        """Insert list of institutions into the institutions table."""
        self._session.add_all(data)
        self._session.flush()
        logger.info("Inserted %d institution rows.", len(data))

    def get_by_id(self, institution_id: int) -> Institution | None:
        """Get institution by ID."""
        return self._session.execute(
            select(Institution).where(Institution.id == institution_id)
        ).scalar_one_or_none()

    def get_by_name(self, institution_name: str) -> Institution | None:
        """Get institution by name."""
        return self._session.execute(
            select(Institution).where(Institution.name == institution_name)
        ).scalar_one_or_none()

    def get_all(self) -> list[Institution]:
        """Get all institutions."""
        result = self._session.execute(select(Institution)).scalars()
        return list(result)

    def count(self) -> int:
        """Count the number of institution records."""
        result = self._session.execute(
            select(func.count()).select_from(Institution)
        ).scalar()
        return result or 0

    def delete_all(self) -> None:
        """Delete all institution records."""
        result = self._session.execute(delete(Institution))
        logger.info("Deleted %d institution records.", result.rowcount)  # type: ignore[attr-defined]

    def hydrate(self, record: Mapping[str, Any]) -> Institution:
        """Hydrate record to Institution entity."""
        institution = Institution(
            name=record["name"],
            description=record.get("description") or None,
        )
        if "id" in record and int(record["id"]) > 0:
            institution.id = int(record["id"])
        return institution

    def hydrate_many(self, data: list[Mapping[str, Any]]) -> list[Institution]:
        """Hydrate list of records to list of Institution entities."""
        return [self.hydrate(record) for record in data]
