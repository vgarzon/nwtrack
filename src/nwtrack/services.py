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

    def insert_sample_data(self, accounts_path: str, balances_path: str) -> None:
        """Insert sample data into the database.

        Args:
            accounts_path (str): Path to the accounts CSV file.
            balances_path (str): Path to the balances CSV file.
        """
        print("Service: Inserting sample data.")
        accounts = csv_file_to_list_dict(accounts_path)
        balances = csv_file_to_list_dict(balances_path)
        self._repo.insert_accounts(accounts)
        self._repo.insert_balances(balances)
