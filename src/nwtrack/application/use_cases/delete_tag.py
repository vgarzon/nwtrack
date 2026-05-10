"""Delete tag interactively."""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import TagDeletePresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases._tag_admin import list_tag_items
from nwtrack.domain.models import Tag

logger = logging.getLogger(__name__)


class DeleteTagInteractive:
    """Delete tag interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        presenter: TagDeletePresenter,
    ) -> None:
        self._uow = uow
        self._presenter = presenter

    def run(self) -> OperationResult[None]:
        """Run the tag delete workflow."""
        logger.info("Starting Delete Tag use case")
        self._presenter.show_header()
        tags = self._list_items()
        if not tags:
            self._presenter.show_no_tags()
            return OperationResult(success=False, error_message="No tags found")
        self._presenter.display_tags(tags)

        tag_id = self._select_tag()
        if tag_id is None:
            logger.warning("Tag delete cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        tag = self._get_tag(tag_id)
        if tag is None:
            message = f"Tag ID {tag_id} not found."
            logger.error(message)
            self._presenter.show_error(message)
            return OperationResult(success=False, error_message=message)

        account_count = self._count_linked_accounts(tag_id)
        if not self._presenter.show_preview_and_confirm(tag, account_count):
            logger.warning("Tag delete cancelled by user.")
            self._presenter.show_cancellation("User declined.")
            return OperationResult(success=False, error_message="User declined")

        if account_count > 0:
            self._presenter.show_delete_blocked(tag, account_count)
            return OperationResult(
                success=False,
                error_message="Tag still has linked accounts",
            )

        if self._delete_tag(tag_id) != 1:
            message = "Tag delete failed."
            logger.error(message)
            self._presenter.show_error(message)
            return OperationResult(success=False, error_message=message)

        self._presenter.show_success(self._list_items())
        logger.info("Finished Tag Delete workflow")
        return OperationResult(success=True)

    def _list_items(self):
        with self._uow() as uow:
            return list_tag_items(uow)

    def _select_tag(self) -> int | None:
        while True:
            tag_id = self._presenter.select_tag()
            if tag_id is None:
                return None
            if self._get_tag(tag_id) is not None:
                return tag_id
            self._presenter.show_tag_not_found(tag_id)

    def _get_tag(self, tag_id: int) -> Tag | None:
        with self._uow() as uow:
            return uow.tags.get_by_id(tag_id)

    def _count_linked_accounts(self, tag_id: int) -> int:
        with self._uow() as uow:
            return uow.tags.count_linked_accounts(tag_id)

    def _delete_tag(self, tag_id: int) -> int:
        with self._uow() as uow:
            return uow.tags.delete_by_id(tag_id)


def main() -> None:
    """Main entry point for tag delete script."""
    from rich.console import Console

    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.entrypoints.cli.adapters.tag_presenters import RichTagDeletePresenter
    from nwtrack.entrypoints.cli.ui.console import build_console

    container = build_base_container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        RichTagDeletePresenter,
        lambda c: RichTagDeletePresenter(console=c.resolve(Console)),
    ).register(
        DeleteTagInteractive,
        lambda c: DeleteTagInteractive(
            uow=lambda: c.resolve(UnitOfWork),
            presenter=c.resolve(RichTagDeletePresenter),
        ),
    )

    result: OperationResult[None] = container.resolve(DeleteTagInteractive).run()
    import sys

    sys.exit(0 if result.success else 1)
