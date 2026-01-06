"""
Test repo registry functionality.
"""

import pytest
from typing import Any
from tests.fakes import FakeEntityA, FakeEntityB
from nwtrack.dbmanager import DBConnectionManager
from nwtrack.application.registries.mappers import MapperRegistry
from nwtrack.application.registries.repos import RepositoryRegistry
from nwtrack.application.ports.repos import Repository


def test_repository_registry(
    mock_db_manager: DBConnectionManager, sample_mapper_registry: MapperRegistry
) -> None:
    """Test RepositoryRegistry initializes repositories correctly."""

    class RepoA(Repository):
        def __init__(self, db: DBConnectionManager, mapper: Any) -> None:
            pass

    class RepoB(Repository):
        def __init__(self, db: DBConnectionManager, mapper: Any) -> None:
            pass

    specs = {
        "repo_a": (FakeEntityA, RepoA),
        "repo_b": (FakeEntityB, RepoB),
    }
    registry = RepositoryRegistry(mock_db_manager, sample_mapper_registry, specs)

    assert hasattr(registry, "repo_a")
    assert hasattr(registry, "repo_b")
    with pytest.raises(AttributeError, match="No repository registered"):
        _ = registry.repo_c
