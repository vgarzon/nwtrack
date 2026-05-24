"""Tests for importing table CSV bundles."""

from pathlib import Path

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.ports.schema import SchemaManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.application.services.export_csv import ExportCSV
from nwtrack.application.use_cases.import_tables_csv import (
    ImportTablesCSVCLI,
    ImportTablesCSVInteractive,
)
from nwtrack.bootstrap.composition import build_base_container
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.domain.models import Account, Balance, Institution, Status, Tag
from nwtrack.infra.config.settings import Settings
from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
from nwtrack.infra.persistence.orm.models import account_tags_table
from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl


class MockImportTablesCSVPresenter:
    """Test double for ImportTablesCSVPresenter."""

    def __init__(self, source_dir_response: str = "") -> None:
        self._source_dir_response = source_dir_response
        self.header_shown = False
        self.cancellation_shown = False
        self.errors: list[str] = []
        self.success_dirs: list[Path] = []

    def show_header(self) -> None:
        self.header_shown = True

    def prompt_for_source_dir(self, default: str) -> str:
        return self._source_dir_response

    def show_cancellation(self) -> None:
        self.cancellation_shown = True

    def show_import_success(self, source_dir: Path) -> None:
        self.success_dirs.append(source_dir)

    def show_error(self, message: str) -> None:
        self.errors.append(message)


def _write_bundle_file(
    target_dir: Path, name: str, header: str, rows: list[str]
) -> None:
    body = "\n".join([header, *rows]) + "\n"
    (target_dir / f"{name}.csv").write_text(body, encoding="utf-8")


def _write_minimal_bundle(target_dir: Path) -> None:
    _write_bundle_file(target_dir, "currencies", "code,description", ["USD,US Dollar"])
    _write_bundle_file(target_dir, "categories", "name,side", ["checking,asset"])
    _write_bundle_file(
        target_dir,
        "institutions",
        "id,name,description",
        ["1,Chase,Primary bank"],
    )
    _write_bundle_file(target_dir, "tags", "id,name,description", ["1,core,Core cash"])
    _write_bundle_file(
        target_dir,
        "accounts",
        "id,name,description,category,institution_id,currency,status",
        ["1,cash,Main cash account,checking,1,USD,active"],
    )
    _write_bundle_file(target_dir, "account_tags", "account_id,tag_id", ["1,1"])
    _write_bundle_file(
        target_dir, "balances", "id,account_id,month,amount", ["1,1,2024-01,1000"]
    )
    _write_bundle_file(
        target_dir,
        "exchange_rates",
        "id,currency,month,rate",
        ["1,USD,2024-01,1.0"],
    )


def _write_invalid_account_tag_bundle(target_dir: Path) -> None:
    _write_minimal_bundle(target_dir)
    _write_bundle_file(target_dir, "account_tags", "account_id,tag_id", ["1,99"])


def _read_bundle_contents(source_dir: Path) -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(source_dir.glob("*.csv"))
    }


@pytest.fixture
def file_db_container(tmp_path: Path) -> Container:
    """Configure a container backed by a temporary SQLite file."""
    settings = Settings(db_file_path=str(tmp_path / "phase22-import.db"))
    container = build_base_container()
    container.register(Settings, lambda _: settings, lifetime=Lifetime.SINGLETON)
    container.register(
        SchemaManager,
        lambda c: SchemaManagerImpl(engine=c.resolve(SQLiteSessionManager).engine),
    )
    container.register(
        DBAdminService,
        lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
    )
    container.register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    )
    return container


def _make_importer_cli(container: Container) -> ImportTablesCSVCLI:
    return ImportTablesCSVCLI(
        importer=container.resolve(InitDataService),
        admin_svc=container.resolve(DBAdminService),
        presenter=MockImportTablesCSVPresenter(),
    )


# --- Presenter interaction tests ---


def test_import_tables_interactive_calls_show_header_and_success(
    file_db_container: Container, tmp_path: Path
) -> None:
    source_dir = tmp_path / "bundle"
    source_dir.mkdir()
    _write_minimal_bundle(source_dir)

    presenter = MockImportTablesCSVPresenter(source_dir_response=str(source_dir))
    ImportTablesCSVInteractive(
        importer=file_db_container.resolve(InitDataService),
        admin_svc=file_db_container.resolve(DBAdminService),
        presenter=presenter,
    ).run(defaults={})

    assert presenter.header_shown
    assert len(presenter.success_dirs) == 1
    assert presenter.success_dirs[0] == source_dir
    assert not presenter.cancellation_shown
    assert not presenter.errors


def test_import_tables_interactive_shows_cancellation_on_quit(
    file_db_container: Container,
) -> None:
    presenter = MockImportTablesCSVPresenter(source_dir_response="q")
    ImportTablesCSVInteractive(
        importer=file_db_container.resolve(InitDataService),
        admin_svc=file_db_container.resolve(DBAdminService),
        presenter=presenter,
    ).run(defaults={})

    assert presenter.header_shown
    assert presenter.cancellation_shown
    assert not presenter.success_dirs
    assert not presenter.errors


