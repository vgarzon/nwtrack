# Simple net worth tracker

## Description

- Python program to track assets and liabilities.
- Data is stored in a local SQLite database.
- Command-line interface for data entry and reporting.

## Database Schema

### Tables

- `accounts`: account information, including type and currency.
- `balances`: account balances on specific dates.
- `account_types`: types of accounts (asset or liability).
- `currencies`: currency codes and names.

See [sql/nwtrack_ddl.sql](sql/nwtrack_ddl.sql) for details.

## Dependencies

- Python 3.12
- SQLite (Python standard library module)

