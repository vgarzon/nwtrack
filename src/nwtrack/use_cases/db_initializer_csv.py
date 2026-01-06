"""
Database initializer services
"""

from pathlib import Path

from nwtrack.admin import DBAdminService
from nwtrack.infra.config.settings import Settings
from nwtrack.services import InitDataService


class DBInitializerCSV:
    """Initialize the database from CSV files."""

    def __init__(
        self,
        config: Settings,
        admin_svc: DBAdminService,
        data_svc: InitDataService,
    ) -> None:
        self._config = config
        self._admin_svc = admin_svc
        self._data_svc = data_svc
        # TODO: Use RepoRegistry to specify required keys
        self._required_keys = [
            "currencies",
            "categories",
            "accounts",
            "balances",
            "exchange_rates",
        ]
        self._file_paths: dict[str, str] = {}

    def run(self) -> None:
        """Run the database initialization process."""
        print(f"Database file path: {self._config.db_file_path}")
        print(f"DDL script path: {self._config.db_ddl_path}")
        n_file_paths = self.collect_file_paths()
        if n_file_paths == 0:
            print("Quitting.")
            return
        print("Specified CSV file paths:")
        for key, path in self._file_paths.items():
            print(f"  {key}: {path}")
        print("WARNING: This script will DELETE and RE-CREATE the database.")
        confirmation = input("Type 'YES' to continue: ")
        if confirmation != "YES":
            print("Quitting.")
            return

        print("Initializing SQLite database.")
        self._admin_svc.init_database()
        self._data_svc.insert_data_from_csv(self._file_paths)
        print("Database initialization complete.")

    def collect_file_paths(self) -> int:
        """Collect and validate file pahhs from user input.

        Returns:
            int: number of elements in file paths dict, or 0 if user quits
        """
        file_paths = {}
        print("Please enter the file paths for the following CSV files or 'q' to quit:")
        for file_key in self._required_keys:
            while True:
                path_str = input(f"{file_key}: ").strip()
                if path_str.lower() == "q":
                    return 0
                path = Path(path_str)
                if not path.is_file():
                    print(f"Error: File not found at {path_str}. Please try again.")
                    continue
                else:
                    file_paths[file_key] = path_str
                    break
        self._file_paths = file_paths.copy()
        return len(self._file_paths)


def main() -> None:
    from nwtrack.admin import SQLiteAdminService
    from nwtrack.bootstrap.composition import build_base_sqlite_uow_container
    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.ports.uow import UnitOfWork

    container = build_base_sqlite_uow_container()
    container.register(
        DBAdminService,
        lambda c: SQLiteAdminService(
            c.resolve(Settings), c.resolve(DBConnectionManager)
        ),
    ).register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        DBInitializerCSV,
        lambda c: DBInitializerCSV(
            c.resolve(Settings), c.resolve(DBAdminService), c.resolve(InitDataService)
        ),
    )
    db_initializer: DBInitializerCSV = container.resolve(DBInitializerCSV)
    db_initializer.run()


if __name__ == "__main__":
    main()