def test_import_tables_cli_calls_show_header_and_success(
    file_db_container: Container, tmp_path: Path
) -> None:
    source_dir = tmp_path / "bundle"
    source_dir.mkdir()
    _write_minimal_bundle(source_dir)

    presenter = MockImportTablesCSVPresenter()
    ImportTablesCSVCLI(
        importer=file_db_container.resolve(InitDataService),
        admin_svc=file_db_container.resolve(DBAdminService),
        presenter=presenter,
    ).run(source_dir=str(source_dir))

    assert presenter.header_shown
    assert len(presenter.success_dirs) == 1
    assert not presenter.errors


def test_import_tables_base_shows_error_on_service_exception(
    file_db_container: Container, tmp_path: Path
) -> None:
    presenter = MockImportTablesCSVPresenter()
    ImportTablesCSVCLI(
        importer=file_db_container.resolve(InitDataService),
        admin_svc=file_db_container.resolve(DBAdminService),
        presenter=presenter,
    ).run(source_dir=str(tmp_path / "nonexistent"))

    assert presenter.errors
    assert not presenter.success_dirs


# --- Business logic tests ---


def test_import_tables_cli_creates_missing_database_and_imports_supported_tables(
    file_db_container: Container, tmp_path: Path
) -> None:
    source_dir = tmp_path / "bundle"
    source_dir.mkdir()
    _write_minimal_bundle(source_dir)

    db_path = Path(file_db_container.resolve(Settings).db_file_path)
    assert not db_path.exists()

    _make_importer_cli(file_db_container).run(source_dir=str(source_dir))

    assert db_path.exists()

    typed_uow: UnitOfWork
    with file_db_container.resolve(UnitOfWork) as typed_uow:
        linked_tags: list[Tag] = typed_uow.tags.get_for_account(1)
        assert typed_uow.currencies.count() == 1
        assert typed_uow.categories.count() == 1
        assert typed_uow.institutions.count() == 1
        assert typed_uow.tags.count() == 1
        assert typed_uow.accounts.count() == 1
        assert typed_uow.balances.count() == 1
        assert typed_uow.exchange_rates.count() == 1
        assert [linked_tag.id for linked_tag in linked_tags] == [1]


def test_import_tables_cli_is_idempotent_for_repeated_bundle_imports(
    file_db_container: Container, tmp_path: Path
) -> None:
    source_dir = tmp_path / "bundle"
    source_dir.mkdir()
    _write_minimal_bundle(source_dir)

    importer = _make_importer_cli(file_db_container)
    importer.run(source_dir=str(source_dir))
    importer.run(source_dir=str(source_dir))

    typed_uow: UnitOfWork
    with file_db_container.resolve(UnitOfWork) as typed_uow:
        assert typed_uow.currencies.count() == 1
        assert typed_uow.categories.count() == 1
        assert typed_uow.institutions.count() == 1
        assert typed_uow.tags.count() == 1
        assert typed_uow.accounts.count() == 1
        assert typed_uow.balances.count() == 1
        assert typed_uow.exchange_rates.count() == 1
        session = getattr(typed_uow, "_session", None)
        assert session is not None
        links = session.execute(account_tags_table.select()).all()
        assert len(links) == 1


def test_import_tables_cli_updates_matching_rows_by_bundle_identity(
    file_db_container: Container, tmp_path: Path
) -> None:
    source_dir = tmp_path / "bundle"
    source_dir.mkdir()
    _write_minimal_bundle(source_dir)

    importer = _make_importer_cli(file_db_container)
    importer.run(source_dir=str(source_dir))

    _write_bundle_file(
        source_dir,
        "institutions",
        "id,name,description",
        ["1,Chase,Updated bank description"],
    )
    _write_bundle_file(
        source_dir,
        "accounts",
        "id,name,description,category,institution_id,currency,status",
        ["1,cash,Updated cash account,checking,1,USD,inactive"],
    )
    _write_bundle_file(
        source_dir, "balances", "id,account_id,month,amount", ["1,1,2024-01,2500"]
    )

    importer.run(source_dir=str(source_dir))

    typed_uow: UnitOfWork
    with file_db_container.resolve(UnitOfWork) as typed_uow:
        institution: Institution | None = typed_uow.institutions.get_by_id(1)
        account: Account | None = typed_uow.accounts.get_by_id(1)
        balance: Balance | None = typed_uow.balances.get_by_id(1)

        assert institution is not None
        assert institution.description == "Updated bank description"
        assert account is not None
        assert account.description == "Updated cash account"
        assert account.status.value == "inactive"
        assert balance is not None
        assert balance.amount == 2500


