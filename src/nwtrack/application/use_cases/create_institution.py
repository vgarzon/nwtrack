"""Create institution interactively."""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import InstitutionCreationPresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases._institution_admin import list_institution_items
from nwtrack.domain.models import Institution

logger = logging.getLogger(__name__)


class CreateInstitutionInteractive:
    """Create institution interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        presenter: InstitutionCreationPresenter,
    ) -> None:
        self._uow = uow
        self._presenter = presenter

    def run(self) -> OperationResult[str]:
        """Run the institution creation workflow."""
        logger.info("Starting Interactive Institution Creator")
        self._presenter.show_header()
        self._presenter.display_institutions(self._list_items())

        data = self._presenter.collect_institution_data()
        if data is None:
            logger.warning("Institution creation cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        if not self._presenter.show_preview_and_confirm(data):
            logger.info("Institution creation cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="User declined")

        institution_name = self._insert_institution(data)
        if institution_name is None:
            _msg = "Institution creation failed."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        is_valid, validation_msg = self._validate_created_institution(
            data, institution_name
        )
        if not is_valid:
            logger.error("Created institution validation failed: %s", validation_msg)
            self._presenter.show_error(f"Validation failed: {validation_msg}")
            return OperationResult(success=False, error_message=validation_msg)

        self._presenter.show_success(institution_name, self._list_items())
        logger.info("Finished Interactive Institution Creator")
        return OperationResult(success=True, data=institution_name)

    def _list_items(self):
        with self._uow() as uow:
            return list_institution_items(uow)

    def _insert_institution(self, institution: Institution) -> str | None:
        with self._uow() as uow:
            try:
                institution_id = uow.institutions.insert(institution)
            except ValueError as e:
                logger.exception("Error inserting institution: %s", e)
                uow.rollback()
                return None
        if institution_id <= 0:
            logger.error("Failed to insert institution: %s", institution.name)
            return None
        return institution.name

    def _validate_created_institution(
        self, data: Institution, institution_name: str
    ) -> tuple[bool, str]:
        with self._uow() as uow:
            result = uow.institutions.get_by_name(institution_name)
        if result is None:
            return False, f"Error retrieving institution '{institution_name}'."
        if result.name != data.name:
            return False, "Institution name mismatch."
        if result.description != data.description:
            return False, "Institution description mismatch."
        return True, "Institution validated successfully."


def main() -> None:
    """Main entry point for institution creation script."""
    from rich.console import Console

    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.entrypoints.cli.adapters.institution_presenters import (
        RichInstitutionCreationPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    container = build_base_container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        RichInstitutionCreationPresenter,
        lambda c: RichInstitutionCreationPresenter(console=c.resolve(Console)),
    ).register(
        CreateInstitutionInteractive,
        lambda c: CreateInstitutionInteractive(
            uow=lambda: c.resolve(UnitOfWork),
            presenter=c.resolve(RichInstitutionCreationPresenter),
        ),
    )

    result: OperationResult[str] = container.resolve(CreateInstitutionInteractive).run()
    import sys

    sys.exit(0 if result.success else 1)
