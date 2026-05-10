"""Tests for importing table CSV bundles."""

from pathlib import Path

import pytest
from rich.console import Console

from nwtrack.application.ports.schema import SchemaManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.application.use_cases.import_tables_csv import ImportTablesCSVCLI
from nwtrack.bootstrap.composition import build_base_container
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.infra.config.settings import Settings
from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
from nwtrack.infra.persistence.orm.models import account_tags_table
from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl


def _write_bundle_file(target_dir: Path, name: str, header: str, rows: list[str]) -> None:
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
    container.register(Console, lambda _: Console(record=True), lifetime=Lifetime.SINGLETON)
    return container


def test_import_tables_cli_creates_missing_database_and_imports_supported_tables(
    file_db_container: Container, tmp_path: Path
) -> None:
    source_dir = tmp_path / "bundle"
    source_dir.mkdir()
    _write_minimal_bundle(source_dir)

    db_path = Path(file_db_container.resolve(Settings).db_file_path)
    assert not db_path.exists()

    ImportTablesCSVCLI(
        importer=file_db_container.resolve(InitDataService),
        admin_svc=file_db_container.resolve(DBAdminService),
        console=file_db_container.resolve(Console),
    ).run(source_dir=str(source_dir))

    assert db_path.exists()

    with file_db_container.resolve(UnitOfWork) as uow:
        assert uow.currencies.count() == 1
        assert uow.categories.count() == 1
        assert uow.institutions.count() == 1
        assert uow.tags.count() == 1
        assert uow.accounts.count() == 1
        assert uow.balances.count() == 1
        assert uow.exchange_rates.count() == 1
        assert [tag.id for tag in uow.tags.get_for_account(1)] == [1]


def test_import_tables_cli_is_idempotent_for_repeated_bundle_imports(
    file_db_container: Container, tmp_path: Path
) -> None:
    source_dir = tmp_path / "bundle"
    source_dir.mkdir()
    _write_minimal_bundle(source_dir)

    importer = ImportTablesCSVCLI(
        importer=file_db_container.resolve(InitDataService),
        admin_svc=file_db_container.resolve(DBAdminService),
        console=file_db_container.resolve(Console),
    )

    importer.run(source_dir=str(source_dir))
    importer.run(source_dir=str(source_dir))

    with file_db_container.resolve(UnitOfWork) as uow:
        assert uow.currencies.count() == 1
        assert uow.categories.count() == 1
        assert uow.institutions.count() == 1
        assert uow.tags.count() == 1
        assert uow.accounts.count() == 1
        assert uow.balances.count() == 1
        assert uow.exchange_rates.count() == 1
        session = getattr(uow, "_session", None)
        assert session is not None
        links = session.execute(account_tags_table.select()).all()
        assert len(links) == 1


def test_import_tables_cli_updates_matching_rows_by_bundle_identity(
    file_db_container: Container, tmp_path: Path
) -> None:
    source_dir = tmp_path / "bundle"
    source_dir.mkdir()
    _write_minimal_bundle(source_dir)

    importer = ImportTablesCSVCLI(
        importer=file_db_container.resolve(InitDataService),
        admin_svc=file_db_container.resolve(DBAdminService),
        console=file_db_container.resolve(Console),
    )
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

    with file_db_container.resolve(UnitOfWork) as uow:
        institution = uow.institutions.get_by_id(1)
        account = uow.accounts.get_by_id(1)
        balance = uow.balances.get_by_id(1)

        assert institution is not None
        assert institution.description == "Updated bank description"
        assert account is not None
        assert account.description == "Updated cash account"
        assert account.status.value == "inactive"
        assert balance is not None
        assert balance.amount == 2500
