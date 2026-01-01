"""
Service layer for managing user operations using unit of work pattern.
"""

from typing import Callable

from nwtrack.fileio import csv_to_records
from nwtrack.models import (
    Account,
    Balance,
    ExchangeRate,
    Month,
    NetWorth,
    Status,
)
from nwtrack.unitofwork import UnitOfWork


class InitDataService:
    """Initialize reference and sample data in the database."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow

    def insert_data_from_csv(self, file_paths: dict[str, str]) -> None:
        """Insert data from CSV files into the database.

        Args:
            file_paths (dict[str, str]): Paths to the CSV files indexed by repo name.
                Expected keys: 'currencies', 'categories', 'accounts', 'balances',
                    'exchange_rates'

        File formats:
          - currencies: code, description
          - categories: name, description, side (asset, liability)
          - accounts: name, description, category, currency, status
          - balances: date, year, month, <account_name_1>, <acct_name_2>, ...
          - exchange_rates: date, year, month, <currency_code_1>, <code_2>, ...

        Note:
          - Liabilities are stored as positive amounts.
        """
        print("InitDataService: Inserting data from CSV files.")
        repo_names = [  # TODO: Use RepoRegistry (pending)
            "currencies",
            "categories",
            "accounts",
            "balances",
            "exchange_rates",
        ]
        assert all(name in repo_names for name in file_paths), (
            f"Missing required file paths. Expected keys: {', '.join(repo_names)}"
        )
        records = {name: csv_to_records(path) for name, path in file_paths.items()}

        # NOTE: storing liabilities as positive amounts
        for row in records["balances"]:
            row["amount"] = abs(int(row["amount"]))

        self._insert_records(records)

    def _load_records_from_csv(self, file_paths: dict[str, str]) -> dict[str, list]:
        """Load records from a collection of CSV files indexed by repo name.

        Args:
            file_paths (dict[str, str]): Path to the CSV files indexed by repo name.

        Returns:
            list[dict]: Collection of records indexed by repo name.
        """
        return {name: csv_to_records(path) for name, path in file_paths.items()}

    def _insert_records(self, records: dict[str, list[dict]]) -> None:
        """Insert records into the database using unit of work pattern.

        Args:
            records (dict[str, list[dict]]): Records indexed by repo name.
        """
        with self._uow() as uow:
            for name in records:
                repo = getattr(uow, name)
                entities = repo.hydrate_many(records[name])
                repo.insert_many(entities)

    def _records_to_entities(self, records: dict[str, list[dict]]) -> dict[str, list]:
        """Hydrate records into entities using unit of work pattern.

        Args:
            records (dict[str, list[dict]]): Records indexed by repo name.
        Returns:
            dict[str, list]: Hydrated entities indexed by repo name.
        """
        entities: dict[str, list] = {}
        with self._uow() as uow:
            for name in records:
                repo = getattr(uow, name)
                entities[name] = repo.hydrate_many(records[name])
        return entities

    def _insert_entities(self, entities: dict[str, list]) -> None:
        """Insert entities into the database using unit of work pattern.

        Args:
            entities (dict[str, list]): Entities indexed by repo name.
        """
        with self._uow() as uow:
            for name in entities:
                repo = getattr(uow, name)
                repo.insert_many(entities[name])


class UpdateService:
    """Service layer to update balance and other data using unit of work pattern."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow

    def update_balance(self, account_id: int, month: Month, new_amount: int) -> None:
        """Update the balance for a specific account on a given month.

        Args:
            account_id (int): ID of the account.
            month (Month): Month of the balance to update.
            new_ammount (int): New balance amount.
        """
        with self._uow() as uow:
            uow.balances.update(
                account_id=account_id, month=month, new_amount=new_amount
            )

    def update_balance_account_name(
        self, account_name: str, month: Month, new_amount: int
    ) -> None:
        """Update the balance for a specific account on a given month.

        Args:
            account_name (str): Name of the account.
            month (Month): Month of the balance to update.
            new_ammount (int): New balance amount.
        """
        with self._uow() as uow:
            account_map = uow.accounts.get_dict_name()
        account = account_map.get(account_name, None)
        if not account:
            raise ValueError(f"Account name '{account_name}' not found.")

        self.update_balance(account_id=account.id, month=month, new_amount=new_amount)

    def roll_balances_forward(self, month: Month) -> None:
        """Copy all active account balances from one month to the next.

        Args:
            month (Month): Month of the source month.
        """
        # check that month is valid
        with self._uow() as uow:
            if not uow.balances.check_month(month):
                raise ValueError("No balances found for month.")
        next_month = month.increment()
        print(f"Service: Copying balances from {month} to {next_month}.")
        with self._uow() as uow:
            uow.balances.roll_forward(month)


