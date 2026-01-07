"""
Convert records from CSV files from wide to long format.

Sample settings TOML file:

[paths]
input_dir = "data/sample/"
output_dir = "data/sample/"

[balances]
input_file = "balances_wide.csv"
output_file = "balances.csv"
accounts_file = "accounts.csv"
index_cols = [ "date", "year", "month" ]
drop_cols = [ "date", "year" ]
var_name = "account_name"
value_name = "amount"
output_fieldnames = [ "month", "account_id", "amount" ]

[exchange_rates]
input_file = "exchange_rates_wide.csv"
output_file = "exchange_rates.csv"
index_cols = [ "date", "year", "month" ]
drop_cols = [ "date", "year" ]
var_name = "currency"
value_name = "rate"
output_fieldnames = [ "currency", "month", "rate" ]
"""

import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

from nwtrack.infra.fileio.csv_io import csv_to_records, records_to_csv


@dataclass
class PathsSettings:
    input_dir: str = "data/sample/"
    output_dir: str = "data/sample_output/"


@dataclass
class BalancesSettings:
    input_file: str = "balances_wide.csv"
    output_file: str = "balances.csv"
    accounts_file: str = "accounts.csv"
    index_cols: tuple[str, ...] = ("date", "year", "month")
    drop_cols: tuple[str, ...] = ("date", "year")
    var_name: str = "account_name"
    value_name: str = "amount"
    output_fieldnames: tuple[str, ...] = ("month", "account_id", "amount")


@dataclass
class ExchangeRatesSettings:
    input_file: str = "exchange_rates_wide.csv"
    output_file: str = "exchange_rates.csv"
    index_cols: tuple[str, ...] = ("date", "year", "month")
    drop_cols: tuple[str, ...] = ("date", "year")
    var_name: str = "currency"
    value_name: str = "rate"
    output_fieldnames: tuple[str, ...] = ("currency", "month", "rate")


@dataclass
class Settings:
    paths: PathsSettings
    balances: BalancesSettings
    exchange_rates: ExchangeRatesSettings

    @classmethod
    def from_dict(cls, raw: dict) -> "Settings":
        return cls(
            paths=PathsSettings(**raw.get("paths", {})),
            balances=BalancesSettings(**raw.get("balances", {})),
            exchange_rates=ExchangeRatesSettings(**raw.get("exchange_rates", {})),
        )

    def __post_init__(self) -> None:
        # light validation
        input_path = Path(self.paths.input_dir)
        output_path = Path(self.paths.output_dir)
        balances_path = input_path / self.balances.input_file
        exchange_rates_path = input_path / self.exchange_rates.input_file
        if not input_path.is_dir():
            raise ValueError("Input directory does not exist.")
        if not output_path.is_dir():
            raise ValueError("Output directory does not exist.")
        if not balances_path.exists():
            raise ValueError("Balances file not found in input directory.")
        if not exchange_rates_path.exists():
            raise ValueError("Exchange rates file not found in input directory.")
        if not self.balances.input_file.endswith(".csv"):
            raise ValueError("Balances input file must be a CSV file.")
        if not self.exchange_rates.input_file.endswith(".csv"):
            raise ValueError("Exchange rates input file must be a CSV file.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_wide_csv_to_long.py <settings_file>")
        sys.exit(1)
    settings_file = sys.argv[1]
    print("Loading settings from", settings_file)
    settings = load_settings_toml(settings_file)
    balances_wide_csv_to_long(settings)
    exchange_rates_wide_csv_to_long(settings)


def balances_wide_csv_to_long(settings: Settings):
    input_dir = settings.paths.input_dir
    output_dir = settings.paths.output_dir
    input_file = settings.balances.input_file
    output_file = settings.balances.output_file
    accounts_file = settings.balances.accounts_file
    output_fieldnames = settings.balances.output_fieldnames

    input_file_path = Path(input_dir) / input_file
    output_file_path = Path(output_dir) / output_file
    accounts_file_path = Path(input_dir) / accounts_file

    assert input_file_path.exists(), f"Input file {input_file_path} not found"
    assert accounts_file_path.exists(), f"Accounts file {accounts_file_path} not found"

    records = csv_to_records(input_file_path)
    accounts = csv_to_records(accounts_file_path)
    print("Read", len(records), f"balance records from {input_file_path}")
    print("Read", len(accounts), f"records from {accounts_file_path}")

    account_name_to_id = {acc["name"]: int(acc["id"]) for acc in accounts}
    clean_balances = clean_balance_records(settings, records, account_name_to_id)
    records_to_csv(clean_balances, output_file_path, output_fieldnames)
    print("Wrote", len(clean_balances), f"records to {output_file_path}")


def exchange_rates_wide_csv_to_long(settings: Settings):
    input_dir = settings.paths.input_dir
    output_dir = settings.paths.output_dir
    input_file = settings.exchange_rates.input_file
    output_file = settings.exchange_rates.output_file
    output_fieldnames = settings.exchange_rates.output_fieldnames

    input_file_path = Path(input_dir) / input_file
    output_file_path = Path(output_dir) / output_file

    assert input_file_path.exists(), f"Input file {input_file_path} not found"

    records = csv_to_records(input_file_path)
    print("Read", len(records), f"exchange rate records from {input_file}")

    clean_exchange_rates = clean_exchange_rate_records(settings, records)
    records_to_csv(clean_exchange_rates, output_file_path, output_fieldnames)
    print("Wrote", len(clean_exchange_rates), f"records to {output_file_path}")


