"""Update institution interactively."""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import InstitutionUpdatePresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases._institution_admin import list_institution_items
from nwtrack.domain.models import Institution

logger = logging.getLogger(__name__)


class UpdateInstitutionInteractive:
    """Update institution interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        presenter: InstitutionUpdatePresenter,
    ) -> None:
        self._uow = uow
        self._presenter = presenter

    def run(self) -> OperationResult[None]:
        """Run the institution update workflow."""
        logger.info("Starting Update Institution use case")
        self._presenter.show_header()
        institutions = self._list_items()
        if not institutions:
            self._presenter.show_no_institutions()
            return OperationResult(success=False, error_message="No institutions found")
        self._presenter.display_institutions(institutions)

        institution_id = self._select_institution()
        if institution_id is None:
            logger.warning("Institution update cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        current_institution = self._get_institution(institution_id)
        if current_institution is None:
            _msg = f"Institution ID {institution_id} not found."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        updated_institution = self._presenter.collect_updated_data(current_institution)
        if updated_institution is None:
            logger.warning("Institution update cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        if self._is_duplicate_name(updated_institution):
            logger.error(
                "Institution name '%s' already exists.",
                updated_institution.name,
            )
            self._presenter.show_duplicate_error(updated_institution.name)
            return OperationResult(
                success=False,
                error_message="Duplicate institution name",
            )

        if not self._presenter.show_preview_and_confirm(updated_institution):
            logger.warning("Institution update cancelled by user.")
            self._presenter.show_cancellation("User declined.")
            return OperationResult(success=False, error_message="User declined")

        self._update_institution(updated_institution)

        if not self._verify_update(institution_id, updated_institution):
            _msg = "Institution update verification failed."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        self._presenter.show_success(self._list_items())
        logger.info("Finished Institution Updater")
        return OperationResult(success=True)

    def _list_items(self):
        with self._uow() as uow:
            return list_institution_items(uow)

    def _select_institution(self) -> int | None:
        while True:
            institution_id = self._presenter.select_institution()
            if institution_id is None:
                return None
            if self._get_institution(institution_id) is not None:
                return institution_id
            self._presenter.show_institution_not_found(institution_id)

    def _get_institution(self, institution_id: int) -> Institution | None:
        with self._uow() as uow:
            return uow.institutions.get_by_id(institution_id)

    def _update_institution(self, updated_institution: Institution) -> None:
        with self._uow() as uow:
            uow.institutions.update(updated_institution)

    def _verify_update(
        self, institution_id: int, update_data: Institution
    ) -> bool:
        retrieved_data = self._get_institution(institution_id)
        if retrieved_data is None:
            logger.error("Error retrieving updated institution.")
            return False
        return retrieved_data == update_data

    def _is_duplicate_name(self, institution: Institution) -> bool:
        with self._uow() as uow:
            institutions = uow.institutions.get_all()
        normalized_name = institution.name.casefold()
        return any(
            existing.name.casefold() == normalized_name
            and existing.id != institution.id
            for existing in institutions
        )


def main() -> None:
    """Main entry point for institution update script."""
    from rich.console import Console

    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.entrypoints.cli.adapters.institution_presenters import (
        RichInstitutionUpdatePresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    container = build_base_container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        RichInstitutionUpdatePresenter,
        lambda c: RichInstitutionUpdatePresenter(console=c.resolve(Console)),
    ).register(
        UpdateInstitutionInteractive,
        lambda c: UpdateInstitutionInteractive(
            uow=lambda: c.resolve(UnitOfWork),
            presenter=c.resolve(RichInstitutionUpdatePresenter),
        ),
    )

    result: OperationResult[None] = container.resolve(
        UpdateInstitutionInteractive
    ).run()
    import sys

    sys.exit(0 if result.success else 1)
