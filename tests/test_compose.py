"""
Test container composition root
"""

import pytest

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.infra.config.settings import Settings
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.infra.sqlite.uow import SQLiteUnitOfWork
from nwtrack.application.registries.repos import RepositoryRegistry


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Configure container for test suite."""
    return base_container


def test_build_basic_services_container(configured_container):
    """Test building the SQLite UoW container."""
    assert configured_container is not None
    assert isinstance(configured_container, Container)


def test_resolve_config(configured_container, base_config):
    """Test resolving Settings from the configured_container."""
    config = configured_container.resolve(Settings)
    assert config is not None
    assert isinstance(config, Settings)
    assert config.db_file_path == base_config.db_file_path
    assert config.db_ddl_path == base_config.db_ddl_path


def test_overwrite_config(configured_container, base_config: Settings):
    """Test re-registering Settings from the configured_container."""
    configured_container.register(
        Settings,
        lambda _: base_config,
        lifetime=Lifetime.SINGLETON,
    )
    settings: Settings = configured_container.resolve(Settings)
    assert settings is not None
    assert isinstance(settings, Settings)
    assert settings.db_file_path == base_config.db_file_path
    assert settings.db_ddl_path == base_config.db_ddl_path


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
