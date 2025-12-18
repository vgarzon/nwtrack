"""
Service layer for managing user operations using unit of work pattern.
"""

from nwtrack.unitofwork import SQLiteUnitOfWork
from nwtrack.fileio import csv_file_to_list_dict
from nwtrack.models import (
    # Account,
    # Balance,
    Category,
    Side,
    Currency,
    # ExchangeRate,
)


class NWTrackService:
    """Service layer for nwtrack operations with unit of work pattern."""

    def __init__(self, uow: SQLiteUnitOfWork) -> None:
        self._uow = uow

    def initialize_reference_data(
        self, currencies_path: str, categories_path: str
    ) -> None:
        """Initialize reference data in the database.

        Args:
            currencies_path (str): Path to currencies CSV file.
            categories_path (str): Path to categories CSV file.
        """
        print("Service: Initializing reference data.")
        currencies = csv_file_to_list_dict(currencies_path)
        categories = csv_file_to_list_dict(categories_path)

        currencies = [Currency(**c) for c in currencies]
        categories = [
            Category(name=at["name"], side=Side(at["side"])) for at in categories
        ]
        with self._uow() as uow:
            uow.currency.insert_many(currencies)
            uow.category.insert_many(categories)

    def insert_sample_data(self, accounts_path: str, balances_path: str) -> None:
        """Insert sample accounts and balances data.

        Args:
            accounts_path (str): Path to the accounts CSV file.
            balances_path (str): Path to the balances CSV file.

        File formats:
          - accounts.csv: name, description, category, currency, status
          - balances.csv: Date, year, month, <account_name_1>, <acct_name_2>, ...

        Notes :
          - Liabilities are assumed to be in negative amounts and will be stored as
            positive.
          - Account names in the header must match those in the accounts.csv file.
        """
        print("Service: Inserting sample data.")
        accounts_data = csv_file_to_list_dict(accounts_path)
        balances_data = csv_file_to_list_dict(balances_path)
        with self._uow() as uow:
            uow.account.insert_many(accounts_data)

        balances = []
        for row in balances_data:
            for key in row:
                if key.lower() in ("date", "year", "month"):
                    continue
                with self._uow() as uow:
                    account_id = uow.account.get_id(key)
                if not account_id:
                    raise ValueError(f"Account name '{key}' not found in accounts.")
                bal = {
                    "account_id": int(account_id),
                    "month": f"{row['year']}-{int(row['month']):0>2}",
                    "amount": abs(int(row[key])) if row[key] else 0,
                }
                balances.append(bal)

        with self._uow() as uow:
            uow.balance.insert_many(balances)

    def insert_exchange_rates(self, exchange_rates_path: str) -> None:
        """Insert exchange rate data from a CSV file.

        Args:
            exchange_rates_path (str): Path to the exchange rates CSV file.
        """
        print(f"Service: Inserting exchange rates from {exchange_rates_path}.")
        exchange_rates_data = csv_file_to_list_dict(exchange_rates_path)
        assert exchange_rates_data, "No exchange rates data found."

        # check that currency codes in the file exist in the database
        with self._uow() as uow:
            currency_codes = uow.currency.get_codes()
        row = exchange_rates_data[0]
        for key in row:
            if key.lower() in ("date", "year", "month"):
                continue
            if key not in currency_codes:
                raise ValueError(f"Currency code '{key}' not found in database.")

        rates = []
        for row in exchange_rates_data:
            for key in row:
                if key.lower() in ("date", "year", "month"):
                    continue
                if not row[key]:
                    continue
                rate = {
                    "currency": key,
                    "month": f"{row['year']}-{int(row['month']):0>2}",
                    "rate": float(row[key]),
                }
                rates.append(rate)

        with self._uow() as uow:
            uow.exchange_rate.insert_many(rates)

    def update_balance(self, account_name: str, month: str, new_amount: int) -> None:
        """Update the balance for a specific account on a given month.

        Args:
            account_name (str): Name of the account.
            month (str): Month of the balance to update, format "YYYY-MM".
            new_ammount (int): New balance amount.
        """
        with self._uow() as uow:
            account_id = uow.account.get_id(account_name)
        if not account_id:
            raise ValueError(f"Account name '{account_name}' not found.")

        with self._uow() as uow:
            uow.balance.update(
                account_id=account_id, month=month, new_amount=new_amount
            )

    def copy_balances_to_next_month(self, month: str) -> None:
        """Copy all active account balances from one month to the next.

        Args:
            month (str): Month of the source month, format "YYYY-MM".
        """
        # check that month is valid
        year_int, month_int = map(int, month.split("-"))
        if month_int < 1 or month_int > 12:
            raise ValueError(f"Invalid month: {month_int}. Must be between 1 and 12.")
        with self._uow() as uow:
            if not uow.balance.check_month(month):
                raise ValueError("No balances found for month.")
        if month_int == 12:
            next_month = f"{year_int + 1}-01"
        else:
            next_month = f"{year_int}-{month_int + 1:02d}"
        print(f"Service: Copying balances from {month} to {next_month}.")
        with self._uow() as uow:
            uow.balance.roll_forward(month)

    def print_active_accounts(self) -> None:
        """Print a table of all active accounts."""
        with self._uow() as uow:
            accounts = uow.account.get_active()
        print("Active accounts:")
        for account in accounts:
            print(f"Account ID: {account['id']}, Name: {account['name']}")

    def print_net_worth_on_month(self, month: str, currency: str = "USD") -> None:
        """Print net worth on a specific month.

        Args:
            month (str): Month in "YYYY-MM" format
            currency (str): Currency code (default: "USD")

        Returns:
            None
        """
        with self._uow() as uow:
            results = uow.net_worth.get(month, currency)
        assert len(results) == 1, (
            f"Expected exactly one record for {month} in {currency}"
        )
        assets, liabilities, net_worth = results[0]
        print(
            f"Month: {month}, Currency: {currency}, Assets: {assets}, "
            f"Liabilities: {liabilities}, Net Worth: {net_worth}"
        )

    def print_net_worth_history(self) -> None:
        """Print net worth history."""
        with self._uow() as uow:
            nw_hist = uow.net_worth.history()
        print("month, assets, liabilities, net_worth")
        for res in nw_hist:
            print(
                f"{res['month']}, {res['total_assets']}, "
                f"{res['total_liabilities']}, {res['net_worth']}"
            )

    def print_exchange_rate(self, currency: str, month: str) -> None:
        """Print exchange rates for a specific currency and month

        Args:
            currency (str): Currency code
            month (str): Month in "YYYY-MM" format
        """
        with self._uow() as uow:
            all_currency_codes = uow.currency.get_codes()
            if currency not in all_currency_codes:
                raise ValueError(f"Currency code '{currency}' not found in database.")
            rate = uow.exchange_rate.get(month, currency)
        if rate:
            print(f"Exchange rate {currency} to USD on {month}: {rate}")
        else:
            print(f"No exchange rate found for {currency} on {month}.")

    def print_exchange_rate_history(self, currency: str) -> None:
        """Print exchange rate history.

        Args:
            currency (str): Currency code
        """
        with self._uow() as uow:
            all_currency_codes = uow.currency.get_codes()
            if currency not in all_currency_codes:
                raise ValueError(f"Currency code '{currency}' not found in database.")
            rates = uow.exchange_rate.history(currency)
        print("currency, month, rate")
        for r in rates:
            print(f"{r['currency']}, {r['month']}, {r['rate']}")

    def print_balances_on_month(self, month: str, active_only: bool = True) -> None:
        """Print all account balances at a specific month.

        Args:
            month (str): Month in "YYYY-MM" format
            active_only (bool): Whether to include only active accounts
        """
        # validate month
        year_int, month_int = map(int, month.split("-"))
        if month_int < 1 or month_int > 12:
            raise ValueError(f"Invalid month: {month_int}. Must be between 1 and 12.")
        with self._uow() as uow:
            balances = uow.balance.get_month(month, active_only)
        print("account_name, month, amount")
        for bal in balances:
            print(f"{bal['account_name']}, {bal['month']}, {bal['amount']}")
