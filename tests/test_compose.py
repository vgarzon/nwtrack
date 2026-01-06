"""
Test container composition root
"""

import pytest

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.config import Config
from nwtrack.container import Container, Lifetime
from nwtrack.infra.sqlite.uow import SQLiteUnitOfWork
from nwtrack.repo_registry import RepositoryRegistry


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Configure container for test suite."""
    return base_container


def test_build_basic_services_container(configured_container):
    """Test building the SQLite UoW container."""
    assert configured_container is not None
    assert isinstance(configured_container, Container)


def test_resolve_config(configured_container, base_config):
    """Test resolving Config from the configured_container."""
    config = configured_container.resolve(Config)
    assert config is not None
    assert isinstance(config, Config)
    assert config.db_file_path == base_config.db_file_path
    assert config.db_ddl_path == base_config.db_ddl_path


def test_overwrite_config(configured_container, base_config: Config):
    """Test re-registering Config from the configured_container."""
    configured_container.register(
        Config,
        lambda _: base_config,
        lifetime=Lifetime.SINGLETON,
    )
    cfg: Config = configured_container.resolve(Config)
    assert cfg is not None
    assert isinstance(cfg, Config)
    assert cfg.db_file_path == base_config.db_file_path
    assert cfg.db_ddl_path == base_config.db_ddl_path


def test_resolve_uow(configured_container):
    """Test resolving UnitOfWork from the configured_container."""
    uow = configured_container.resolve(UnitOfWork)
    assert uow is not None
    assert isinstance(uow, SQLiteUnitOfWork)
    assert hasattr(uow, "_db")
    assert hasattr(uow, "_repos")


def test_mapper_registry_in_uow(configured_container):
    """Test that MapperRegistry is correctly set in SQLiteUnitOfWork."""
    uow = configured_container.resolve(UnitOfWork)
    assert uow is not None
    assert hasattr(uow, "_mappers")
    # NOTE: This works because MapperRegistry is a concrete implementation
    assert isinstance(
        uow._mappers, configured_container.resolve(type(uow._mappers)).__class__
    )
    assert uow._mappers is configured_container.resolve(type(uow._mappers))


def test_repository_registry_in_uow(configured_container):
    """Test that RepositoryRegistry is correctly set in SQLiteUnitOfWork."""
    uow = configured_container.resolve(UnitOfWork)
    assert uow is not None
    assert hasattr(uow, "_repos")
    assert uow._repos is configured_container.resolve(RepositoryRegistry)
