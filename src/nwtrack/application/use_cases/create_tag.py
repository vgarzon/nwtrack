"""Create tag interactively."""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import TagCreationPresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases._tag_admin import (
    list_tag_items,
    normalize_tag_name,
    normalized_tag,
)
from nwtrack.domain.models import Tag

logger = logging.getLogger(__name__)


class CreateTagInteractive:
    """Create tag interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        presenter: TagCreationPresenter,
    ) -> None:
        self._uow = uow
        self._presenter = presenter

    def run(self) -> OperationResult[str]:
        """Run the tag creation workflow."""
        logger.info("Starting Interactive Tag Creator")
        self._presenter.show_header()
        self._presenter.display_tags(self._list_items())

        raw_data = self._presenter.collect_tag_data()
        if raw_data is None:
            logger.warning("Tag creation cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        data = normalized_tag(raw_data)
        if not data.name:
            self._presenter.show_empty_name_error()
            return OperationResult(
                success=False,
                error_message="Tag name cannot be empty after normalization",
            )

        if self._is_duplicate_name(data.name):
            logger.error("Tag name '%s' already exists.", data.name)
            self._presenter.show_duplicate_error(data.name)
            return OperationResult(
                success=False,
                error_message="Duplicate tag name",
            )

        if not self._presenter.show_preview_and_confirm(data):
            logger.info("Tag creation cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="User declined")

        tag_name = self._insert_tag(data)
        if tag_name is None:
            message = "Tag creation failed."
            logger.error(message)
            self._presenter.show_error(message)
            return OperationResult(success=False, error_message=message)

        is_valid, validation_msg = self._validate_created_tag(data, tag_name)
        if not is_valid:
            logger.error("Created tag validation failed: %s", validation_msg)
            self._presenter.show_error(f"Validation failed: {validation_msg}")
            return OperationResult(success=False, error_message=validation_msg)

        self._presenter.show_success(tag_name, self._list_items())
        logger.info("Finished Interactive Tag Creator")
        return OperationResult(success=True, data=tag_name)

    def _list_items(self):
        with self._uow() as uow:
            return list_tag_items(uow)

    def _insert_tag(self, tag: Tag) -> str | None:
        with self._uow() as uow:
            try:
                tag_id = uow.tags.insert(tag)
            except ValueError as exc:
                logger.exception("Error inserting tag: %s", exc)
                uow.rollback()
                return None
        if tag_id <= 0:
            logger.error("Failed to insert tag: %s", tag.name)
            return None
        return tag.name

    def _is_duplicate_name(self, tag_name: str) -> bool:
        with self._uow() as uow:
            tags = uow.tags.get_all()
        normalized_name = normalize_tag_name(tag_name)
        return any(tag.name == normalized_name for tag in tags)

    def _validate_created_tag(self, data: Tag, tag_name: str) -> tuple[bool, str]:
        with self._uow() as uow:
            result = uow.tags.get_by_name(tag_name)
        if result is None:
            return False, f"Error retrieving tag '{tag_name}'."
        if result.name != data.name:
            return False, "Tag name mismatch."
        if result.description != data.description:
            return False, "Tag description mismatch."
        return True, "Tag validated successfully."


def main() -> None:
    """Main entry point for tag creation script."""
    from rich.console import Console

    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.entrypoints.cli.adapters.tag_presenters import (
        RichTagCreationPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    container = build_base_container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        RichTagCreationPresenter,
        lambda c: RichTagCreationPresenter(console=c.resolve(Console)),
    ).register(
        CreateTagInteractive,
        lambda c: CreateTagInteractive(
            uow=lambda: c.resolve(UnitOfWork),
            presenter=c.resolve(RichTagCreationPresenter),
        ),
    )

    result: OperationResult[str] = container.resolve(CreateTagInteractive).run()
    import sys

    sys.exit(0 if result.success else 1)
