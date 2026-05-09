# nwtrack — Stakeholder input

This document collects input from stakeholders and is intended to inform the product specification and design. It is not a formal specification itself, but rather a synthesis of stakeholder needs, goals, and constraints.

Project constitution files in the `specs/` directory are the source of truth for the official product specification. If there are discrepancies between this document and the constitution specs, the constitution specs take precedence.

## Overview

**nwtrack** is a personal net worth tracking CLI application. It allows a single user to record asset and liability balances across multiple accounts and currencies over time, and to generate net worth reports and historical trends.

Data is stored locally in a SQLite database. All interaction happens through a terminal-based CLI with rich formatting and interactive prompts.

This document is a legacy product specification. If terminology here conflicts with the constitution docs in `specs/`, the constitution docs are the source of truth.

## Terminology Mapping

- "Balances by Category (Monthly Snapshot)" maps to single-month aggregation by category.
- "Net Worth History" maps to history aggregation by side as a compatibility reporting surface.
- Future aggregation commands should be described by aggregation dimension and time window, not as separate bespoke report types.
- "Compatibility reporting" means preserving existing user-facing report commands while converging them on the shared aggregation model.

---

## Goals

- Track balances for any number of financial accounts month by month
- Compute and display net worth (assets minus liabilities) at any point in time
- Show net worth trends over configurable time windows
- Support multiple currencies with exchange rate records
- Enable import/export via CSV for portability and backup

---

## Non-Goals

- No multi-user support
- No network connectivity or cloud sync
- No real-time market data or automatic exchange rate fetching
- No sub-monthly granularity (months are the atomic time unit)
- No budgeting, forecasting, or transaction-level tracking

---

## Data Model

### Currencies

| Field       | Type   | Constraints          |
|-------------|--------|----------------------|
| code        | string | Primary key (e.g. "USD") |
| description | string | Human-readable label |

Currencies are reference data. They are not created interactively; they are loaded from CSV during database initialization.

### Categories

| Field | Type   | Constraints                    |
|-------|--------|--------------------------------|
| name  | string | Primary key, unique            |
| side  | enum   | `"asset"` or `"liability"` only |

Categories classify accounts for accounting purposes. The `side` field determines whether an account's balance contributes positively (asset) or negatively (liability) to net worth.

### Institutions

| Field | Type   | Constraints                    |
|-------|--------|--------------------------------|
| id    | int    | Primary key, unique            |
| name  | string | Short label, unique            |
| description | string | Optional free-text description |

Institutions are first-class reference data representing the financial institution where an account is held.

### Tags

| Field | Type   | Constraints                    |
|-------|--------|--------------------------------|
| id    | int    | Primary key, unique            |
| name  | string | Short label, unique            |
| description | string | Optional free-text description |

Tags are first-class reusable reference data used for grouping and reporting across accounts.

### Accounts

| Field          | Type   | Constraints                            |
|----------------|--------|----------------------------------------|
| id             | int    | Primary key, auto-generated            |
| name           | string | Unique across all accounts             |
| description    | string | Free-text label                        |
| category_name  | string | FK → categories.name                   |
| institution_id | int    | Optional FK → institutions.id          |
| currency_code  | string | FK → currencies.code, default "USD"    |
| status         | enum   | `"active"` or `"inactive"`, default "active" |

Accounts may initially reference zero or one institution. Existing accounts remain valid without an institution during the initial rollout, and institution assignment is expected to be added manually rather than through disruptive bulk reassignment.
Accounts may also reference zero, one, or many tags through explicit associations. Existing accounts remain valid with zero tags during the initial rollout, and tag assignment is expected to be added manually rather than through disruptive bulk reassignment.

### Account Tags

| Field      | Type | Constraints                 |
|------------|------|-----------------------------|
| account_id | int  | FK → accounts.id            |
| tag_id     | int  | FK → tags.id                |

Composite unique constraint: `(account_id, tag_id)`.

### Balances

| Field      | Type  | Constraints                                |
|------------|-------|--------------------------------------------|
| id         | int   | Primary key, auto-generated                |
| account_id | int   | FK → accounts.id                           |
| month      | Month | Stored as "YYYY-MM" string                 |
| amount     | int   | Balance in smallest currency unit (e.g. cents) |

Composite unique constraint: `(account_id, month)`. A given account has at most one balance record per month.

### Exchange Rates

