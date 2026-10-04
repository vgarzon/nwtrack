"""Tests for the CreateSampleDatabase use case."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from nwtrack.application.ports.presentation import AdminCreateSampleDbPresenter
from nwtrack.application.ports.schema import SchemaManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.use_cases.admin_create_sample_db import CreateSampleDatabase
from nwtrack.bootstrap.composition import (
    build_base_container,
    build_data_services_container,
)
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.domain.value_objects import Month
from nwtrack.infra.config.settings import Settings
from nwtrack.infra.persistence.alembic_runtime import build_alembic_config

TODAY = Month(2026, 10)


def _container_for(path: Path) -> Container:
    settings = Settings(
        db_file_path=str(path),
        log_file=str(path.parent / "test.log"),
        log_file_level="INFO",
        log_rotation_mb=10,
        log_backup_count=7,
    )
    container = build_base_container().register(
        Settings, lambda _: settings, lifetime=Lifetime.SINGLETON
    )
    return build_data_services_container(container)


def _use_case(
    path: Path, container: Container, presenter: MagicMock
) -> CreateSampleDatabase:
    return CreateSampleDatabase(
        path=path,
        schema_manager=lambda: container.resolve(SchemaManager),
        data_service=lambda: container.resolve(InitDataService),
        presenter=presenter,
        today=TODAY,
    )


@pytest.fixture
def presenter() -> MagicMock:
    return MagicMock(spec=AdminCreateSampleDbPresenter)


def test_creates_database_with_schema_at_head_and_data(
    tmp_path: Path, presenter: MagicMock
) -> None:
    target = tmp_path / "demo.db"
    container = _container_for(target)

    result = _use_case(target, container, presenter).run()

    assert result.success
    assert result.data is not None
    assert result.data.path == target
    assert result.data.last_month == TODAY
    presenter.show_header.assert_called_once()
    presenter.show_success.assert_called_once_with(result.data)

    engine = create_engine(f"sqlite:///{target}")
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    engine.dispose()
    with create_engine("sqlite://").connect() as conn:
        config = build_alembic_config(conn)
        head = ScriptDirectory.from_config(config).get_current_head()
    assert version == head

    uow: UnitOfWork
    with container.resolve(UnitOfWork) as uow:
        assert len(uow.accounts.get_all()) == result.data.accounts


def test_reports_run_against_sample_database(
    tmp_path: Path, presenter: MagicMock
) -> None:
    from nwtrack.application.services.fetch import FetchService

    target = tmp_path / "demo.db"
    container = _container_for(target)
    result = _use_case(target, container, presenter).run()
    assert result.success

    fetcher = FetchService(uow=lambda: container.resolve(UnitOfWork))
    recent = fetcher.get_recent_months(n_months=1)
    assert recent == [TODAY]


@pytest.mark.parametrize("kind", ["file", "directory"])
def test_refuses_existing_path_and_leaves_it_unchanged(
    tmp_path: Path, presenter: MagicMock, kind: str
) -> None:
    target = tmp_path / "existing"
    if kind == "file":
        target.write_bytes(b"production data")
    else:
        target.mkdir()
    container = _container_for(target)

    result = _use_case(target, container, presenter).run()

    assert not result.success
    assert "already exists" in result.error_message
    presenter.show_error.assert_called_once()
    presenter.show_success.assert_not_called()
    if kind == "file":
        assert target.read_bytes() == b"production data"
    else:
        assert target.is_dir() and not list(target.iterdir())


def test_refuses_dangling_symlink(tmp_path: Path, presenter: MagicMock) -> None:
    target = tmp_path / "link.db"
    target.symlink_to(tmp_path / "missing.db")
    container = _container_for(target)

    result = _use_case(target, container, presenter).run()

    assert not result.success
    assert not (tmp_path / "missing.db").exists()


def test_missing_parent_directory_fails_without_creating_anything(
    tmp_path: Path, presenter: MagicMock
) -> None:
    target = tmp_path / "nope" / "demo.db"
    container = _container_for(target)

    result = _use_case(target, container, presenter).run()

    assert not result.success
    assert "does not exist" in result.error_message
    assert not (tmp_path / "nope").exists()


def test_failure_during_load_removes_partial_file(
    tmp_path: Path, presenter: MagicMock
) -> None:
    target = tmp_path / "demo.db"
    container = _container_for(target)
    data_service = MagicMock(spec=InitDataService)
    data_service.import_records.side_effect = RuntimeError("boom")
    use_case = CreateSampleDatabase(
        path=target,
        schema_manager=lambda: container.resolve(SchemaManager),
        data_service=lambda: data_service,
        presenter=presenter,
        today=TODAY,
    )

    result = use_case.run()

    assert not result.success
    assert "boom" in result.error_message
    assert not target.exists()
    presenter.show_error.assert_called_once()
