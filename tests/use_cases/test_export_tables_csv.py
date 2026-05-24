"""
Test use case to export database tables to CSV files.
"""

import textwrap
from pathlib import Path

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases.export_tables_csv import (
    ExportTablesCSVCLI,
    ExportTablesCSVInteractive,
)
from nwtrack.bootstrap.container import Container
from nwtrack.domain.models import Account, Institution, Status, Tag


class MockExportTablesCSVPresenter:
    """Test double for ExportTablesCSVPresenter."""

    def __init__(
        self,
        target_dir_response: str = "",
        confirm_create: bool = False,
    ) -> None:
        self._target_dir_response = target_dir_response
        self._confirm_create = confirm_create
        self.header_shown = False
        self.cancellation_shown = False
        self.tables_exported: list[tuple[str, str, int]] = []
        self.tables_skipped: list[str] = []
        self.directories_created: list[Path] = []
        self.create_errors: list[tuple[Path, str]] = []
        self.not_found_errors: list[Path] = []
        self.not_a_dir_errors: list[Path] = []

    def show_header(self) -> None:
        self.header_shown = True

    def prompt_for_target_dir(self, default: str) -> str:
        return self._target_dir_response

    def confirm_create_directory(self, target_dir: str) -> bool:
        return self._confirm_create

    def show_creating_directory(self, target_dir: Path) -> None:
        self.directories_created.append(target_dir)

    def show_directory_create_error(self, target_dir: Path, message: str) -> None:
        self.create_errors.append((target_dir, message))

    def show_directory_not_found_error(self, target_dir: Path) -> None:
        self.not_found_errors.append(target_dir)

    def show_not_a_directory_error(self, target_dir: Path) -> None:
        self.not_a_dir_errors.append(target_dir)

    def show_cancellation(self) -> None:
        self.cancellation_shown = True

    def show_table_exported(
        self, table_name: str, csv_path: str, n_records: int
    ) -> None:
        self.tables_exported.append((table_name, csv_path, n_records))

    def show_table_skipped(self, table_name: str) -> None:
        self.tables_skipped.append(table_name)


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.services.export_csv import ExportCSV
    from nwtrack.infra.config.settings import Settings
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

    return (
        base_container.register(
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
    )


def _make_interactive(
    container: Container,
    target_dir: str = "",
    confirm_create: bool = False,
) -> tuple[ExportTablesCSVInteractive, MockExportTablesCSVPresenter]:
    from nwtrack.application.services.export_csv import ExportCSV

    presenter = MockExportTablesCSVPresenter(
        target_dir_response=target_dir, confirm_create=confirm_create
    )
    use_case = ExportTablesCSVInteractive(
        exporter=container.resolve(ExportCSV), presenter=presenter
    )
    return use_case, presenter


def _make_cli(
    container: Container,
) -> tuple[ExportTablesCSVCLI, MockExportTablesCSVPresenter]:
    from nwtrack.application.services.export_csv import ExportCSV

    presenter = MockExportTablesCSVPresenter()
    use_case = ExportTablesCSVCLI(
        exporter=container.resolve(ExportCSV), presenter=presenter
    )
    return use_case, presenter


# --- Presenter interaction tests ---


def test_export_interactive_happy_path_calls_header_and_export_methods(
    configured_container: Container,
    sample_entities: dict[str, list],
    tmp_path: Path,
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    use_case, presenter = _make_interactive(
        configured_container, target_dir=str(tmp_path)
    )
    use_case.run(defaults={})

    assert presenter.header_shown
    assert not presenter.cancellation_shown
    assert presenter.tables_exported or presenter.tables_skipped


def test_export_interactive_shows_cancellation_on_quit(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    use_case, presenter = _make_interactive(configured_container, target_dir="q")
    use_case.run(defaults={})

    assert presenter.header_shown
    assert presenter.cancellation_shown
    assert not presenter.tables_exported
    assert not presenter.tables_skipped


def test_export_interactive_nonexistent_dir_prompts_create_and_creates_on_confirm(
    configured_container: Container,
    sample_entities: dict[str, list],
    tmp_path: Path,
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    new_dir = tmp_path / "new_export"
    use_case, presenter = _make_interactive(
        configured_container, target_dir=str(new_dir), confirm_create=True
    )
    use_case.run(defaults={})

    assert new_dir in presenter.directories_created
    assert presenter.tables_exported or presenter.tables_skipped


def test_export_cli_happy_path_calls_header_and_export_methods(
    configured_container: Container,
    sample_entities: dict[str, list],
    tmp_path: Path,
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    use_case, presenter = _make_cli(configured_container)
    use_case.run(target_dir=str(tmp_path), create=False)

    assert presenter.header_shown
    assert presenter.tables_exported or presenter.tables_skipped


def test_export_cli_not_a_directory_shows_error(
    configured_container: Container,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "somefile.txt"
    file_path.write_text("x")
    use_case, presenter = _make_cli(configured_container)
    use_case.run(target_dir=str(file_path), create=False)

    assert presenter.not_a_dir_errors
    assert not presenter.tables_exported


def test_export_cli_missing_dir_without_create_shows_not_found_error(
    configured_container: Container,
    tmp_path: Path,
) -> None:
    use_case, presenter = _make_cli(configured_container)
    use_case.run(target_dir=str(tmp_path / "missing"), create=False)

    assert presenter.not_found_errors
    assert not presenter.tables_exported


def test_export_cli_missing_dir_with_create_creates_and_exports(
    configured_container: Container,
    sample_entities: dict[str, list],
    tmp_path: Path,
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    new_dir = tmp_path / "created"
    use_case, presenter = _make_cli(configured_container)
    use_case.run(target_dir=str(new_dir), create=True)

    assert new_dir in presenter.directories_created
    assert presenter.tables_exported or presenter.tables_skipped


# --- Business logic tests ---


def test_export_tables_interactive(
    configured_container: Container,
    sample_entities: dict[str, list],
    tmp_path,
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    use_case, presenter = _make_interactive(
        configured_container, target_dir=str(tmp_path)
    )
    use_case.run(defaults={"target_dir": str(tmp_path)})

    assert "institutions" in presenter.tables_skipped
    assert "tags" in presenter.tables_skipped
    assert "account_tags" in presenter.tables_skipped

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

    currencies_expected = textwrap.dedent("""
        code,description
        USD,United States Dollar
        CHF,Swiss Franc
        CNY,Chinese Yuan
    """).lstrip()
    categories_expected = textwrap.dedent("""
        name,side
        checking,asset
        savings,asset
        mortgage,liability
        revolving_credit,liability
    """).lstrip()
    accounts_expected = textwrap.dedent("""
        id,name,description,category,institution_id,currency,status
        1,bank_1_checking,bank_1 checking,checking,,USD,active
        2,bank_2_savings,bank_2_savings,savings,,USD,active
        3,credit_cards_1,credit_cards_1,revolving_credit,,USD,active
        4,mortgage_1,mortgage_1,mortgage,,USD,inactive
    """).lstrip()

    with open(tmp_path / "currencies.csv", encoding="utf-8") as f:
        assert f.read() == currencies_expected
    with open(tmp_path / "categories.csv", encoding="utf-8") as f:
        assert f.read() == categories_expected
    with open(tmp_path / "accounts.csv", encoding="utf-8") as f:
        assert f.read() == accounts_expected
    with open(tmp_path / "balances.csv", encoding="utf-8") as f:
        balances_csv = f.readlines()
    assert "id,account_id,month,amount\n" == balances_csv[0]
    assert "10,2,2024-08,2100\n" in balances_csv[:11]


def test_export_accounts_csv_includes_institution_id_when_present(
    configured_container: Container,
    sample_entities: dict[str, list],
    tmp_path,
) -> None:
    from nwtrack.application.services.export_csv import ExportCSV

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
        line
        == (
            "5,phase10_export_account,Export compatibility check,"
            "checking,1,USD,active"
        )
        for line in accounts_csv[1:]
    )


def test_export_tables_csv_includes_institutions_and_tags_when_present(
    configured_container: Container,
    sample_entities: dict[str, list],
    tmp_path,
) -> None:
    from nwtrack.application.services.export_csv import ExportCSV

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

    use_case, presenter = _make_cli(configured_container)
    use_case.run(target_dir=str(tmp_path), create=False)

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

    exported_names = {t[0] for t in presenter.tables_exported}
    assert "institutions" in exported_names
    assert "tags" in exported_names
    assert "account_tags" in exported_names
