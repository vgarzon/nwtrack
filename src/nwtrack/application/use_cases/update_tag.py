"""Update tag interactively."""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import TagUpdatePresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases._tag_admin import (
    list_tag_items,
    normalize_tag_name,
    normalized_tag,
)
from nwtrack.domain.models import Tag

logger = logging.getLogger(__name__)


class UpdateTagInteractive:
    """Update tag interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        presenter: TagUpdatePresenter,
    ) -> None:
        self._uow = uow
        self._presenter = presenter

    def run(self) -> OperationResult[None]:
        """Run the tag update workflow."""
        logger.info("Starting Update Tag use case")
        self._presenter.show_header()
        tags = self._list_items()
        if not tags:
            self._presenter.show_no_tags()
            return OperationResult(success=False, error_message="No tags found")
        self._presenter.display_tags(tags)

        tag_id = self._select_tag()
        if tag_id is None:
            logger.warning("Tag update cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        current_tag = self._get_tag(tag_id)
        if current_tag is None:
            message = f"Tag ID {tag_id} not found."
            logger.error(message)
            self._presenter.show_error(message)
            return OperationResult(success=False, error_message=message)

        raw_updated_tag = self._presenter.collect_updated_data(current_tag)
        if raw_updated_tag is None:
            logger.warning("Tag update cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        updated_tag = normalized_tag(raw_updated_tag)
        if not updated_tag.name:
            self._presenter.show_empty_name_error()
            return OperationResult(
                success=False,
                error_message="Tag name cannot be empty after normalization",
            )

        if self._is_duplicate_name(updated_tag):
            logger.error("Tag name '%s' already exists.", updated_tag.name)
            self._presenter.show_duplicate_error(updated_tag.name)
            return OperationResult(
                success=False,
                error_message="Duplicate tag name",
            )

        if not self._presenter.show_preview_and_confirm(updated_tag):
            logger.warning("Tag update cancelled by user.")
            self._presenter.show_cancellation("User declined.")
            return OperationResult(success=False, error_message="User declined")

        self._update_tag(updated_tag)

        if not self._verify_update(tag_id, updated_tag):
            message = "Tag update verification failed."
            logger.error(message)
            self._presenter.show_error(message)
            return OperationResult(success=False, error_message=message)

        self._presenter.show_success(self._list_items())
        logger.info("Finished Tag Updater")
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

    def _update_tag(self, updated_tag: Tag) -> None:
        with self._uow() as uow:
            uow.tags.update(updated_tag)

    def _verify_update(self, tag_id: int, update_data: Tag) -> bool:
        retrieved_data = self._get_tag(tag_id)
        if retrieved_data is None:
            logger.error("Error retrieving updated tag.")
            return False
        return retrieved_data == update_data

    def _is_duplicate_name(self, tag: Tag) -> bool:
        with self._uow() as uow:
            tags = uow.tags.get_all()
        normalized_name = normalize_tag_name(tag.name)
        return any(
            existing.name == normalized_name and existing.id != tag.id
            for existing in tags
        )


def main() -> None:
    """Main entry point for tag update script."""
    from rich.console import Console

    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.entrypoints.cli.adapters.tag_presenters import RichTagUpdatePresenter
    from nwtrack.entrypoints.cli.ui.console import build_console

    container = build_base_container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        RichTagUpdatePresenter,
        lambda c: RichTagUpdatePresenter(console=c.resolve(Console)),
    ).register(
        UpdateTagInteractive,
        lambda c: UpdateTagInteractive(
            uow=lambda: c.resolve(UnitOfWork),
            presenter=c.resolve(RichTagUpdatePresenter),
        ),
    )

    result: OperationResult[None] = container.resolve(UpdateTagInteractive).run()
    import sys

    sys.exit(0 if result.success else 1)