| Field         | Type  | Constraints                       |
|---------------|-------|-----------------------------------|
| id            | int   | Primary key, auto-generated       |
| currency_code | string | FK → currencies.code             |
| month         | Month | Stored as "YYYY-MM" string        |
| rate          | float | Rate relative to base currency    |

Composite unique constraint: `(currency_code, month)`.

### Month (Value Object)

Months are represented throughout the system as `Month(year, month)` value objects, not raw dates. They serialize to and from "YYYY-MM" strings.

**Validation rules:**
- `month` must be in range 1–12
- `year` must be >= 0

Months support equality, hashing, sorting, and increments (next month).

---

## Business Rules

### Amounts as Integers

All balance amounts are stored as integers in the smallest unit of the currency (e.g. cents for USD). No floating-point arithmetic is used for balance values. Display formatting handles decimal conversion.

### Asset vs. Liability Accounting

Net worth is computed as:

```
net_worth = sum(balances for ASSET accounts) − sum(balances for LIABILITY accounts)
```

Liability balances are stored as positive integers; the account's category side determines whether they subtract from or add to net worth.

### Balance Transfer Side Logic

When transferring amount `A` from account F (side F_side) to account T (side T_side):

| F side      | T side      | F delta | T delta | Rationale                              |
|-------------|-------------|---------|---------|----------------------------------------|
| asset       | asset       | −A      | +A      | Money moves between assets             |
| asset       | liability   | −A      | −A      | Asset used to pay down debt            |
| liability   | asset       | +A      | +A      | Taking on debt to fund asset purchase  |
| liability   | liability   | +A      | −A      | Debt transferred from one to another   |

A missing balance for the target month is treated as 0 (created if needed).

### Account Status

- **active**: Included in balance update workflows and default list views.
- **inactive**: Hidden from default list views; excluded from interactive month-to-month balance update loops. Still visible when `--active-only` is disabled.

### Duplicate Prevention

- Account names are unique. Creating an account with a duplicate name is rejected.
- Category names are unique (case-insensitive comparison). Creating a duplicate category is rejected.
- `(account_id, month)` is unique in balances. Roll-forward operations use insert-or-ignore to avoid duplicates.

---

## Features

### Account Management

#### List Accounts

Display all accounts with their category, currency, status, and latest balance.

**Options:**
- `--active-only` (default: true): Filter to active accounts only.

#### Create Account

Interactive workflow to register a new account.

**Inputs collected:**
1. Account name (validated unique)
2. Description
3. Category (selected from existing categories)
4. Currency (selected from available currencies)
5. Status (active / inactive)
6. Initial balance month (YYYY-MM)
7. Initial balance amount

**Post-conditions:** An `Account` record and one `Balance` record for the initial month are created atomically. If either fails, both are rolled back.

#### Update Account

Interactive workflow to modify an existing account's metadata.

**Modifiable fields:** name, description, category, currency, status.

**Invariants:** Account balances are not affected by account updates.

---

### Category Management

#### List Categories

Display all categories with their side (asset / liability).

#### Create Category

Interactive workflow to create a new category.

**Inputs collected:**
1. Category name (validated unique, case-insensitive)
2. Side (asset or liability)

---

### Balance Management

#### Update Balances

Interactive workflow to enter or revise account balances for a selected month.

**Workflow:**
1. User selects a month (from recent months or custom input).
2. The system displays all active accounts with their current balance for that month.
3. User selects an account to update.
4. User enters the new amount.
5. Steps 3–4 repeat until the user exits.
6. Net worth summary is displayed at the end.

**Invariants:** Updates are applied per-account. Existing balance records are overwritten; missing ones are created.

#### Roll Balances Forward

Copy all balance records from a selected month to the next consecutive month.

**Workflow:**
1. User selects a source month (must have existing balance records).
2. The system determines the target month (source + 1 month).
3. User confirms before execution.
4. All balance records from the source month are duplicated into the target month. Records that already exist in the target month are skipped (insert-or-ignore).

**Post-condition:** The target month contains at least the same set of balances as the source month.

#### Delete Balance

Remove a single balance record for a specific account and month.

**Workflow:**
1. User selects a month.
2. User selects an account.
3. User confirms deletion.
4. The balance record is permanently deleted.

**Invariants:** Only the selected (account, month) pair is deleted. No other records are affected.

#### Balance Transfer

