"""
Database initializer services
"""

import logging
from pathlib import Path

from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.infra.config.settings import Settings

logger = logging.getLogger(__name__)


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
        logger.info("Starting database initialization from CSV files.")
        logger.info("Database file path: %s", self._config.db_file_path)
        logger.info("DDL script path: %s", self._config.db_ddl_path)
        print(f"Database file path: {self._config.db_file_path}")
        print(f"DDL script path: {self._config.db_ddl_path}")
        try:
            self.collect_file_paths()
        except KeyboardInterrupt:
            logging.warning("User aborted csv file input.")
            print("Stopping.")
            return
        print("Specified CSV file paths:")
        for key, path in self._file_paths.items():
            print(f"  {key}: {path}")
        print("WARNING: This script will DELETE and RE-CREATE the database.")
        confirmation = input("Type 'YES' to continue: ")
        if confirmation.strip().lower() != "yes":
            logger.warning("User aborted database initialization.")
            print("Quitting.")
            return

        print("Initializing SQLite database.")
        self._admin_svc.init_database()
        self._data_svc.insert_data_from_csv(self._file_paths)
        print("Database initialization complete.")
        logger.info("Finished database initialization from CSV files.")

    def collect_file_paths(self) -> None:
        """Collect and validate file pahhs from user input.

        Returns:
            None

        Exceptions:
            KeyboardInterrupt: if user interrupts input
        """
        file_paths = {}
        print("Please enter the file paths for the required CSV files or 'q' to quit:")
        for file_key in self._required_keys:
            while True:
                path_str = input(f"{file_key}: ").strip()
                if path_str.lower() == "q":
                    logger.warning("User aborted csv file input for key %s", file_key)
                    raise KeyboardInterrupt
                path = Path(path_str)
                if not path.is_file():
                    print(f"Error: File not found at {path_str}. Please try again.")
                    continue
                else:
                    file_paths[file_key] = path_str
                    break
        self._file_paths = file_paths.copy()


def main() -> None:
    from dotenv import load_dotenv

    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.bootstrap.composition import (
        build_base_sqlite_uow_container,
    )

    load_dotenv()
    setup_logging()

    container = build_base_sqlite_uow_container()
    container.register(
        DBAdminService,
        lambda c: DBAdminService(c.resolve(Settings), c.resolve(DBConnectionManager)),
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
