"""
Test DBInitializerCSV class methods.
"""

import pytest

import nwtrack.application.use_cases.init_db_csv
import nwtrack.entrypoints.cli.adapters.db_admin_presenters
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases.init_db_csv import DBInitializerCSV
from nwtrack.bootstrap.container import Container


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register additional services required for tests."""
    from nwtrack.application.ports.presentation import DBInitCSVPresenter
    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.services.data_loader import InitDataService
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.entrypoints.cli.adapters.db_admin_presenters import (
        Console,
        RichDBInitCSVPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings
    from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory
    from nwtrack.infra.config.settings import Settings
    from nwtrack.infra.sqlite.sqlalchemy_manager import SQLAlchemySessionManager
    from nwtrack.infra.sqlite.sqlalchemy_schema_manager import SQLAlchemySchemaManager

    console_defaults = ConsoleSettings(record=True)

    return (
        base_container.register(
            SchemaManager,
            lambda c: SQLAlchemySchemaManager(
                engine=c.resolve(SQLAlchemySessionManager).engine
            ),
        ).register(
            DBAdminService,
            lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
        )
        .register(
            InitDataService,
            lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            Console,
            lambda c: ConsoleFactory(default_settings=console_defaults)(),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            DBInitCSVPresenter,
            lambda c: RichDBInitCSVPresenter(console=c.resolve(Console)),
        )
        .register(
            DBInitializerCSV,
            lambda c: DBInitializerCSV(
                config=c.resolve(Settings),
                admin_svc=c.resolve(DBAdminService),
                data_svc=c.resolve(InitDataService),
                presenter=c.resolve(DBInitCSVPresenter),
            ),
        )
    )


@pytest.fixture
def valid_file_paths() -> dict[str, str]:
    """Mapping of table names to CSV file paths for tests."""
    return {
        "currencies": "tests/data/csv/currencies.csv",
        "categories": "tests/data/csv/categories.csv",
        "accounts": "tests/data/csv/accounts.csv",
        "balances": "tests/data/csv/balances.csv",
        "exchange_rates": "tests/data/csv/exchange_rates.csv",
    }


def test_db_initializer_csv_yes(
    configured_container, monkeypatch, valid_file_paths
) -> None:
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.db_admin_presenters.RichDBInitCSVPresenter,
        "prompt_for_file_paths",
        lambda *args, **kwargs: valid_file_paths,
    )

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.db_admin_presenters.RichDBInitCSVPresenter,
        "prompt_for_confirmation",
        lambda *args, **kwargs: True,
    )
    service = configured_container.resolve(DBInitializerCSV)
    service.run()

    captured_out = service._presenter._console.export_text()
    assert "Database initialized successfully." in captured_out
    with configured_container.resolve(UnitOfWork) as uow:
        balances = uow.balances.get_all_by_account_id(1)
    assert len(balances) == 12
    assert balances[11].amount == 200


def test_db_initializer_csv_no(
    configured_container, monkeypatch, valid_file_paths
) -> None:
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.db_admin_presenters.RichDBInitCSVPresenter,
        "prompt_for_file_paths",
        lambda *args, **kwargs: valid_file_paths,
    )

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.db_admin_presenters.RichDBInitCSVPresenter,
        "prompt_for_confirmation",
        lambda *args, **kwargs: False,
    )
    service = configured_container.resolve(DBInitializerCSV)
    service.run()

    captured_out = service._presenter._console.export_text()
    print(captured_out)
    assert "Database initialization aborted by user" in captured_out
