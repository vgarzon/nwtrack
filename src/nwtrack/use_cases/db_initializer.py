"""
Database initializer services
"""

from pathlib import Path

from nwtrack.admin import DBAdminService
from nwtrack.config import Config
from nwtrack.services import InitDataService


class DBInitializerCSV:
    """Initialize the database from CSV files."""

    def __init__(
        self,
        config: Config,
        admin_svc: DBAdminService,
        data_svc: InitDataService,
    ) -> None:
        self._config = config
        self._admin_svc = admin_svc
        self._data_svc = data_svc

    def run(self, file_paths: dict[str, str]) -> None:
        print(f"Database file path: {self._config.db_file_path}")
        print(f"DDL script path: {self._config.db_ddl_path}")
        print("Specified CSVfile paths:")
        for key, path in file_paths.items():
            print(f"  {key}: {path}")
        # TODO: Use RepoRegistry to specify required keys
        required_keys = {
            "accounts",
            "balances",
            "categories",
            "currencies",
            "exchange_rates",
        }
        self._validate_file_path_keys(file_paths, required_keys)
        self._validate_file_paths(file_paths)
        print("WARNING: This script will DELETE and RE-CREATE the database.")
        confirmation = input("Type 'YES' to continue: ")
        if confirmation != "YES":
            print("Quitting.")
            return

        print("Initializing SQLite database.")
        self._admin_svc.init_database()
        self._data_svc.insert_data_from_csv(file_paths)
        print("Database initialization complete.")

    def _validate_file_path_keys(
        self, file_paths: dict[str, str], required_keys: set[str]
    ) -> None:
        print("Validating required file path keys.")
        missing_keys = required_keys - file_paths.keys()
        if missing_keys:
            raise KeyError(f"Missing required file paths for keys: {missing_keys}")

    def _validate_file_paths(self, file_paths: dict[str, str]) -> None:
        print("Validating file paths.")
        for key, path in file_paths.items():
            _path = Path(path)
            if not _path.is_file():
                raise FileNotFoundError(f"Path for '{key}' is not a file: {path}")
