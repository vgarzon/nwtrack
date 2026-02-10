"""
Test container composition root
"""

import pytest

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.infra.config.settings import Settings
from nwtrack.infra.persistence.uow import SQLAlchemyUnitOfWork


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


def test_resolve_uow(configured_container):
    """Test resolving UnitOfWork from the configured_container."""
    uow = configured_container.resolve(UnitOfWork)
    assert uow is not None
    assert isinstance(uow, SQLAlchemyUnitOfWork)
    assert hasattr(uow, "_session_factory")


def test_uow_has_repositories(configured_container):
    """Test that UnitOfWork provides access to all repositories."""

    # Create factory function that resolves UnitOfWork
    def uow_factory():
        return configured_container.resolve(UnitOfWork)

    with uow_factory() as uow:
        # Verify all repositories are accessible
        assert hasattr(uow, "currencies")
        assert hasattr(uow, "categories")
        assert hasattr(uow, "accounts")
        assert hasattr(uow, "balances")
        assert hasattr(uow, "exchange_rates")
        assert hasattr(uow, "net_worth")
