"""
Test container composition root
"""

from nwtrack.compose import (
    build_base_sqlite_uow_container,
    build_data_services_container,
)
from nwtrack.container import Container
from nwtrack.config import Config, load_config
from nwtrack.container import Lifetime
from nwtrack.unitofwork import UnitOfWork, SQLiteUnitOfWork
from nwtrack.repo_registry import RepositoryRegistry


def build_test_container() -> Container:
    """Build a test container with basic services."""
    container = build_base_sqlite_uow_container()
    container = build_data_services_container(container)
    return container


def test_build_basic_services_container():
    """Test building the SQLite UoW container."""
    container = build_test_container()
    assert container is not None
    assert isinstance(container, Container)


def test_resolve_config():
    """Test resolving Config from the container."""
    container = build_test_container()
    config = container.resolve(Config)
    source_config = load_config()
    assert config is not None
    assert isinstance(config, Config)
    assert config.db_file_path == source_config.db_file_path
    assert config.db_ddl_path == source_config.db_ddl_path


def test_overwrite_config(test_config: Config):
    """Test re-registering Config from the container."""
    container = build_test_container()
    container.register(
        Config,
        lambda _: test_config,
        lifetime=Lifetime.SINGLETON,
    )
    cfg: Config = container.resolve(Config)
    assert cfg is not None
    assert isinstance(cfg, Config)
    assert cfg.db_file_path == test_config.db_file_path
    assert cfg.db_ddl_path == test_config.db_ddl_path


def test_resolve_uow():
    """Test resolving UnitOfWork from the container."""
    container = build_test_container()
    uow = container.resolve(UnitOfWork)
    assert uow is not None
    assert isinstance(uow, SQLiteUnitOfWork)
    assert hasattr(uow, "_db")
    assert hasattr(uow, "_repos")


def test_mapper_registry_in_uow():
    """Test that MapperRegistry is correctly set in SQLiteUnitOfWork."""
    container = build_test_container()
    uow = container.resolve(UnitOfWork)
    assert uow is not None
    assert hasattr(uow, "_mappers")
    # NOTE: This works because MapperRegistry is a concrete implementation
    assert isinstance(uow._mappers, container.resolve(type(uow._mappers)).__class__)
    assert uow._mappers is container.resolve(type(uow._mappers))


def test_repository_registry_in_uow():
    """Test that RepositoryRegistry is correctly set in SQLiteUnitOfWork."""
    container = build_test_container()
    uow = container.resolve(UnitOfWork)
    assert uow is not None
    assert hasattr(uow, "_repos")
    assert uow._repos is container.resolve(RepositoryRegistry)
