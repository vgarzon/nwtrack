"""
Convert records from CSV files from wide to long format.
"""

from nwtrack.fileio import csv_to_records, records_to_csv


def main():
    balance_wide_csv_to_long()
    exchange_rate_wide_csv_to_long()


def balance_wide_csv_to_long():
    csv_file = "data/sample/balances_wide.csv"
    output_file = "data/sample/balances.csv"
    index_cols = ("date", "year", "month")
    drop_cols = ("date", "year")
    var_name = "account_name"
    value_name = "amount"
    output_fieldnames = ("month", "account_id", "amount")
    accounts_file = "data/sample/accounts.csv"

    records = csv_to_records(csv_file)
    print("Read", len(records), f"balance records from {csv_file}")
    accounts = csv_to_records(accounts_file)
    print("Read", len(accounts), f"records from {accounts_file}")

    account_name_to_id = {acc["name"]: int(acc["id"]) for acc in accounts}
    clean_balances = clean_balance_records(
        records,
        index_cols,
        var_name,
        value_name,
        account_name_to_id,
        drop_cols,
    )
    records_to_csv(clean_balances, output_file, output_fieldnames)
    print("Wrote", len(clean_balances), f"records to {output_file}")


def exchange_rate_wide_csv_to_long():
    csv_file = "data/sample/exchange_rates_wide.csv"
    output_file = "data/sample/exchange_rates.csv"
    index_cols = ("date", "year", "month")
    drop_cols = ("date", "year")
    var_name = "currency"
    value_name = "exchange_rate"
    output_fieldnames = ("currency", "month", "exchange_rate")

    records = csv_to_records(csv_file)
    print("Read", len(records), f"exchange rate records from {csv_file}")

    clean_exchange_rates = clean_exchange_rate_records(
        records, index_cols, var_name, value_name, drop_cols
    )
    records_to_csv(clean_exchange_rates, output_file, output_fieldnames)
    print("Wrote", len(clean_exchange_rates), f"records to {output_file}")


def clean_balance_records(
    records, index_cols, var_name, value_name, name_to_id, drop_cols
):
    """Clean exchange rate records by converting from wide to long format,
    replacing month with year-month, and dropping specified columns.

    Args:
        records (list of dict): List of exchange rate records in wide format.
        index_cols (tuple of str): Columns to keep as index.
        var_name (str): Name of the variable column in long format.
        value_name (str): Name of the value column in long format.
        name_to_id (dict): Mapping from account name to account ID.
        drop_cols (tuple of str): Columns to drop after processing.

    Returns:
        list of dict: Cleaned exchange rate records in long format.
    """
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


def clean_exchange_rate_records(records, index_cols, var_name, value_name, drop_cols):
    """Clean exchange rate records by converting from wide to long format,
    replacing month with year-month, and dropping specified columns.

    Args:
        records (list of dict): List of exchange rate records in wide format.
        index_cols (tuple of str): Columns to keep as index.
        var_name (str): Name of the variable column in long format.
        value_name (str): Name of the value column in long format.
        drop_cols (tuple of str): Columns to drop after processing.

    Returns:
        list of dict: Cleaned exchange rate records in long format.
    """
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


if __name__ == "__main__":
    main()
