"""Interactively assign institutions to accounts that have none."""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import AdminAssignInstitutionsPresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account

logger = logging.getLogger(__name__)


class AssignInstitutions:
    """Interactive remediation: assign institutions to unassigned accounts."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        fetcher: FetchService,
        presenter: AdminAssignInstitutionsPresenter,
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._presenter = presenter

    def run(self) -> OperationResult[int]:
        logger.info("Starting AssignInstitutions use case")
        self._presenter.show_header()

        institutions = self._fetcher.get_all_institutions()
        if not institutions:
            self._presenter.show_no_institutions_error()
            return OperationResult(
                success=False, error_message="No institutions available"
            )

        assigned_count = 0

        while True:
            accounts = self._fetcher.get_accounts_without_institution()
            if not accounts:
                self._presenter.show_empty_state()
                break

            self._presenter.display_unassigned(accounts)
            account_id = self._presenter.select_account(accounts)
            if account_id is None:
                break

            account = next((a for a in accounts if a.id == account_id), None)
            if account is None:
                continue

            institution_id = self._presenter.select_institution(institutions)
            if institution_id is None:
                break

            institution = next(
                (i for i in institutions if i.id == institution_id), None
            )
            if institution is None:
                continue

            if not self._presenter.confirm_assignment(account, institution):
                continue

            self._assign_institution(account, institution_id)
            self._presenter.show_assignment_success(account, institution)
            assigned_count += 1

        self._presenter.show_session_summary(assigned_count)
        logger.info(
            "Finished AssignInstitutions; assigned %d institution(s)", assigned_count
        )
        return OperationResult(success=True, data=assigned_count)

    def _assign_institution(self, account: Account, institution_id: int) -> None:
        with self._uow() as uow:
            updated = Account(
                name=account.name,
                description=account.description,
                category_name=account.category_name,
                currency_code=account.currency_code,
                institution_id=institution_id,
                status=account.status,
            )
            updated.id = account.id
            uow.accounts.update(updated)


def main() -> int:
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.composition import build_base_container
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.admin_presenters import (
        RichAdminAssignInstitutionsPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    load_dotenv()
    setup_logging()

    container = build_base_container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        RichAdminAssignInstitutionsPresenter,
        lambda c: RichAdminAssignInstitutionsPresenter(
            console=c.resolve(Console),
            fetcher=c.resolve(FetchService),
        ),
    ).register(
        AssignInstitutions,
        lambda c: AssignInstitutions(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=c.resolve(FetchService),
            presenter=c.resolve(RichAdminAssignInstitutionsPresenter),
        ),
    )

    result: OperationResult[int] = container.resolve(AssignInstitutions).run()
    return 0 if result.success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
