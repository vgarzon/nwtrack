"""
Test DBInitializerCSV class methods.
"""

import pytest

import nwtrack.application.use_cases.init_db_csv
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases.init_db_csv import DBInitializerCSV
from nwtrack.bootstrap.container import Container


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register additional services required for tests."""
    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.services.data_loader import InitDataService
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.use_cases.init_db_csv import Console
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.infra.config.settings import Settings

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
            Console,
            lambda c: Console(),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            DBInitializerCSV,
            lambda c: DBInitializerCSV(
                config=c.resolve(Settings),
                admin_svc=c.resolve(DBAdminService),
                data_svc=c.resolve(InitDataService),
                console=c.resolve(Console),
            ),
        )
    )


def _uow_factory(container: Container) -> UnitOfWork:
    """Factory to create UnitOfWork instances for tests."""
    return container.resolve(UnitOfWork)


def test_db_initializer_csv_yes(configured_container, monkeypatch, capsys) -> None:
    inputs_prompt = iter(
        [
            "tests/data/csv/currencies.csv",
            "tests/data/csv/categories.csv",
            "tests/data/csv/accounts.csv",
            "tests/data/csv/balances.csv",
            "tests/data/csv/exchange_rates.csv",
        ]
    )
    inputs_confirm = iter(["YES"])

    def mock_prompt(*args, **kwargs):
        return next(inputs_prompt)

    def mock_confirm(*args, **kwargs):
        return next(inputs_confirm)

    monkeypatch.setattr(
        nwtrack.application.use_cases.init_db_csv.Prompt, "ask", mock_prompt
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.init_db_csv.Confirm, "ask", mock_confirm
    )
    configured_container.resolve(DBInitializerCSV).run()
    captured = capsys.readouterr()
    assert "Database initialized successfully." in captured.out
    with _uow_factory(configured_container) as uow:
        balances = uow.balances.get_all_by_account_id(1)
    assert len(balances) == 12
    assert balances[11].amount == 200


def test_db_initializer_csv_file_path_quit(
    configured_container, monkeypatch, capsys
) -> None:
    inputs = iter(["q"])

    def mock_prompt(*args, **kwargs):
        return next(inputs)

    monkeypatch.setattr(
        nwtrack.application.use_cases.init_db_csv.Prompt, "ask", mock_prompt
    )
    configured_container.resolve(DBInitializerCSV).run()
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

    def mock_prompt(*args, **kwargs):
        return next(inputs)

    monkeypatch.setattr(
        nwtrack.application.use_cases.init_db_csv.Prompt,
        "ask",
        mock_prompt,
    )
    configured_container.resolve(DBInitializerCSV).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert f"Error: File not found: {invalid_path}" in captured.out
    assert "Stopping." in captured.out
