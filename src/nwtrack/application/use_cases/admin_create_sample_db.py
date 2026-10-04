"""Create a new SQLite database filled with a minimal sample dataset."""

import logging
from collections.abc import Callable
from pathlib import Path

from nwtrack.application.dto import OperationResult, SampleDatabaseResult
from nwtrack.application.ports.presentation import AdminCreateSampleDbPresenter
from nwtrack.application.ports.schema import SchemaManager
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.sample_data import (
    build_sample_records,
    sample_months,
)
from nwtrack.domain.value_objects import Month

logger = logging.getLogger(__name__)


class CreateSampleDatabase:
    """Create a brand-new database at ``path`` and load the sample dataset.

    Never overwrites: any existing path is rejected, and the target file is
    created exclusively before any database engine touches it. The schema and
    data services are passed as factories so nothing is built (and no parent
    directory is created) until the target has been validated.
    """

    def __init__(
        self,
        path: Path,
        schema_manager: Callable[[], SchemaManager],
        data_service: Callable[[], InitDataService],
        presenter: AdminCreateSampleDbPresenter,
        today: Month,
    ) -> None:
        self._path = path
        self._schema_manager = schema_manager
        self._data_service = data_service
        self._presenter = presenter
        self._today = today

    def run(self) -> OperationResult[SampleDatabaseResult]:
        logger.info("Starting CreateSampleDatabase use case: %s", self._path)
        self._presenter.show_header()

        error = self._validate_target()
        if error:
            return self._fail(error)

        try:
            self._path.touch(exist_ok=False)  # exclusive create: never overwrite
        except FileExistsError:
            return self._fail(f"{self._path} already exists; nothing was changed.")
        except OSError as e:
            return self._fail(f"Cannot create {self._path}: {e}")

        records = build_sample_records(self._today)
        try:
            self._schema_manager().create_all_tables()
            self._data_service().import_records(records)
        except Exception as e:
            logger.error("Sample database creation failed: %s", e)
            self._path.unlink(missing_ok=True)  # only a file this run created
            return self._fail(f"Sample database creation failed: {e}")

        months = sample_months(self._today)
        result = SampleDatabaseResult(
            path=self._path,
            currencies=len(records["currencies"]),
            institutions=len(records["institutions"]),
            tags=len(records["tags"]),
            accounts=len(records["accounts"]),
            balances=len(records["balances"]),
            first_month=months[0],
            last_month=months[-1],
        )
        self._presenter.show_success(result)
        logger.info("Finished CreateSampleDatabase: %s", self._path)
        return OperationResult(success=True, data=result)

    def _validate_target(self) -> str:
        if self._path.exists() or self._path.is_symlink():
            return f"{self._path} already exists; nothing was changed."
        if not self._path.parent.is_dir():
            return f"Directory {self._path.parent} does not exist."
        return ""

    def _fail(self, message: str) -> OperationResult[SampleDatabaseResult]:
        self._presenter.show_error(message)
        return OperationResult(success=False, error_message=message)


def main(path: Path) -> int:
    from dataclasses import replace
    from datetime import date

    from rich.console import Console

    from nwtrack.bootstrap.composition import (
        build_base_container,
        build_data_services_container,
    )
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.admin_presenters import (
        RichAdminCreateSampleDbPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console
    from nwtrack.infra.config.load import load_settings
    from nwtrack.infra.config.settings import Settings

    target = path.expanduser().absolute()
    settings = load_settings()
    setup_logging(settings)

    # Point every persistence component at the target file, never the
    # configured database.
    sample_settings = replace(settings, db_file_path=str(target))
    container = build_base_container().register(
        Settings, lambda _: sample_settings, lifetime=Lifetime.SINGLETON
    )
    build_data_services_container(container)
    container.register(
        Console, lambda _: build_console(), lifetime=Lifetime.SINGLETON
    ).register(
        RichAdminCreateSampleDbPresenter,
        lambda c: RichAdminCreateSampleDbPresenter(console=c.resolve(Console)),
    )

    today = date.today()
    use_case = CreateSampleDatabase(
        path=target,
        schema_manager=lambda: container.resolve(SchemaManager),
        data_service=lambda: container.resolve(InitDataService),
        presenter=container.resolve(RichAdminCreateSampleDbPresenter),
        today=Month(today.year, today.month),
    )
    op = use_case.run()
    return 0 if op.success else 1
