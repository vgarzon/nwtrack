"""
Test use case to export database tables to CSV files.
"""

import textwrap

import pytest
from tests.helpers import init_db_tables_w_entities

import nwtrack.application.use_cases.export_tables_csv
from nwtrack.application.use_cases.export_tables_csv import (
    ExportTablesCSVInteractive,
)
from nwtrack.bootstrap.container import Container, Lifetime


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.use_cases.export_tables_csv import (
        Console,
        ExportCSV,
    )
    from nwtrack.infra.config.settings import Settings
    from nwtrack.infra.sqlite.sqlalchemy_manager import SQLAlchemySessionManager
    from nwtrack.infra.sqlite.sqlalchemy_schema_manager import SQLAlchemySchemaManager

    return (
        base_container.register(
            Console,
            lambda c: Console(),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            SchemaManager,
            lambda c: SQLAlchemySchemaManager(
                engine=c.resolve(SQLAlchemySessionManager).engine
            ),
        ).register(
            DBAdminService,
            lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
        )
        .register(
            ExportCSV,
            lambda c: ExportCSV(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            ExportTablesCSVInteractive,
            lambda c: ExportTablesCSVInteractive(
                exporter=c.resolve(ExportCSV), console=c.resolve(Console)
            ),
        )
    )


def test_export_tables_interactive(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    # TODO: Use common fixture to init DB with entities
    input_prompt = iter([str(tmp_path)])
    input_confirm = iter(["y"])

    def mock_prompt(*args, **kwargs):
        return next(input_prompt)

    def mock_confirm(*args, **kwargs):
        return next(input_confirm)

    init_db_tables_w_entities(configured_container, sample_entities)
    defaults = {"target_dir": str(tmp_path), "create": True}
    monkeypatch.setattr(
        nwtrack.application.use_cases.export_tables_csv.Prompt,
        "ask",
        mock_prompt,
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.export_tables_csv.Confirm,
        "ask",
        mock_confirm,
    )
    configured_container.resolve(ExportTablesCSVInteractive).run(defaults)
    captured = capsys.readouterr()

    print(captured.out)

    for table_name in [
        "currencies",
        "categories",
        "accounts",
        "balances",
        "exchange_rates",
    ]:
        assert (tmp_path / f"{table_name}.csv").exists()

    currencies_expected = """
        code,description
        USD,United States Dollar
        CHF,Swiss Franc
        CNY,Chinese Yuan
     """
    categories_expected = """
        name,side
        checking,asset
        savings,asset
        mortgage,liability
        revolving_credit,liability
    """
    accounts_expected = """
        id,name,description,category,currency,status
        1,bank_1_checking,bank_1 checking,checking,USD,active
        2,bank_2_savings,bank_2_savings,savings,USD,active
        3,credit_cards_1,credit_cards_1,revolving_credit,USD,active
        4,mortgage_1,mortgage_1,mortgage,USD,inactive
    """

    currencies_expected = textwrap.dedent(currencies_expected).lstrip()
    categories_expected = textwrap.dedent(categories_expected).lstrip()
    accounts_expected = textwrap.dedent(accounts_expected).lstrip()

    with open(tmp_path / "currencies.csv", encoding="utf-8") as f:
        currencies_csv = f.read()
    assert currencies_csv == currencies_expected

    with open(tmp_path / "categories.csv", encoding="utf-8") as f:
        categories_csv = f.read()
    assert categories_csv == categories_expected

    with open(tmp_path / "accounts.csv", encoding="utf-8") as f:
        accounts_csv = f.read()
    assert accounts_csv == accounts_expected

    with open(tmp_path / "balances.csv", encoding="utf-8") as f:
        balances_csv = f.readlines()
    assert "id,account_id,month,amount\n" == balances_csv[0]
    assert "10,2,2024-08,2100\n" in balances_csv[:11]
