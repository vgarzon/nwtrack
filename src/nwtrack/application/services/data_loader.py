"""
Data loading services
"""

import logging
from csv import DictReader
from collections.abc import Callable
from pathlib import Path

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.infra.fileio.csv_io import csv_to_records

logger = logging.getLogger(__name__)


class InitDataService:
    """Initialize reference and sample data in the database."""

    IMPORT_TABLE_NAMES = (
        "currencies",
        "categories",
        "institutions",
        "tags",
        "accounts",
        "account_tags",
        "balances",
        "exchange_rates",
    )
    IMPORT_HEADERS = {
        "currencies": ("code", "description"),
        "categories": ("name", "side"),
        "institutions": ("id", "name", "description"),
        "tags": ("id", "name", "description"),
        "accounts": (
            "id",
            "name",
            "description",
            "category",
            "institution_id",
            "currency",
            "status",
        ),
        "account_tags": ("account_id", "tag_id"),
        "balances": ("id", "account_id", "month", "amount"),
        "exchange_rates": ("id", "currency", "month", "rate"),
    }
    IMPORT_ENTITY_TABLE_NAMES = (
        "currencies",
        "categories",
        "institutions",
        "tags",
        "accounts",
        "balances",
        "exchange_rates",
    )

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
        logger.info("InitDataService: Inserting data from CSV files.")
        repo_names = [  # TODO: Use RepoRegistry (pending)
            "currencies",
            "categories",
            "accounts",
            "balances",
            "exchange_rates",
        ]
        for name in repo_names:
            if name not in file_paths:
                logger.error("Missing required file path for repo: %s", name)
                raise KeyError(f"Missing required file path for repo: {name}")
            logger.info("Loading data for repo %s from %s", name, file_paths[name])

        records = {name: csv_to_records(path) for name, path in file_paths.items()}

        # NOTE: storing liabilities as positive amounts
        for row in records["balances"]:
            row["amount"] = abs(int(row["amount"]))

        self._insert_records(records)

    def import_bundle_from_dir(self, source_dir: Path) -> None:
        """Import a standard CSV bundle from one source directory."""
        file_paths = self.validate_import_bundle(source_dir)
        records = self._load_records_from_csv(file_paths)

        # NOTE: storing liabilities as positive amounts
        for row in records["balances"]:
            row["amount"] = abs(int(row["amount"]))

        self._import_records(records)

    def validate_import_bundle(self, source_dir: Path) -> dict[str, str]:
        """Validate a standard CSV bundle before mutating database data."""
        if not source_dir.exists():
            raise ValueError(f"Source directory {source_dir} does not exist.")
        if not source_dir.is_dir():
            raise ValueError(f"Source path {source_dir} is not a directory.")

        file_paths: dict[str, str] = {}
        missing_files: list[str] = []
        for name in self.IMPORT_TABLE_NAMES:
            csv_path = source_dir / f"{name}.csv"
            if not csv_path.is_file():
                missing_files.append(csv_path.name)
                continue
            file_paths[name] = str(csv_path)

        if missing_files:
            missing = ", ".join(sorted(missing_files))
            raise ValueError(f"Missing required CSV files: {missing}")

        for table_name, csv_path in file_paths.items():
            self._validate_csv_header(table_name, Path(csv_path))

        return file_paths

    def _validate_csv_header(self, table_name: str, csv_path: Path) -> None:
        """Validate one CSV header against the supported import contract."""
        with open(csv_path, encoding="utf-8") as file_obj:
            reader = DictReader(file_obj)
            actual_fields = tuple(reader.fieldnames or ())

        expected_fields = self.IMPORT_HEADERS[table_name]
        if actual_fields != expected_fields:
            raise ValueError(
                "Malformed CSV header for "
                f"{csv_path.name}: expected {expected_fields}, got {actual_fields}"
            )

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

    def _import_records(self, records: dict[str, list[dict]]) -> None:
        """Import the supported CSV bundle into the database."""
        with self._uow() as uow:
            session = getattr(uow, "_session", None)
            if session is None:
                raise ValueError("Unit of work session is unavailable for CSV import.")

            for name in self.IMPORT_ENTITY_TABLE_NAMES:
                repo = getattr(uow, name)
                entities = repo.hydrate_many(records[name])
                for entity in entities:
                    session.merge(entity)
            session.flush()

            account_tag_map: dict[int, list[int]] = {}
            for row in records["account_tags"]:
                account_id = int(row["account_id"])
                tag_id = int(row["tag_id"])
                account_tag_map.setdefault(account_id, []).append(tag_id)

            for account_id, tag_ids in sorted(account_tag_map.items()):
                uow.tags.replace_for_account(account_id, tag_ids)

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
