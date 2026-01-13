"""
File input / output utility functions.
"""

from pathlib import Path
import csv


def csv_to_records(csv_file_path: str | Path) -> list[dict]:
    """Read records from a CSV file

    Args:
        csv_file_path (str): Path to the CSV file.

    Returns:
        list[dict]: List of records as dictionaries.
    """
    with open(csv_file_path, "r") as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]

    return data


def records_to_csv(
    records: list[dict],
    csv_file_path: str | Path,
    fieldnames: tuple[str, ...] | None = None,
) -> None:
    """Write records to a CSV file.

    Args:
        records (list[dict]): List of records to write.
        csv_file_path (str): Path to the output CSV file.
        fieldnames (tuple[str, ...] | None): Optional list of field names for the CSV.
            If None, use first dict keys.  Default: None

    Returns:
        None
    """
    if not records:
        raise ValueError("Emplty records list provided.")
    if fieldnames is None:
        try:
            keys = records[0].keys()
        except AttributeError as e:
            raise ValueError("Records must be a list of dictionaries.") from e
        fieldnames = tuple(keys)

    with open(csv_file_path, mode="w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
