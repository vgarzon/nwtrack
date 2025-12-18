-- Simple schema for a simple networth tracking application
-- Prototype SQLite version

-- Disabl3e foreign keys temporarily to make dropping easier
PRAGMA foreign_keys = OFF;

--------------
--  Tables  --
--------------

DROP TABLE IF EXISTS balances;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS currencies;
DROP TABLE IF EXISTS exchange_rates;

CREATE TABLE currencies (
    code TEXT PRIMARY KEY,     -- currency code, e.g., USD, EUR
    description TEXT NOT NULL  -- currency name, e.g., US Dollar, Euro
);

CREATE TABLE categories (
    name TEXT PRIMARY KEY,               -- category name , e.g., checking, savings, credit card
    side TEXT NOT NULL DEFAULT 'asset'  -- accounting side, either 'asset' or 'liability'
        CHECK (side IN ('asset', 'liability'))
);

CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL REFERENCES categories(name),
    currency TEXT NOT NULL DEFAULT 'USD' REFERENCES currencies(code),
    status TEXT NOT NULL DEFAULT 'active'
	CHECK (status IN ('active', 'inactive')),
    UNIQUE(name)
);

CREATE TABLE balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    month TEXT NOT NULL,  -- format 'YYYY-MM'
    amount INTEGER NOT NULL,
    UNIQUE(account_id, month)
);

-- Exchanges rates to convert from other currencies to USD
CREATE TABLE exchange_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    currency TEXT NOT NULL REFERENCES currencies(code),
    month TEXT NOT NULL,  -- format 'YYYY-MM'
    rate REAL NOT NULL,
    UNIQUE(currency, month)
);

-------------
--  Views  --
-------------

DROP VIEW IF EXISTS networth_history;

-- Summary of assets and liabilities by month, and currency
CREATE VIEW networth_history AS
SELECT
    b.month,
    a.currency,
    SUM(CASE WHEN at.side = 'asset' THEN b.amount ELSE 0 END) AS total_assets,
    SUM(CASE WHEN at.side = 'liability' THEN b.amount ELSE 0 END) AS total_liabilities,
    SUM(CASE WHEN at.side = 'asset' THEN b.amount ELSE 0 END) -
    SUM(CASE WHEN at.side = 'liability' THEN b.amount ELSE 0 END) AS net_worth
FROM
    balances b
JOIN
    accounts a ON b.account_id = a.id
JOIN
    categories at ON a.category = at.name
GROUP BY
    b.month, a.currency
ORDER BY
    b.month, a.currency;

-- Vacuum database to reclaim unused space
PRAGMA foreign_keys = ON;
