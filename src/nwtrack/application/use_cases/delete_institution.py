"""Delete institution interactively."""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import InstitutionDeletePresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases._institution_admin import list_institution_items
from nwtrack.domain.models import Institution

logger = logging.getLogger(__name__)


class DeleteInstitutionInteractive:
    """Delete institution interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        presenter: InstitutionDeletePresenter,
    ) -> None:
        self._uow = uow
        self._presenter = presenter

    def run(self) -> OperationResult[None]:
        """Run the institution delete workflow."""
        logger.info("Starting Delete Institution use case")
        self._presenter.show_header()
        institutions = self._list_items()
        if not institutions:
            self._presenter.show_no_institutions()
            return OperationResult(success=False, error_message="No institutions found")
        self._presenter.display_institutions(institutions)

        institution_id = self._select_institution()
        if institution_id is None:
            logger.warning("Institution delete cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        institution = self._get_institution(institution_id)
        if institution is None:
            _msg = f"Institution ID {institution_id} not found."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        account_count = self._count_linked_accounts(institution_id)
        if not self._presenter.show_preview_and_confirm(institution, account_count):
            logger.warning("Institution delete cancelled by user.")
            self._presenter.show_cancellation("User declined.")
            return OperationResult(success=False, error_message="User declined")

        if account_count > 0:
            self._presenter.show_delete_blocked(institution, account_count)
            return OperationResult(
                success=False,
                error_message="Institution still has linked accounts",
            )

        if self._delete_institution(institution_id) != 1:
            _msg = "Institution delete failed."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        self._presenter.show_success(self._list_items())
        logger.info("Finished Institution Delete workflow")
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

    def _count_linked_accounts(self, institution_id: int) -> int:
        with self._uow() as uow:
            return uow.institutions.count_linked_accounts(institution_id)

    def _delete_institution(self, institution_id: int) -> int:
        with self._uow() as uow:
            return uow.institutions.delete_by_id(institution_id)


def main() -> None:
    """Main entry point for institution delete script."""
    from rich.console import Console

    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.entrypoints.cli.adapters.institution_presenters import (
        RichInstitutionDeletePresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    container = build_base_container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        RichInstitutionDeletePresenter,
        lambda c: RichInstitutionDeletePresenter(console=c.resolve(Console)),
    ).register(
        DeleteInstitutionInteractive,
        lambda c: DeleteInstitutionInteractive(
            uow=lambda: c.resolve(UnitOfWork),
            presenter=c.resolve(RichInstitutionDeletePresenter),
        ),
    )

    result: OperationResult[None] = container.resolve(
        DeleteInstitutionInteractive
    ).run()
    import sys

    sys.exit(0 if result.success else 1)
