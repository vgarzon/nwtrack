"""
Repository Registry.

Collects repositories and mappers.  Passsed to Unit of Work in composition root.
"""

import logging
from typing import Any

from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.application.registries.mappers import MapperRegistry

logger = logging.getLogger(__name__)


class RepositoryRegistry:
    """Generic repository registry based on specified repositories and mappers."""

    def __init__(
        self,
        db: DBConnectionManager,
        mappers: MapperRegistry,
        specs: dict[str, tuple[type[Any], type[Any]]],
    ) -> None:
        """Initialize the Repository Registry with repository instances."""
        self._db = db
        self._mappers = mappers
        self._specs = specs
        self._instances: dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        """Dynamically get repository instances based on specs."""
        if name not in self._specs:
            logging.error("Repository '%s' not found in registry specs.", name)
            raise AttributeError(f"No repository registered with name: {name}")

        if name not in self._instances:
            entity_cls, repo_cls = self._specs[name]
            mapper = self._mappers.get_mapper_for(entity_cls)
            self._instances[name] = repo_cls(self._db, mapper)

        return self._instances[name]
