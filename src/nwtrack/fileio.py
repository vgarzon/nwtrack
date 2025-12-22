"""
File input / output utility functions.
"""

import csv


def csv_to_records(csv_file_path: str) -> list[dict]:
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


def records_to_csv(records, csv_file_path, fieldnames=None):
    """Write records to a CSV file.

    Args:
        records (list of dict): List of records to write.
        csv_file_path (str): Path to the output CSV file.
        fieldnames (list of str): List of field names for the CSV.
            If None, use first dict keys.  Default: None

    Returns:
        None
    """
    if fieldnames is None and records:
        fieldnames = list(records[0].keys())

    with open(csv_file_path, mode="w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
