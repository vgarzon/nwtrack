"""
Test container composition root
"""

from nwtrack.compose import build_sqlite_uow_container
from nwtrack.container import Container
from nwtrack.config import Config, load_config
from nwtrack.container import Lifetime
from nwtrack.unitofwork import UnitOfWork, SQLiteUnitOfWork


def test_build_sqlite_uow_container():
    """Test building the SQLite UoW container."""
    container = build_sqlite_uow_container()
    assert container is not None
    assert isinstance(container, Container)


def test_resolve_config():
    """Test resolving Config from the container."""
    container = build_sqlite_uow_container()
    config = container.resolve(Config)
    source_config = load_config()
    assert config is not None
    assert isinstance(config, Config)
    assert config.db_file_path == source_config.db_file_path
    assert config.db_ddl_path == source_config.db_ddl_path


def test_overwrite_config(test_config: Config):
    """Test re-registering Config from the container."""
    container = build_sqlite_uow_container()
    container.register(
        Config,
        lambda _: test_config,
        lifetime=Lifetime.SINGLETON,
    )
    cfg = container.resolve(Config)
    assert cfg is not None
    assert isinstance(cfg, Config)
    assert cfg.db_file_path == test_config.db_file_path
    assert cfg.db_ddl_path == test_config.db_ddl_path


def test_resolve_uow():
    """Test resolving UnitOfWork from the container."""
    container = build_sqlite_uow_container()
    uow = container.resolve(UnitOfWork)
    assert uow is not None
    assert isinstance(uow, SQLiteUnitOfWork)
    assert hasattr(uow, "_db")
    assert hasattr(uow, "_mappers")


def test_mapper_registry_in_uow():
    """Test that MapperRegistry is correctly set in SQLiteUnitOfWork."""
    container = build_sqlite_uow_container()
    uow = container.resolve(UnitOfWork)
    assert uow is not None
    assert hasattr(uow, "_mappers")
    assert uow._mappers is not None
    assert hasattr(uow._mappers, "currency")
    assert hasattr(uow._mappers, "category")
