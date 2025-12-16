"""
Service layer for managing user operations.
"""

from nwtrack.config import Config
from nwtrack.repos import NwTrackRepository
from nwtrack.fileio import csv_file_to_list_dict


class NWTrackService:
    """Service layer for nwtrack operations."""

    def __init__(self, config: Config, repo: NwTrackRepository) -> None:
        self._config = config
        self._repo = repo

    def init_database(self) -> None:
        """Initialize the database schema."""
        print("Service: Initializing database.")
        ddl_path = self._config.db_ddl_path
        with open(ddl_path, "r", encoding="utf-8") as f:
            ddl_script = f.read()
        self._repo.init_database_ddl(ddl_script)

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
        self._repo.init_currencies(currencies)
        self._repo.init_account_types(account_types)

    def update_balance(
        self, account_name: str, year: int, month: int, new_amount: int
    ) -> None:
        """Update the balance for a specific account at a given year and month.

        Args:
            account_name (str): Name of the account.
            year (int): Year of the balance to update.
            month (int): Month of the balance to update.
            new_ammount (int): New balance amount.
        """
        account_id = self._repo.get_account_id_by_name(account_name)
        if not account_id:
            raise ValueError(f"Account name '{account_name}' not found.")

        self._repo.update_account_balance(
            account_id=account_id, year=year, month=month, new_amount=new_amount
        )

    def insert_sample_data(self, accounts_path: str, balances_path: str) -> None:
        """Insert sample data into the database.

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
                    "year": int(row["year"]),
                    "month": int(row["month"]),
                    "amount": abs(int(row[key])) if row[key] else 0,
                }
                balances.append(bal)

        self._repo.insert_balances(balances)

    def insert_exchange_rates(self, exchange_rates_path: str) -> None:
        """Insert exchange rates from a CSV file.

        Args:
            exchange_rates_path (str): Path to the exchange rates CSV file.
        """
        print(f"Service: Inserting exchange rates from {exchange_rates_path}.")
        exchange_rates_data = csv_file_to_list_dict(exchange_rates_path)
        assert exchange_rates_data, "No exchange rates data found."

        # check that currency codes in the file exist in the database
        currency_codes = self._repo.get_all_currency_codes()
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
                    "year": int(row["year"]),
                    "month": int(row["month"]),
                    "rate": float(row[key]),
                }
                rates.append(rate)

        self._repo.insert_exchange_rates(rates)

    def copy_balances_to_next_month(self, year: int, month: int) -> None:
        """Copy all active account balances from one month to the next.

        Args:
            year (int): Year of the source month.
            month (int): Month of the source month.
        """
        # check that month is valid
        if month < 1 or month > 12:
            raise ValueError(f"Invalid month: {month}. Must be between 1 and 12.")
        if not self._repo.check_year_month_exists_in_balances(year, month):
            raise ValueError(f"No balances found for {year}-{month:02d}.")
        print(
            f"Service: Copying balances from {year}-{month:02d} "
            f"to {year}-{month + 1:02d}."
        )
        self._repo.copy_balances_to_next_month(year, month)

    def print_active_accounts(self) -> None:
        """Print a table of all active accounts."""
        accounts = self._repo.get_active_accounts()
        print("Active accounts:")
        for account in accounts:
            print(f"Account ID: {account['id']}, Name: {account['name']}")

    def print_net_worth_at_year_month(
        self, year: int, month: int, currency: str = "USD"
    ) -> None:
        """Print net worth at a specific year and month.

        Args:
            year (int): Year
            month (int): Month
            currency (str): Currency code (default: "USD")

        Returns:
            None
        """
        results = self._repo.get_net_worth_at_year_month(year, month, currency)
        assert len(results) == 1, (
            f"Expected exactly one record for {year}-{month} in {currency}"
        )
        assets, liabilities, net_worth = results[0]
        print(
            f"Year: {year}, Month: {month}, Currency: {currency}, "
            f"Assets: {assets}, Liabilities: {liabilities}, "
            f"Net Worth: {net_worth}"
        )

    def print_net_worth_history(self) -> None:
        """Print net worth history."""
        nw_hist = self._repo.get_net_worth_history()
        print("year, month, assets, liabilities, net_worth")
        for res in nw_hist:
            print(
                f"{res['year']}, {res['month']}, {res['total_assets']}, "
                f"{res['total_liabilities']}, {res['net_worth']}"
            )

    def print_exchange_rate(self, currency: str, year: int, month: int) -> None:
        """Print exchange rates for a specific currency, year, month

        Args:
            currency (str): Currency code
            year (int): Year
            month (int): Month
        """
        all_currency_codes = self._repo.get_all_currency_codes()
        if currency not in all_currency_codes:
            raise ValueError(f"Currency code '{currency}' not found in database.")
        rate = self._repo.get_exchange_rate(year, month, currency)
        if rate:
            print(f"Exchange rate {currency} to USD on {year}-{month}: {rate}")
        else:
            print(f"No exchange rate found for {currency} on {year}-{month}.")

    def print_exchange_rate_history(self, currency: str) -> None:
        """Print exchange rate history.

        Args:
            currency (str): Currency code
        """
        all_currency_codes = self._repo.get_all_currency_codes()
        if currency not in all_currency_codes:
            raise ValueError(f"Currency code '{currency}' not found in database.")
        rates = self._repo.get_exchange_rate_history(currency)
        print("currency, year, month, rate")
        for r in rates:
            print(f"{r['currency']}, {r['year']}, {r['month']}, {r['rate']}")

    def print_balances_at_year_month(
        self, year: int, month: int, active_only: bool = True
    ) -> None:
        """Print all account balances at a specific year and month.

        Args:
            year (int): Year
            month (int): Month
            active_only (bool): Whether to include only active accounts
        """
        # valedate month
        if month < 1 or month > 12:
            raise ValueError(f"Invalid month: {month}. Must be between 1 and 12.")
        balances = self._repo.get_balances_at_year_month(year, month, active_only)
        print("account_name, year, month, amount")
        for bal in balances:
            print(
                f"{bal['account_name']}, {bal['year']}, {bal['month']}, {bal['amount']}"
            )

    def close_repo(self) -> None:
        """Close open repos."""
        self._repo.close_db_connection()
