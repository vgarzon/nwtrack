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

    def update_balance(self, account_name: str, month: Month, new_amount: int) -> None:
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

        with self._uow() as uow:
            uow.balances.update(
                account_id=account.id, month=month, new_amount=new_amount
            )

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

    def get_net_worth(self, month: Month) -> NetWorth:
        """Get net worth for a specific month.

        Args:
            month (Month): Month object

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

    def count_records(self) -> dict[str, int]:
        """Count the number of records in a table.

        Args:
            table_name (str): Name of the table.

        Returns:
            int: Number of records in the table.
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
                count = repo.count_records()
                counts[label] = count
        return counts
