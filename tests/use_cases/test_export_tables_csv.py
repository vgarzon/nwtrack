"""
Test use case to export database tables to CSV files.
"""

import textwrap

import pytest
from tests.helpers import init_db_tables_w_entities

import nwtrack.application.use_cases.export_tables_csv
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases.export_tables_csv import (
    ExportTablesCSVCLI,
    ExportTablesCSVInteractive,
)
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.domain.models import Account, Institution, Status, Tag


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
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

    return (
        base_container.register(
            Console,
            lambda c: Console(),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            SchemaManager,
            lambda c: SchemaManagerImpl(engine=c.resolve(SQLiteSessionManager).engine),
        )
        .register(
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
    assert "Skipped empty 'institutions' table." in captured.out
    assert "Skipped empty 'tags' table." in captured.out
    assert "Skipped empty 'account_tags' table." in captured.out

    for table_name in [
        "currencies",
        "categories",
        "accounts",
        "balances",
        "exchange_rates",
    ]:
        assert (tmp_path / f"{table_name}.csv").exists()
    assert not (tmp_path / "institutions.csv").exists()
    assert not (tmp_path / "tags.csv").exists()
    assert not (tmp_path / "account_tags.csv").exists()

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
        id,name,description,category,institution_id,currency,status
        1,bank_1_checking,bank_1 checking,checking,,USD,active
        2,bank_2_savings,bank_2_savings,savings,,USD,active
        3,credit_cards_1,credit_cards_1,revolving_credit,,USD,active
        4,mortgage_1,mortgage_1,mortgage,,USD,inactive
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


def test_export_accounts_csv_includes_institution_id_when_present(
    configured_container: Container,
    sample_entities: dict[str, list],
    tmp_path,
) -> None:
    """Account CSV output should include institution linkage in Phase 21."""
    from nwtrack.application.use_cases.export_tables_csv import ExportCSV

    init_db_tables_w_entities(configured_container, sample_entities)

    uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow:
        institution_id = uow.institutions.insert(
            Institution(name="Chase", description="Primary bank")
        )
        uow.accounts.insert(
            Account(
                name="phase10_export_account",
                description="Export compatibility check",
                category_name="checking",
                institution_id=institution_id,
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )

    exporter: ExportCSV = configured_container.resolve(ExportCSV)
    exporter.export_tables_to_dir(tmp_path)

    with open(tmp_path / "accounts.csv", encoding="utf-8") as f:
        accounts_csv = f.read().splitlines()

    assert accounts_csv[0] == (
        "id,name,description,category,institution_id,currency,status"
    )
    assert any(
        line == "5,phase10_export_account,Export compatibility check,checking,1,USD,active"
        for line in accounts_csv[1:]
    )


def test_export_tables_csv_includes_institutions_and_tags_when_present(
    configured_container: Container,
    sample_entities: dict[str, list],
    tmp_path,
) -> None:
    """Phase 21 should export institution, tag, and account-tag tables."""
    from nwtrack.application.use_cases.export_tables_csv import ExportCSV

    init_db_tables_w_entities(configured_container, sample_entities)
    uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow:
        uow.institutions.insert(
            Institution(name="Fidelity", description="Brokerage institution")
        )
        retirement_id = uow.tags.insert(
            Tag(name="retirement", description="Tax-advantaged")
        )
        liquid_id = uow.tags.insert(Tag(name="liquid", description="Cash-like"))
        uow.tags.replace_for_account(1, [liquid_id, retirement_id])
        uow.tags.replace_for_account(2, [retirement_id])

    exporter: ExportCSV = configured_container.resolve(ExportCSV)
    exporter.export_tables_to_dir(tmp_path)

    with open(tmp_path / "institutions.csv", encoding="utf-8") as f:
        institutions_csv = f.read().splitlines()
    assert institutions_csv == [
        "id,name,description",
        "1,Fidelity,Brokerage institution",
    ]

    with open(tmp_path / "tags.csv", encoding="utf-8") as f:
        tags_csv = f.read().splitlines()
    assert tags_csv == [
        "id,name,description",
        "1,retirement,Tax-advantaged",
        "2,liquid,Cash-like",
    ]

    with open(tmp_path / "account_tags.csv", encoding="utf-8") as f:
        account_tags_csv = f.read().splitlines()
    assert account_tags_csv == [
        "account_id,tag_id",
        "1,1",
        "1,2",
        "2,1",
    ]


def test_export_tables_cli_includes_richer_table_set(
    configured_container: Container,
    sample_entities: dict[str, list],
    tmp_path,
) -> None:
    """The non-interactive export path should write the richer Phase 21 table set."""
    from rich.console import Console

    from nwtrack.application.use_cases.export_tables_csv import ExportCSV

    init_db_tables_w_entities(configured_container, sample_entities)
    uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow:
        institution_id = uow.institutions.insert(
            Institution(name="Chase", description="Primary bank")
        )
        growth_id = uow.tags.insert(Tag(name="growth", description="Long-term"))
        income_id = uow.tags.insert(Tag(name="income", description="Income focused"))
        account = uow.accounts.get_by_id(1)
        assert account is not None
        account.institution_id = institution_id
        uow.accounts.update(account)
        uow.tags.replace_for_account(1, [income_id, growth_id])

    exporter: ExportCSV = configured_container.resolve(ExportCSV)
    console = Console(record=True)
    ExportTablesCSVCLI(exporter=exporter, console=console).run(
        target_dir=str(tmp_path),
        create=False,
    )

    for table_name in [
        "currencies",
        "categories",
        "institutions",
        "tags",
        "accounts",
        "account_tags",
        "balances",
        "exchange_rates",
    ]:
        assert (tmp_path / f"{table_name}.csv").exists()

    output = console.export_text()
    assert "Exported 1 'institutions' records" in output
    assert "Exported 2 'tags' records" in output
    assert "Exported 2 'account_tags' records" in output
