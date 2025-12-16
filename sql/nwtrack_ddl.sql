-- Simple schema for a simple networth tracking application
-- Prototype SQLite version

--------------
--  Tables  --
--------------

DROP TABLE IF EXISTS balances;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS account_types;
DROP TABLE IF EXISTS currencies;
DROP TABLE IF EXISTS exchange_rates;

CREATE TABLE currencies (
    code TEXT PRIMARY KEY,  -- currency code, e.g., USD, EUR
    name TEXT NOT NULL      -- currency name, e.g., US Dollar, Euro
);

CREATE TABLE account_types (
    type TEXT PRIMARY KEY,              -- account type , e.g., checking, savings, credit card
    kind TEXT NOT NULL DEFAULT 'asset'  -- account kind, either 'asset' or 'liability'
        CHECK (kind IN ('asset', 'liability'))
);

CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL REFERENCES account_types(type),
    currency TEXT NOT NULL DEFAULT 'USD' REFERENCES currencies(code),
    status TEXT NOT NULL DEFAULT 'active'
	CHECK (status IN ('active', 'inactive')),
    UNIQUE(name)
);

CREATE TABLE balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    UNIQUE(account_id, year, month)
);

-- Exchanges rates to convert from other currencies to USD
CREATE TABLE exchange_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    currency TEXT NOT NULL REFERENCES currencies(code),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    rate REAL NOT NULL,
    UNIQUE(currency, year, month)
);

-------------
--  Views  --
-------------

DROP VIEW IF EXISTS networth_history;

-- Summary of assets and liabilities by year, month, and currency
CREATE VIEW networth_history AS
SELECT
    b.year,
    b.month,
    a.currency,
    SUM(CASE WHEN at.kind = 'asset' THEN b.amount ELSE 0 END) AS total_assets,
    SUM(CASE WHEN at.kind = 'liability' THEN b.amount ELSE 0 END) AS total_liabilities,
    SUM(CASE WHEN at.kind = 'asset' THEN b.amount ELSE 0 END) -
    SUM(CASE WHEN at.kind = 'liability' THEN b.amount ELSE 0 END) AS net_worth
FROM
    balances b
JOIN
    accounts a ON b.account_id = a.id
JOIN
    account_types at ON a.type = at.type
GROUP BY
    b.year, b.month, a.currency
ORDER BY
    b.year, b.month, a.currency;

