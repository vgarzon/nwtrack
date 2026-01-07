"""
Accounts services (to be replaced by use cases).
"""

from typing import Callable

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.domain.models import (
    Account,
    Balance,
    Category,
    Status,
)


class AccountService:
    """Account operations."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow

    def get_all(self, active_only: bool = True) -> list[Account]:
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

    def get_map_name(self) -> dict[str, Account]:
        """Get a map of account names to Account instances.

        Returns:
            dict[str, Account]: Map of account names to instances.
        """
        with self._uow() as uow:
            accounts = uow.accounts.get_dict_name()
        return accounts

    def get_map_id(self, active_only: bool = True) -> dict[int, Account]:
        """Get a map of account id to Account instances.

        Args:
            active_only (bool): Whether to include only active accounts.

        Returns:
            dict[int, Account]: Map of account id to Account objects.
        """
        with self._uow() as uow:
            accounts = uow.accounts.get_dict_id()
        return accounts

    def get_by_name(self, account_name: str) -> Account | None:
        """Get account by name.

        Args:
            account_name (str): Name of the account.

        Returns:
            Account | None: Account object if found, else None.
        """
        with self._uow() as uow:
            result = uow.accounts.get_by_name(account_name)
        if result:
            return result
        else:
            return None

    def get_by_id(self, account_id: int) -> Account | None:
        """Get account by id.

        Args:
            account_id (int): ID of the account.

        Returns:
            Account | None: Account object if found, else None.
        """
        with self._uow() as uow:
            result = uow.accounts.get_by_id(account_id)
        if result:
            return result
        return None

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

    def get_balances_by_account_id(self, account_id: int) -> list[Balance]:
        """Get all balances for an account.

        Args:
            account_id (int): Account id
        Return:
            list[Balance]: List of Balance object for the specified account.
        """
        with self._uow() as uow:
            balances = uow.balances.get_all_by_account_id(account_id)
        return balances

    def create(
        self,
        name: str,
        description: str,
        category_name: str,
        status_str: str = "active",
        currency_code: str = "USD",
    ) -> Account | None:
        """Create a new account.

        Args:
            name (str): Name of the account.
            description (str): Description of the account.
            category_name (str): Category name of the account.
            status_str (str): "active" or "inactive", defaults to "active".
            currency_code (str): Currency code of the account, defaults to "USD".

        Returns:
            Account | None: Account object of the newly created account.
        """
        # check for duplicate account name
        with self._uow() as uow:
            response = uow.accounts.get_by_name(name)
        if response:
            raise ValueError(f"Account with name '{name}' already exists.")

        # validate status
        if status_str not in [Status.ACTIVE.value, Status.INACTIVE.value]:
            raise ValueError("Status must be 'active' or 'inactive'.")

        # validate currency exists
        with self._uow() as uow:
            currency = uow.currencies.get(currency_code)
        if not currency:
            raise ValueError(f"Currency not found: '{currency_code}'.")

        # validate category exists
        with self._uow() as uow:
            category = uow.categories.get(category_name)
        if not category:
            raise ValueError(f"Category not found: '{category_name}'.")

        account = Account(
            id=0,  # Placeholder, will be set by the repository
            name=name,
            description=description,
            category_name=category_name,
            currency_code=currency_code,
            status=Status(status_str),
        )
        with self._uow() as uow:
            last_id: int = uow.accounts.insert(account)
        assert last_id > 0, "Failed to insert new account."

        with self._uow() as uow:
            response = uow.accounts.get_by_name(name)
        if not response:
            raise ValueError("Failed to retrieve newly created account.")
        account = response
        print(f"Created account '{account.name}' with ID {account.id}.")

        return account

    def delete(self, name: str) -> None:
        """Delete an account by name.

        Args:
            name (str): Name of the account to delete.
        """
        with self._uow() as uow:
            account = uow.accounts.get_by_name(name)
        if account is None:
            raise ValueError(f"Account not found: '{name}'.")

        with self._uow() as uow:
            balance_count = uow.balances.delete_by_account_id(account.id)
            account_count = uow.accounts.delete_by_id(account.id)
        assert account_count == 1, "Failed to delete account."
        print(f"Deleted {balance_count} balance entries for account '{name}'.")
        print(f"Deleted account '{name}' with ID {account.id}.")

    def update(
        self,
        name: str,
        new_name: str | None = None,
        new_description: str | None = None,
        new_category_name: str | None = None,
        new_status_str: str | None = None,
        new_currency_code: str | None = None,
    ) -> Account:
        """Update existing account.

        Args:
            name (str | None): Name of the account.
            new_name (str | None): Optional new name of the account.
            new_description (str | None): Optional description of the account.
            new_category_name (str |  None): Optional category name of the account.
            new_status_str (st | None): Optional new status, "active" or "inactive".
            new_currency_code (str | None): Optional new currency code of the account.

        Returns:
            Account: Account object of the newly created account.
        """
        with self._uow() as uow:
            account = uow.accounts.get_by_name(name)
        if account is None:
            raise ValueError(f"Account not found: '{name}'.")
        account_id = account.id

        if new_name is not None:
            with self._uow() as uow:
                existing_account = uow.accounts.get_by_name(new_name)
            if existing_account:
                raise ValueError(f"Account with name '{new_name}' already exists.")
            with self._uow() as uow:
                rowcount = uow.accounts.update_name(account_id, new_name)
            assert rowcount == 1, "Failed to update account name."

        if new_description is not None:
            if new_description.lower() == "":
                raise ValueError("Description cannot be empty.")
            with self._uow() as uow:
                rowcount = uow.accounts.update_description(account_id, new_description)
            assert rowcount == 1, "Failed to update account description."

        if new_currency_code is not None:
            with self._uow() as uow:
                currency = uow.currencies.get(new_currency_code)
            if not currency:
                raise ValueError(f"Currency not found: '{new_currency_code}'.")
            with self._uow() as uow:
                rowcount = uow.accounts.update_currency(account_id, new_currency_code)
            assert rowcount == 1, "Failed to update account description."

        if new_category_name is not None:
            with self._uow() as uow:
                category = uow.categories.get(new_category_name)
            if not category:
                raise ValueError(f"Category not found: '{new_category_name}'.")
            with self._uow() as uow:
                rowcount = uow.accounts.update_category(account_id, new_category_name)
            assert rowcount == 1, "Failed to update account category."

        if new_status_str is not None:
            if new_status_str not in [
                Status.ACTIVE.value,
                Status.INACTIVE.value,
            ]:
                raise ValueError("Status must be 'active' or 'inactive'.")
            with self._uow() as uow:
                rowcount = uow.accounts.update_status(
                    account_id, Status(new_status_str)
                )
            assert rowcount == 1, "Failed to update account status."

        with self._uow() as uow:
            account = uow.accounts.get_by_id(account_id)
        assert account is not None, "Failed to retrieve updated account."
        print(f"Updated account with ID {account.id}.")

        return account
