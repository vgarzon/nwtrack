# Simple net worth tracker

## Objective

Simple Python programs to track assets and liabilities.

## Dependencies

- Python 3.12
- SQLite

## Database Schema

The database consists of two main tables: `accounts` and `balances`. The `accounts` table stores account info, including its type and currency. The `balances` table records the balance of each account on specific dates.

Auxiliary table `account_types` defines different types of accounts and whether they are assets or liabilities. The `currencies` table holds currency codes and names.

See [sql/nwtrack_ddl.sql](sql/nwtrack_ddl.sql) for details.

