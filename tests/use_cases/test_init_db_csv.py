"""
Test DBInitializerCSV class methods.
"""

import pytest

from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.infra.config.settings import Settings
from nwtrack.bootstrap.container import Container
from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases.init_db_csv import DBInitializerCSV


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register additional services required for tests."""
    return (
        base_container.register(
            DBAdminService,
            lambda c: DBAdminService(
                c.resolve(Settings), c.resolve(DBConnectionManager)
            ),
        )
        .register(
            InitDataService,
            lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            DBInitializerCSV,
            lambda c: DBInitializerCSV(
                c.resolve(Settings),
                c.resolve(DBAdminService),
                c.resolve(InitDataService),
            ),
        )
    )


def _uow_factory(container: Container) -> UnitOfWork:
    """Factory to create UnitOfWork instances for tests."""
    return container.resolve(UnitOfWork)


def test_db_initializer_csv_yes(configured_container, monkeypatch, capsys) -> None:
    inputs = iter(
        [
            "tests/data/csv/currencies.csv",
            "tests/data/csv/categories.csv",
            "tests/data/csv/accounts.csv",
            "tests/data/csv/balances.csv",
            "tests/data/csv/exchange_rates.csv",
            "YES",
        ]
    )
    db_initializer: DBInitializerCSV = configured_container.resolve(DBInitializerCSV)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    db_initializer.run()
    captured = capsys.readouterr()
    assert "Database initialization complete." in captured.out
    with _uow_factory(configured_container) as uow:
        balances = uow.balances.get_all_by_account_id(1)
    assert len(balances) == 12
    assert balances[11].amount == 200


def test_db_initializer_csv_file_path_quit(
    configured_container, monkeypatch, capsys
) -> None:
    db_initializer: DBInitializerCSV = configured_container.resolve(DBInitializerCSV)
    inputs = iter(["q"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    db_initializer.run()
    captured = capsys.readouterr()
    assert "Stopping." in captured.out


def test_db_initializer_csv_invalid_path(
    configured_container, monkeypatch, capsys
) -> None:
    invalid_path = "invalid/path/accounts.csv"
    inputs = iter(
        [
            invalid_path,
            "q",
        ]
    )
    db_initializer: DBInitializerCSV = configured_container.resolve(DBInitializerCSV)

    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    db_initializer.run()
    captured = capsys.readouterr()
    assert f"Error: File not found at {invalid_path}" in captured.out
    assert "Stopping." in captured.out
