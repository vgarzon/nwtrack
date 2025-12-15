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

    def close_repo(self) -> None:
        """Close open repos."""
        self._repo.close_db_connection()
