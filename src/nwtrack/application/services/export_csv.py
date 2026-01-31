"""
Service to export records to CSV files.
"""

import logging
from collections.abc import Callable
from pathlib import Path

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.infra.fileio.csv_io import records_to_csv

logger = logging.getLogger(__name__)


class ExportCSV:
    """Service to export records to CSV files."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow
        # TODO: Use RepoRegistry to define table names
        self._table_names = [
            "currencies",
            "categories",
            "accounts",
            "balances",
            "exchange_rates",
        ]

    def export_tables_to_dir(self, target_dir: Path) -> list[tuple[str, str, int]]:
        """Export pre-specified database tables to CSV files in target directory.

        Args:
            target_dir (Path): Target directory for CSV export.

        Returns:
            list[tuple[str, str, int]]: Summary of exported records per table.
            - table_name (str): Name of the table.
            - csv_path (str): Path to the exported CSV file.
            - n_records (int): Number of records exported.
        """
        export_summary = []
        for table_name in self._table_names:
            csv_path = target_dir / f"{table_name}.csv"
            n_records = self.export_table(table_name, csv_path)
            export_summary.append((table_name, str(csv_path), n_records))
        logger.info(
            "Exported %d tables to CSV files in directory %s",
            len(self._table_names),
            target_dir,
        )
        return export_summary

    def export_table(self, table_name: str, csv_path: Path) -> int:
        """Export database table to CSV file.

        Args:
            table_name (str): Name of the table to export.
            csv_path (Path): Target CSV file path.

        Returns:
            int: Number of records exported.
        """
        # TODO: Use RepoRegistry to validate table_name
        with self._uow() as uow:
            try:
                repo = getattr(uow, table_name)
            except AttributeError:
                logger.error("Repository for table %s not found. Skipping.", table_name)
                raise ValueError(f"Repository for table {table_name} not found.")
            entities = repo.get_all()
            records = [repo._mapper.to_record(entity) for entity in entities]

        if not records:
            logger.info("No records found in table %s. Skipping export.", table_name)
            return 0

        records_to_csv(records, csv_path)
        n_records = len(records)
        logger.info(
            "Exported %d records from table %s to %s", n_records, table_name, csv_path
        )
        return n_records
