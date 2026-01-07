"""
Reporting service (to be replaced by use cases).
"""

from typing import Callable

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.domain.models import (
    Account,
    Balance,
    Category,
    ExchangeRate,
    NetWorth,
)
from nwtrack.domain.value_objects import Month


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

    def get_balance_count_per_month(self) -> list[tuple[Month, int]]:
        """Get count of balance entries per month.

        Returns:
            list[tuple[Month, int]]: list of tuples Month count of balance entries.
        """
        with self._uow() as uow:
            counts = uow.balances.count_per_month()
        return counts

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
            f"Month: {month} Currency: {currency_code} Assets: {nw.assets:,} "
            f"Liabilities: {nw.liabilities:,} Net Worth: {nw.net_worth:,}"
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

    def get_all_categories(self) -> list[Category]:
        """Get a list of all categories.

        Returns:
            list[Category]: List of Category objects.
        """
        with self._uow() as uow:
            categories = uow.categories.get_all()
        return categories