Move an amount between two accounts for a selected month, applying the correct accounting side logic.

**Workflow:**
1. User selects a month.
2. User selects source account (from).
3. User selects destination account (to).
4. User enters the transfer amount.
5. System shows the projected balance changes for both accounts.
6. User confirms before execution.
7. Both balances are updated atomically.

**Constraints:** Source and destination accounts must be different. The transfer amount must be a positive integer.

---

### Reports

#### Balances by Category (Monthly Snapshot)

Display a full net worth snapshot for a selected month.

**Output sections:**
1. Accounts table: name, category, currency, amount for each active account.
2. Category summary table: total balance per category.
3. Net worth total: assets minus liabilities.

**Options:** User selects the month interactively from available months.

#### Net Worth History

Display net worth values across multiple consecutive months.

**Output:** Chronological table of months with assets, liabilities, and net worth columns. Total change over the period is shown at the bottom.

**Options:**
- `--n-months N` (default: 12): Show the last N months.
- `--n-years N`: Show the last N × 12 months (alternative to `--n-months`).

---

### Data Import / Export

#### Initialize Database from CSV

Populate an empty database from a set of CSV files. Used for initial setup or migration.

**Required files:** `currencies.csv`, `categories.csv`, `accounts.csv`, `balances.csv`, `exchange_rates.csv`.

**Expected columns:**

| File               | Columns                                             |
|--------------------|-----------------------------------------------------|
| currencies.csv     | code, description                                   |
| categories.csv     | name, side                                          |
| accounts.csv       | id, name, description, category, currency, status   |
| balances.csv       | id, account_id, month, amount                       |
| exchange_rates.csv | id, currency, month, rate                           |

**Invariants:** The operation fails atomically if any file is malformed or any constraint is violated.

#### Export Tables to CSV

Export all database tables to CSV files in a target directory.

**Options:**
- `--interactive`: Prompt for output directory.
- `--target-dir PATH`: Specify output directory non-interactively.
- `--create`: Create the target directory if it does not exist.

**Output files:** One CSV per table, named after the table (`currencies.csv`, etc.).

---

## Configuration

### Environment Variables

| Variable                | Default                   | Description                             |
|-------------------------|---------------------------|-----------------------------------------|
| `NWTRACK_DB_FILE_PATH`  | `data/sqlite/nwtrack.db`  | Path to the SQLite database file        |
| `NWTRACK_LOG_FILE`      | `./logs/nwtrack.log`      | Path to the log file                    |
| `NWTRACK_LOG_FILE_LEVEL`| `INFO`                    | Log level: DEBUG, INFO, WARNING, ERROR  |
| `NWTRACK_LOG_ROTATION_MB` | `10`                    | Log file rotation threshold in MB       |
| `NWTRACK_LOG_BACKUP_COUNT` | `7`                    | Number of rotated log files to retain   |

Configuration is loaded from a `.env` file at startup (see `.env_example`).

---

## CLI Command Reference

```
nwtrack
├── accounts
│   ├── list          [--active-only / --no-active-only]
│   ├── create        (interactive)
│   └── update        (interactive)
├── balances
│   ├── update        (interactive)
│   ├── roll          (interactive)
│   ├── delete        (interactive)
│   └── transfer      (interactive)
├── categories
│   ├── list
│   └── create        (interactive)
├── reports
│   ├── balances-category     (interactive month selection)
│   └── networth-history      [--n-months INT] [--n-years INT]
└── export
    └── tables-csv    [--interactive] [--target-dir PATH] [--create]
```

---

## Error Handling

- Duplicate names (accounts, categories) are detected before insertion and reported to the user; no partial writes occur.
- Invalid month strings (not "YYYY-MM", invalid ranges) are rejected at input time.
- Missing balance records for a transfer target are treated as 0 and created as needed.
- All multi-step writes (account + balance, dual-account transfer) execute within a single database transaction; failures roll back completely.
- The database file path must be writable; startup fails with a clear error if it is not.

---

## Out of Scope (Future Considerations)

The following are explicitly out of scope for the current version but noted for awareness:

- Automatic currency conversion in net worth reports (exchange rates are stored but multi-currency aggregation is not currently implemented in reports)
- Inactive account balances in reports (currently only active accounts appear in balance views)
- Archiving or soft-deleting balance history
- Command-line flags for non-interactive balance updates (all balance operations are interactive)