def test_import_tables_interactive_imports_valid_bundle(
    file_db_container: Container, tmp_path: Path
) -> None:
    source_dir = tmp_path / "bundle"
    source_dir.mkdir()
    _write_minimal_bundle(source_dir)

    presenter = MockImportTablesCSVPresenter(source_dir_response=str(source_dir))
    ImportTablesCSVInteractive(
        importer=file_db_container.resolve(InitDataService),
        admin_svc=file_db_container.resolve(DBAdminService),
        presenter=presenter,
    ).run(defaults={"source_dir": str(source_dir)})

    typed_uow: UnitOfWork
    with file_db_container.resolve(UnitOfWork) as typed_uow:
        assert typed_uow.accounts.count() == 1

    assert len(presenter.success_dirs) == 1


def test_import_tables_cli_leaves_unmatched_existing_rows_unchanged(
    file_db_container: Container, tmp_path: Path
) -> None:
    source_dir = tmp_path / "bundle"
    source_dir.mkdir()
    _write_minimal_bundle(source_dir)

    importer = _make_importer_cli(file_db_container)
    importer.run(source_dir=str(source_dir))

    typed_uow_insert: UnitOfWork
    with file_db_container.resolve(UnitOfWork) as typed_uow_insert:
        inserted_id: int = typed_uow_insert.institutions.insert(
            Institution(name="Spare bank", description="Not in bundle")
        )
        assert inserted_id == 2

    importer.run(source_dir=str(source_dir))

    typed_uow_verify: UnitOfWork
    with file_db_container.resolve(UnitOfWork) as typed_uow_verify:
        spare: Institution | None = typed_uow_verify.institutions.get_by_id(2)
        assert spare is not None
        assert spare.name == "Spare bank"


def test_import_tables_cli_rolls_back_on_invalid_relationship_rows(
    file_db_container: Container, tmp_path: Path
) -> None:
    source_dir = tmp_path / "bundle"
    source_dir.mkdir()
    _write_invalid_account_tag_bundle(source_dir)

    presenter = MockImportTablesCSVPresenter()
    ImportTablesCSVCLI(
        importer=file_db_container.resolve(InitDataService),
        admin_svc=file_db_container.resolve(DBAdminService),
        presenter=presenter,
    ).run(source_dir=str(source_dir))

    typed_uow: UnitOfWork
    with file_db_container.resolve(UnitOfWork) as typed_uow:
        assert typed_uow.currencies.count() == 0
        assert typed_uow.accounts.count() == 0
        session = getattr(typed_uow, "_session", None)
        assert session is not None
        assert session.execute(account_tags_table.select()).all() == []

    assert presenter.errors


def test_export_import_round_trip_reproduces_supported_bundle(
    base_container: Container,
    sample_entities: dict[str, list],
    tmp_path: Path,
) -> None:
    base_container.register(
        DBAdminService,
        lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
    )
    init_db_tables_w_entities(base_container, sample_entities)

    typed_uow: UnitOfWork
    with base_container.resolve(UnitOfWork) as typed_uow:
        institution_id: int = typed_uow.institutions.insert(
            Institution(name="Fidelity", description="Brokerage")
        )
        retirement_id: int = typed_uow.tags.insert(
            Tag(name="retirement", description="Retirement assets")
        )
        core_id: int = typed_uow.tags.insert(
            Tag(name="core", description="Core liquidity")
        )
        account: Account | None = typed_uow.accounts.get_by_id(1)
        assert account is not None
        account.institution_id = institution_id
        account.status = Status.INACTIVE
        typed_uow.accounts.update(account)
        typed_uow.tags.replace_for_account(1, [core_id, retirement_id])
        typed_uow.tags.replace_for_account(2, [retirement_id])

    source_export_dir = tmp_path / "source-export"
    source_export_dir.mkdir()
    ExportCSV(uow=lambda: base_container.resolve(UnitOfWork)).export_tables_to_dir(
        source_export_dir
    )

    target_container = build_base_container()
    target_container.register(
        Settings,
        lambda _: Settings(db_file_path=str(tmp_path / "roundtrip.db")),
        lifetime=Lifetime.SINGLETON,
    )
    target_container.register(
        SchemaManager,
        lambda c: SchemaManagerImpl(engine=c.resolve(SQLiteSessionManager).engine),
    )
    target_container.register(
        DBAdminService,
        lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
    )
    target_container.register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    )

    ImportTablesCSVCLI(
        importer=target_container.resolve(InitDataService),
        admin_svc=target_container.resolve(DBAdminService),
        presenter=MockImportTablesCSVPresenter(),
    ).run(source_dir=str(source_export_dir))

    roundtrip_export_dir = tmp_path / "roundtrip-export"
    roundtrip_export_dir.mkdir()
    ExportCSV(uow=lambda: target_container.resolve(UnitOfWork)).export_tables_to_dir(
        roundtrip_export_dir
    )

    assert _read_bundle_contents(roundtrip_export_dir) == _read_bundle_contents(
        source_export_dir
    )
