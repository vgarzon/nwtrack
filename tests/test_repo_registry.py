"""
Test repo registry functionality.
"""

import pytest
from typing import Any
from unittest.mock import Mock
from nwtrack.dbmanager import DBConnectionManager
from nwtrack.mapper_registry import MapperRegistry
from nwtrack.repo_registry import SQLiteRepositoryRegistry
from nwtrack.repos import Repository


def test_repository_registry():
    """Test RepositoryRegistry initializes repositories correctly."""
    db_mock = Mock(spec=DBConnectionManager)

    class EntityA:
        pass

    class EntityB:
        pass

    class MapperA:
        pass

    class MapperB:
        pass

    class RepoA(Repository):
        def __init__(self, db: DBConnectionManager, mapper: Any) -> None:
            pass

    class RepoB(Repository):
        def __init__(self, db: DBConnectionManager, mapper: Any) -> None:
            pass

    mapper_registry = MapperRegistry()
    mapper_registry.register(EntityA, MapperA())
    mapper_registry.register(EntityB, MapperB())

    specs = {
        "repo_a": (EntityA, RepoA),
        "repo_b": (EntityB, RepoB),
    }
    registry = SQLiteRepositoryRegistry(db_mock, mapper_registry, specs)

    assert hasattr(registry, "repo_a")
    assert hasattr(registry, "repo_b")
    with pytest.raises(AttributeError, match="No repository registered"):
        _ = registry.repo_c
