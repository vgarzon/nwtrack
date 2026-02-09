"""
Create category interactively.
"""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import CategoryCreationPresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Category

logger = logging.getLogger(__name__)


class CreateCategoryInteractive:
    """Create category interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        fetcher: FetchService,
        presenter: CategoryCreationPresenter,
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._presenter = presenter

    def run(self) -> OperationResult[str]:
        """Run the category creation workflow.

        Returns:
            OperationResult with category name if successful
        """
        logger.info("Starting Interactive Category Creator")

        # Show header and existing categories
        self._presenter.show_header()
        categories = self._fetcher.get_all_categories()
        self._presenter.display_categories(categories)

        # Collect category data
        data = self._presenter.collect_category_data()
        if data is None:
            logger.warning("Category creation cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        # Validate data
        if not self._validate_data(data):
            _msg = "Invalid category data provided."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        # Show preview and confirm
        if not self._presenter.show_preview_and_confirm(data):
            logger.info("Category creation cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="User declined")

        # Insert category
        category_name = self._insert_category(data)
        if category_name is None:
            _msg = "Category creation failed."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        # Validate created category
        is_valid, validation_msg = self._validate_created_category(data, category_name)
        if not is_valid:
            logger.error("Created category validation failed: %s", validation_msg)
            self._presenter.show_error(f"Validation failed: {validation_msg}")
            return OperationResult(success=False, error_message=validation_msg)

        # Show success
        categories = self._fetcher.get_all_categories()
        self._presenter.show_success(category_name, categories)
        logger.info("Finished Interactive Category Creator")

        return OperationResult(success=True, data=category_name)

    def _insert_category(self, category: Category) -> str | None:
        """Insert new category into the database.

        Args:
            category: Category data to insert

        Returns:
            The name of the created category, or None if failed
        """
        with self._uow() as uow:
            try:
                row_count = uow.categories.insert(category)
            except ValueError as e:
                logger.exception("Error inserting category: %s", e)
                uow.rollback()
                return None

        if row_count != 1:
            logger.error("Failed to insert category: %s", category.name)
            return None

        logger.info("Inserted new category: %s", category.name)
        return category.name

    def _validate_data(self, data: Category) -> bool:
        """Validate collected category data.

        Args:
            data: Collected category data

        Returns:
            True if valid, False otherwise
        """
        all_categories = self._fetcher.get_all_categories()
        for category in all_categories:
            if category.name.lower() == data.name.lower():
                logger.error("Category name '%s' already exists.", data.name)
                self._presenter.show_duplicate_error(data.name)
                return False
        return True

    def _validate_created_category(
        self, data: Category, category_name: str
    ) -> tuple[bool, str]:
        """Validate that the created category matches input data.

        Args:
            data: Input category data
            category_name: Category name

        Returns:
            Validation result and message
        """
        result: Category | None = self._fetcher.get_category_by_name(category_name)
        if result is None:
            _msg = f"Error retrieving category '{category_name}'."
            return False, _msg
        category: Category = result

        if category.name != data.name:
            return False, "Category name mismatch."
        if category.side != data.side:
            return False, "Category side mismatch."

        return True, "Category validated successfully."


def main() -> None:
    """Main entry point for category creation script."""
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.category_presenters import (
        RichCategoryCreationPresenter,
    )

    load_dotenv()
    setup_logging()

    container = build_base_container()
    container.register(
        Console,
        lambda _: Console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        RichCategoryCreationPresenter,
        lambda c: RichCategoryCreationPresenter(console=c.resolve(Console)),
    ).register(
        CreateCategoryInteractive,
        lambda c: CreateCategoryInteractive(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=c.resolve(FetchService),
            presenter=c.resolve(RichCategoryCreationPresenter),
        ),
    )

    result: OperationResult[str] = container.resolve(CreateCategoryInteractive).run()
    import sys

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
