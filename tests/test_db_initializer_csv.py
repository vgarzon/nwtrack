"""
Test DBInitializerCSV class methods.
"""

import pytest

from nwtrack.admin import DBAdminService, SQLiteAdminService
from nwtrack.config import Config
from nwtrack.container import Container
from nwtrack.dbmanager import DBConnectionManager
from nwtrack.services import InitDataService
from nwtrack.unitofwork import UnitOfWork
from nwtrack.use_cases.db_initializer import DBInitializerCSV


def register_services(test_container: Container) -> Container:
    """Register additional services required for tests."""
    return (
        test_container.register(
            DBAdminService,
            lambda c: SQLiteAdminService(
                c.resolve(Config), c.resolve(DBConnectionManager)
            ),
        )
        .register(
            InitDataService,
            lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            DBInitializerCSV,
            lambda c: DBInitializerCSV(
                c.resolve(Config), c.resolve(DBAdminService), c.resolve(InitDataService)
            ),
        )
    )


def uow_factory(test_container: Container) -> UnitOfWork:
    """Factory to create UnitOfWork instances for tests."""
    return test_container.resolve(UnitOfWork)


def test_db_initializer_csv_yes(
    test_container, test_file_paths, monkeypatch, capsys
) -> None:
    container = register_services(test_container)
    db_initializer = container.resolve(DBInitializerCSV)
    inputs = iter(["YES"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    db_initializer.run(test_file_paths)
    captured = capsys.readouterr()
    assert "Database initialization complete." in captured.out
    with uow_factory(container) as uow:
        balances = uow.balances.get_all_by_account_id(1)
    assert len(balances) == 12
    assert balances[11].amount == 200


def test_db_initializer_csv_quit(
    test_container, test_file_paths, monkeypatch, capsys
) -> None:
    container = register_services(test_container)
    db_initializer = container.resolve(DBInitializerCSV)
    inputs = iter(["no"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    db_initializer.run(test_file_paths)
    captured = capsys.readouterr()
    assert "Quitting." in captured.out


def test_db_initializer_csv_missing_key(test_container, test_file_paths) -> None:
    container = register_services(test_container)
    db_initializer = container.resolve(DBInitializerCSV)
    incomplete_file_paths = test_file_paths.copy()
    del incomplete_file_paths["accounts"]

    with pytest.raises(KeyError) as exc_info:
        db_initializer.run(incomplete_file_paths)
    assert "Missing required file paths for keys" in str(exc_info.value)
    assert "accounts" in str(exc_info.value)


def test_db_initializer_csv_invalid_path(test_container, test_file_paths) -> None:
    container = register_services(test_container)
    db_initializer = container.resolve(DBInitializerCSV)
    invalid_file_paths = test_file_paths.copy()
    invalid_file_paths["accounts"] = "invalid/path/accounts.csv"

    with pytest.raises(FileNotFoundError) as exc_info:
        db_initializer.run(invalid_file_paths)
    assert "Path for 'accounts' is not a file" in str(exc_info.value)
    assert "invalid/path/accounts.csv" in str(exc_info.value)
