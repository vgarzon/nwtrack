"""List institutions interactively."""

from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import InstitutionListPresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases._institution_admin import list_institution_items


class ListInstitutions:
    """List institutions."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        presenter: InstitutionListPresenter,
    ) -> None:
        self._uow = uow
        self._presenter = presenter

    def run(self) -> OperationResult[None]:
        """Run the institution listing workflow."""
        with self._uow() as uow:
            institutions = list_institution_items(uow)
        self._presenter.display_institutions(institutions)
        return OperationResult(success=True)


def main() -> None:
    """Main entry point for institution listing script."""
    from rich.console import Console

    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.entrypoints.cli.adapters.institution_presenters import (
        RichInstitutionListPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    container = build_base_container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        RichInstitutionListPresenter,
        lambda c: RichInstitutionListPresenter(console=c.resolve(Console)),
    ).register(
        ListInstitutions,
        lambda c: ListInstitutions(
            uow=lambda: c.resolve(UnitOfWork),
            presenter=c.resolve(RichInstitutionListPresenter),
        ),
    )

    result: OperationResult[None] = container.resolve(ListInstitutions).run()
    import sys

    sys.exit(0 if result.success else 1)