def clean_balance_records(settings, records, name_to_id):
    """Clean exchange rate records by converting from wide to long format,
    replacing month with year-month, and dropping specified columns.

    Args:
        settings (Settings): Settings object containing configuration.
        records (list of dict): List of exchange rate records in wide format.
        name_to_id (dict): Mapping from account name to account ID.

    Returns:
        list of dict: Cleaned exchange rate records in long format.

    Settings:
        index_cols (tuple of str): Columns to keep as index.
        var_name (str): Name of the variable column in long format.
        value_name (str): Name of the value column in long format.
        drop_cols (tuple of str): Columns to drop after processing.

    """
    index_cols = settings.balances.index_cols
    drop_cols = settings.balances.drop_cols
    var_name = settings.balances.var_name
    value_name = settings.balances.value_name
    recs = wide_to_long(records, index_cols, var_name, value_name)
    recs = replace_field_func(recs, "month", year_month_to_month)
    name_to_id_func = account_name_to_id_wrapper(name_to_id)
    recs = replace_field_func(
        recs,
        "account_name",
        name_to_id_func,
        "account_id",
    )
    recs = drop_fields(recs, drop_cols)
    recs = sort_records(recs, ["month", "account_id"])
    return recs


def clean_exchange_rate_records(settings, records):
    """Clean exchange rate records by converting from wide to long format,
    replacing month with year-month, and dropping specified columns.

    Args:
        settings (Settings): Settings object containing configuration.
        records (list of dict): List of exchange rate records in wide format.

    Returns:
        list of dict: Cleaned exchange rate records in long format.

    Settings:
        index_cols (tuple of str): Columns to keep as index.
        var_name (str): Name of the variable column in long format.
        value_name (str): Name of the value column in long format.
        drop_cols (tuple of str): Columns to drop after processing.

    """
    index_cols = settings.exchange_rates.index_cols
    drop_cols = settings.exchange_rates.drop_cols
    var_name = settings.exchange_rates.var_name
    value_name = settings.exchange_rates.value_name
    recs = wide_to_long(records, index_cols, var_name, value_name)
    recs = replace_field_func(recs, "month", year_month_to_month)
    recs = drop_fields(recs, drop_cols)
    recs = sort_records(recs, [var_name, "month"])
    return recs


def wide_to_long(records, index_cols, var_name, value_name):
    """Convert records from wide to long format.

    Args:
        records (list of dict): List of records in wide format.
        index_cols (tuple of str): Columns to keep as index.
        var_name (str): Name of the variable column in long format.
        value_name (str): Name of the value column in long format.

    Returns:
        list of dict: List of records in long format.
    """
    long_records = []
    for rec in records:
        index_rec = {col: rec[col] for col in index_cols}
        for key, value in rec.items():
            if key in index_cols:
                continue
            if value == "":
                continue
            long_rec = index_rec.copy()
            long_rec[var_name] = key
            long_rec[value_name] = value
            long_records.append(long_rec)
    return long_records


def replace_field_func(records, field, func, new_name=None):
    """Replace field values in records using a function.

    Args:
        records (list of dict): List of records.
        field (str): Field to replace.
        func (callable): Function to replace field.  Takes record as input.
        new_name (str): If provided, use this as the new field name.

    Returns:
        list of dict: List of records with replaced field values.
    """
    for rec in records:
        if field in rec:
            rec[field] = func(rec)
            if new_name is not None and new_name != field:
                rec[new_name] = rec.pop(field)
    return records


def account_name_to_id_wrapper(name_to_id):
    """Create a function to map account names to account IDs.

    Args:
        name_to_id (dict): Mapping from account name to account ID.

    Returns:
        func: Function that maps account names to account IDs.
    """

    def account_name_to_id(rec):
        return name_to_id.get(rec.get("account_name", ""), -1)

    return account_name_to_id


def year_month_to_month(rec):
    """Replace 'month' field with 'year-month' format.

    Args:
        rec (dict): Record with 'year' and 'month' fields.

    Returns:
        str: 'year-month' formatted string.
    """
    year = rec.get("year", "")
    month = rec.get("month", "")
    return f"{year}-{month:>02}"


def drop_fields(records, fields):
    """Drop specified fields from records.

    Args:
        records (list of dict): List of records.
        fields (list of str): Fields to drop.

    Returns:
        list of dict: List of records with specified fields dropped.
    """
    for rec in records:
        for field in fields:
            rec.pop(field, None)
    return records


def sort_records(records, sort_fields):
    """Sort records by specified fields.

    Args:
        records (list of dict): List of records to sort.
        sort_fields (list of str): Fields to sort by.

    Returns:
        list of dict: Sorted list of records.
    """
    return sorted(records, key=lambda rec: tuple(rec[field] for field in sort_fields))


def load_settings_toml(file_path: str) -> Settings:
    """Load settings from a TOML file."""

    with open(file_path, "rb") as f:
        raw = tomllib.load(f)
    settings = Settings.from_dict(raw)
    return settings


if __name__ == "__main__":
    main()
