"""Validation tests for CSV import bundle handling."""

from pathlib import Path

import pytest

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.bootstrap.container import Container


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register the import data service for validation tests."""
    return base_container.register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    )


def _write_bundle_file(target_dir: Path, name: str, header: str) -> None:
    (target_dir / f"{name}.csv").write_text(f"{header}\n", encoding="utf-8")


def _write_valid_bundle(target_dir: Path) -> None:
    headers = InitDataService.IMPORT_HEADERS
    for name, fieldnames in headers.items():
        _write_bundle_file(target_dir, name, ",".join(fieldnames))


def test_validate_import_bundle_rejects_missing_source_directory(
    configured_container: Container, tmp_path: Path
) -> None:
    service = configured_container.resolve(InitDataService)

    with pytest.raises(ValueError, match="does not exist"):
        service.validate_import_bundle(tmp_path / "missing")


def test_validate_import_bundle_rejects_missing_required_files(
    configured_container: Container, tmp_path: Path
) -> None:
    service = configured_container.resolve(InitDataService)
    _write_valid_bundle(tmp_path)
    (tmp_path / "tags.csv").unlink()

    with pytest.raises(ValueError, match="Missing required CSV files: tags.csv"):
        service.validate_import_bundle(tmp_path)


def test_validate_import_bundle_rejects_malformed_headers(
    configured_container: Container, tmp_path: Path
) -> None:
    service = configured_container.resolve(InitDataService)
    _write_valid_bundle(tmp_path)
    _write_bundle_file(tmp_path, "accounts", "id,name,description")

    with pytest.raises(ValueError, match="Malformed CSV header for accounts.csv"):
        service.validate_import_bundle(tmp_path)
