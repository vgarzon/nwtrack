"""
Data loading services
"""

from typing import Callable

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.infra.fileio.csv_io import csv_to_records


class InitDataService:
    """Initialize reference and sample data in the database."""

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
        print("InitDataService: Inserting data from CSV files.")
        repo_names = [  # TODO: Use RepoRegistry (pending)
            "currencies",
            "categories",
            "accounts",
            "balances",
            "exchange_rates",
        ]
        assert all(name in repo_names for name in file_paths), (
            f"Missing required file paths. Expected keys: {', '.join(repo_names)}"
        )
        records = {name: csv_to_records(path) for name, path in file_paths.items()}

        # NOTE: storing liabilities as positive amounts
        for row in records["balances"]:
            row["amount"] = abs(int(row["amount"]))

        self._insert_records(records)

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
