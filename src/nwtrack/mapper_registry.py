"""
Mapper Registry Module
"""

from typing import Any, TypeVar
from nwtrack.mappers import Mapper

TEntity = TypeVar("TEntity")


class MapperRegistry:
    """Mappers registry."""

    def __init__(self) -> None:
        """Initialize the Mapper Registry."""
        self._registry: dict[type[Any], Mapper[Any]] = {}

    def register(self, entity_cls: type[TEntity], mapper: Mapper[TEntity]) -> None:
        """Register a mapper for an entity class."""
        self._registry[entity_cls] = mapper

    def get_mapper_for(self, entity_cls: type[TEntity]) -> Mapper[TEntity]:
        """Programmatic lookup for the RepositoryRegistry."""

        try:
            return self._registry[entity_cls]
        except KeyError:
            raise ValueError(f"No mapper registered for entity: {entity_cls.__name__}")
