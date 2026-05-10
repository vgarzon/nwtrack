"""List tags interactively."""

from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import TagListPresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases._tag_admin import list_tag_items


class ListTags:
    """List tags."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        presenter: TagListPresenter,
    ) -> None:
        self._uow = uow
        self._presenter = presenter

    def run(self) -> OperationResult[None]:
        """Run the tag listing workflow."""
        with self._uow() as uow:
            tags = list_tag_items(uow)
        self._presenter.display_tags(tags)
        return OperationResult(success=True)


def main() -> None:
    """Main entry point for tag listing script."""
    from rich.console import Console

    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.entrypoints.cli.adapters.tag_presenters import RichTagListPresenter
    from nwtrack.entrypoints.cli.ui.console import build_console

    container = build_base_container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        RichTagListPresenter,
        lambda c: RichTagListPresenter(console=c.resolve(Console)),
    ).register(
        ListTags,
        lambda c: ListTags(
            uow=lambda: c.resolve(UnitOfWork),
            presenter=c.resolve(RichTagListPresenter),
        ),
    )

    result: OperationResult[None] = container.resolve(ListTags).run()
    import sys

    sys.exit(0 if result.success else 1)
