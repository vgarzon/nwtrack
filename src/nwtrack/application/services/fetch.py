"""
Fetch service module for read-only data retrieval.
"""

from typing import Callable
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.domain.models import Account, Balance, Category, Currency


class FetchService:
    """Read-only data fetching service."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow

    def get_accounts(self, active_only: bool = True) -> list[Account]:
        """Get a list of all accounts.

        Args:
            active_only (bool): Whether to include only active accounts.

        Returns:
            list[Account]: List of active Account objects.
        """
        if active_only:
            with self._uow() as uow:
                accounts = uow.accounts.get_active()
        else:
            with self._uow() as uow:
                accounts = uow.accounts.get_all()
        return accounts

    def get_all_categories(self) -> list[Category]:
        """Get a list of all categories.

        Returns:
            list[Category]: List of Category objects.
        """
        with self._uow() as uow:
            categories = uow.categories.get_all()
        return categories

    def get_all_currencies(self) -> list[Currency]:
        """Get a list of all currencies.

        Returns:
            list[Currency]: List of currency codes.
        """
        with self._uow() as uow:
            currencies = uow.currencies.get_all()
        return currencies

    def get_category_by_account_id(self, account_id: int) -> Category | None:
        """Get category side for a given account ID.

        Args:
            account_id (int): Account ID

        Returns:
            Category | None: Category instance if found, else None.
        """
        with self._uow() as uow:
            account = uow.accounts.get_by_id(account_id)
        if not account:
            return None
        with self._uow() as uow:
            category = uow.categories.get(account.category_name)
        return category

    def get_account_by_id(self, account_id: int) -> Account | None:
        """Get account by ID.

        Args:
            account_id (int): Account ID

        Returns:
            Account | None: Account instance if found, else None.
        """
        with self._uow() as uow:
            account = uow.accounts.get_by_id(account_id)
        return account

    def get_balance_by_id(self, balance_id: int) -> Balance | None:
        """Get balance by ID.

        Args:
            balance_id (int): Balance ID

        Returns:
            Balance | None: Balance instance if found, else None.
        """
        with self._uow() as uow:
            balance = uow.balances.get_by_id(balance_id)
        return balance

    def get_category_by_name(self, category_name: str) -> Category | None:
        """Get category by name.

        Args:
            category_name (str): Category name

        Returns:
            Category | None: Category instance if found, else None.
        """
        with self._uow() as uow:
            category = uow.categories.get(category_name)
        return category
