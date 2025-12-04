"""
File input / output utility functions.
"""

import csv


def csv_file_to_list_dict(csv_file_path: str) -> list[dict]:
    """
    Read a CSV file and return its contents as a list of dictionaries.
    Each dictionary represents a row in the CSV file, with column headers as keys.

    Args:
        csv_file_path (str): Path to the CSV file.

    Returns:
        list[dict]: List of dictionaries representing the CSV rows.
    """
    with open(csv_file_path, "r") as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]

    return data