class ReportService:
    """Printing and reporting service using unit of work pattern."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow

    def get_accounts(self, active_only: bool = True) -> list[Account]:
        """Get a list of all active accounts.

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

    def get_map_name_to_account(self, active_only: bool = True) -> dict[str, Account]:
        """Get a map of account names to Account objects.

        Args:
            active_only (bool): Whether to include only active accounts.

        Returns:
            dict[str, Account]: Map of account names to Account objects.
        """
        accounts = self.get_accounts(active_only)
        account_map = {acc.name: acc for acc in accounts}
        return account_map

    def get_map_id_to_account(self, active_only: bool = True) -> dict[int, Account]:
        """Get a map of account id to Account objects.

        Args:
            active_only (bool): Whether to include only active accounts.

        Returns:
            dict[int, Account]: Map of account id to Account objects.
        """
        accounts = self.get_accounts(active_only)
        account_map = {acc.id: acc for acc in accounts}
        return account_map

    def print_accounts(self, active: bool = True) -> None:
        """Print a table of all active accounts.

        Args:
            active (bool): Whether to include only active accounts.
        """
        accounts = self.get_accounts(active_only=active)
        print("Accounts:")
        print("id, name, category, status")
        for account in accounts:
            print(account.id, account.name, account.category_name, account.status)

    def get_balance(self, month: Month, account_name: str) -> Balance:
        """Get balance for an account on a specific month.

        Args:
            month (Month): Month object
            account_name (str): Name of the account

        Return:
            Balance: Balance object for the specified account and month.
        """
        with self._uow() as uow:
            balance = uow.balances.get(month, account_name)
        return balance

    def get_balance_for_account_id(self, month: Month, account_id: int) -> Balance:
        """Get balance for an account on a specific month.

        Args:
            month (Month): Month object
            account_id (int): Account id

        Return:
            Balance: Balance object for the specified account and month.
        """
        with self._uow() as uow:
            balance = uow.balances.get_by_account_id(month, account_id)
        return balance

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

    def get_month_balances(
        self, month: Month, active_only: bool = True
    ) -> list[Balance]:
        """Get balance all accounts on a specific month.

        Args:
            month (Month): Month object
            active_only (bool): Whether to include only active accounts

        Return:
            list[Balance]: List of Balance object for the specified account and month.
        """
        with self._uow() as uow:
            balances = uow.balances.get_month(month, active_only)
        return balances

    def get_balances_sample(self, limit: int = 5) -> list[Balance]:
        """Get sample balances for testing.

        Returns:
            list[Balance]: List of sample Balance objects.
        """
        with self._uow() as uow:
            balances = uow.balances.fetch_sample(limit)
        return balances

    def print_balance(self, month: Month, account_name: str) -> None:
        """Print account balance for a specific month.

        Args:
            month (Month): Month object
            account_name (str): Name of the account
        """
        bal = self.get_balance(month, account_name)
        print("Balance for", account_name, "on", str(bal.month), "=", bal.amount)

    def print_month_balances(self, month: Month, active_only: bool = True) -> None:
        """Print account balances on a specific month.

        Args:
            month (Month): Month object
            active_only (bool): Whether to include only active accounts
        """
        balances = self.get_month_balances(month, active_only)
        accounts = self.get_accounts(active_only)
        account_map = {acc.id: acc for acc in accounts}
        print("id, account_id, month, amount")
        for bal in balances:
            account_name = account_map[bal.account_id].name
            print(bal.id, account_name, str(bal.month), bal.amount)

    def get_net_worth(self, month: Month, currency_code: str = "USD") -> NetWorth:
        """Get net worth for a specific month and currency

        Args:
            month (Month): Month object
            currency_code (str): Currency code (default: "USD")

        Returns:
            NetWorth: NetWorth object for the specified month.
        """
        with self._uow() as uow:
            nw = uow.net_worth.get(month)
        return nw

    def get_net_worth_history(self) -> list[NetWorth]:
        """Get net worth history.

        Returns:
            list[NetWorth]: List of net worth records.
        """
        with self._uow() as uow:
            nw_hist = uow.net_worth.history()
        return nw_hist

    def print_net_worth(self, month: Month, currency_code: str = "USD") -> None:
        """Print net worth on a specific month.

        Args:
            month (Month): Month object
            currency (str): Currency code (default: "USD")

        Returns:
            None
        """
        with self._uow() as uow:
            nw = uow.net_worth.get(month, currency_code)
        if not nw:
            raise ValueError(f"No net worth data found for {month} in {currency_code}")
        print(
            f"Month: {month}, Currency: {currency_code}, Assets: {nw.assets}, "
            f"Liabilities: {nw.liabilities}, Net Worth: {nw.net_worth}"
        )

    def print_net_worth_history(self) -> None:
        """Print net worth history."""
        nw_hist = self.get_net_worth_history()
        print("month, assets, liabilities, net_worth")
        for nw in nw_hist:
            print(nw.month, nw.assets, nw.liabilities, nw.net_worth)

    def get_exchange_rate(
        self, month: Month, currency_code: str
    ) -> ExchangeRate | None:
        """Get exchange rate for given currency and month.

        Args:
            month (Month): Month objectk
            currency_code (str): Currency code

        Returns:
            ExchangeRate | None
        """
        with self._uow() as uow:
            all_currency_codes = uow.currencies.get_codes()
        if currency_code not in all_currency_codes:
            raise ValueError(f"Currency '{currency_code}' not found in database.")
        with self._uow() as uow:
            rate = uow.exchange_rates.get(month, currency_code)
        return rate

    def get_exchange_rate_history(self, currency_code: str) -> list[ExchangeRate]:
        """Get exchange rate history for given currency.

        Args:
            currency_code (str): Currency code

        Returns:
            list[ExchangeRate]: List of ExchangeRate objects
        """
        with self._uow() as uow:
            all_currency_codes = uow.currencies.get_codes()
        if currency_code not in all_currency_codes:
            raise ValueError(f"Currency '{currency_code}' not found in database.")
        with self._uow() as uow:
            rates = uow.exchange_rates.get_currency(currency_code)
        return rates

    def get_month_exchange_rates(self, month: Month) -> list[ExchangeRate]:
        """Get exchange rates for all currencies on a specific month.

        Args:
            month (Month): Month object

        Returns:
            list[ExchangeRate]: List of ExchangeRate objects
        """
        with self._uow() as uow:
            rates = uow.exchange_rates.get_month(month)
        return rates

    def print_exchange_rate(self, month: Month, currency_code: str) -> None:
        """Print exchange rates for a specific currency and month

        Args:
            month (Month): Month object
            currency_code (str): Currency code
        """
        rate = self.get_exchange_rate(month, currency_code)
        if rate:
            print(f"Exchange rate {currency_code} to USD on {month}: {rate.rate}")
        else:
            print(f"No exchange rate found for {currency_code} on {str(month)}.")

    def print_exchange_rate_history(self, currency_code: str) -> None:
        """Print exchange rate history.

        Args:
            currency (str): Currency code
        """
        rates = self.get_exchange_rate_history(currency_code)
        print("currency, month, rate")
        for r in rates:
            print(r.currency_code, str(r.month), r.rate)

    def count_entries(self) -> dict[str, int]:
        """Count the number of repository entries.

        Returns:
            int: Number of records in each repository.
        """
        # TODO: refactor to use RepoRegistry (pending)
        repo_labels = [
            "currencies",
            "categories",
            "accounts",
            "balances",
            "exchange_rates",
        ]
        with self._uow() as uow:
            counts = {}
            for label in repo_labels:
                repo = getattr(uow, label)
                count = repo.count()
                counts[label] = count
        return counts


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
            rowcount = uow.accounts.insert(account)
        assert rowcount == 1, "Failed to insert new account."

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
