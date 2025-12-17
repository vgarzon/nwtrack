"""
Service layer for managing user operations.
"""

from nwtrack.repos import (
    SQLiteCurrencyRepository,
    SQLiteAccountTypeRepository,
    SQLiteExchangeRateRepository,
    NwTrackRepository,
)
from nwtrack.fileio import csv_file_to_list_dict


class NWTrackService:
    """Service layer for nwtrack operations."""

    def __init__(
        self,
        currency_repo: SQLiteCurrencyRepository,
        account_types_repo: SQLiteAccountTypeRepository,
        exchange_rate_repo: SQLiteExchangeRateRepository,
        repo: NwTrackRepository,
    ) -> None:
        self._currency_repo = currency_repo
        self._account_type_repo = account_types_repo
        self._exchange_rate_repo = exchange_rate_repo
        self._repo = repo

    def initialize_reference_data(
        self, currencies_path: str, account_types_path: str
    ) -> None:
        """Initialize reference data in the database.

        Args:
            currencies_path (str): Path to the currencies CSV file.
            account_types_path (str): Path to the account types CSV file.
        """
        print("Service: Initializing reference data.")
        currencies = csv_file_to_list_dict(currencies_path)
        account_types = csv_file_to_list_dict(account_types_path)
        self._currency_repo.insert_many(currencies)
        self._account_type_repo.insert_many(account_types)

    def insert_sample_data(self, accounts_path: str, balances_path: str) -> None:
        """Insert sample accounts and balances data.

        Args:
            accounts_path (str): Path to the accounts CSV file.
            balances_path (str): Path to the balances CSV file.

        File formats:
          - accounts.csv: name, description, type, currency, status
          - balances.csv: Date, year, month, <account_name_1>, <acct_name_2>, ...

        Notes :
          - Liabilities are assumed to be in negative amounts and will be stored as
            positive.
          - Account names in the header must match those in the accounts.csv file.
        """
        print("Service: Inserting sample data.")
        accounts_data = csv_file_to_list_dict(accounts_path)
        balances_data = csv_file_to_list_dict(balances_path)
        self._repo.insert_accounts(accounts_data)

        balances = []
        for row in balances_data:
            for key in row:
                if key.lower() in ("date", "year", "month"):
                    continue
                account_id = self._repo.get_account_id_by_name(key)
                if not account_id:
                    raise ValueError(f"Account name '{key}' not found in accounts.")
                bal = {
                    "account_id": int(account_id),
                    "month": f"{row['year']}-{int(row['month']):0>2}",
                    "amount": abs(int(row[key])) if row[key] else 0,
                }
                balances.append(bal)

        self._repo.insert_balances(balances)

    def insert_exchange_rates(self, exchange_rates_path: str) -> None:
        """Insert exchange rate data from a CSV file.

        Args:
            exchange_rates_path (str): Path to the exchange rates CSV file.
        """
        print(f"Service: Inserting exchange rates from {exchange_rates_path}.")
        exchange_rates_data = csv_file_to_list_dict(exchange_rates_path)
        assert exchange_rates_data, "No exchange rates data found."

        # check that currency codes in the file exist in the database
        currency_codes = self._currency_repo.get_codes()
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

        self._exchange_rate_repo.insert_many(rates)

    def update_balance(self, account_name: str, month: str, new_amount: int) -> None:
        """Update the balance for a specific account on a given month.

        Args:
            account_name (str): Name of the account.
            month (str): Month of the balance to update, format "YYYY-MM".
            new_ammount (int): New balance amount.
        """
        account_id = self._repo.get_account_id_by_name(account_name)
        if not account_id:
            raise ValueError(f"Account name '{account_name}' not found.")

        self._repo.update_account_balance(
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
        if not self._repo.check_month_exists_in_balances(month):
            raise ValueError("No balances found for month.")
        if month_int == 12:
            next_month = f"{year_int + 1}-01"
        else:
            next_month = f"{year_int}-{month_int + 1:02d}"
        print(f"Service: Copying balances from {month} to {next_month}.")
        self._repo.copy_balances_to_next_month(month)

    def print_active_accounts(self) -> None:
        """Print a table of all active accounts."""
        accounts = self._repo.get_active_accounts()
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
        results = self._repo.get_net_worth_on_month(month, currency)
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
        nw_hist = self._repo.get_net_worth_history()
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
        all_currency_codes = self._currency_repo.get_codes()
        if currency not in all_currency_codes:
            raise ValueError(f"Currency code '{currency}' not found in database.")
        rate = self._exchange_rate_repo.get(month, currency)
        if rate:
            print(f"Exchange rate {currency} to USD on {month}: {rate}")
        else:
            print(f"No exchange rate found for {currency} on {month}.")

    def print_exchange_rate_history(self, currency: str) -> None:
        """Print exchange rate history.

        Args:
            currency (str): Currency code
        """
        all_currency_codes = self._currency_repo.get_codes()
        if currency not in all_currency_codes:
            raise ValueError(f"Currency code '{currency}' not found in database.")
        rates = self._exchange_rate_repo.history(currency)
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
        balances = self._repo.get_balances_on_month(month, active_only)
        print("account_name, month, amount")
        for bal in balances:
            print(f"{bal['account_name']}, {bal['month']}, {bal['amount']}")

    def close_repo(self) -> None:
        """Close open repos."""
        self._repo.close_db_connection()
