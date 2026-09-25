---
name: single-currency-conversion-reporting
status: idea
---

## Problem

Add conversion-backed reporting so aggregated views can be rendered in one explicit reporting
currency instead of failing on mixed-currency totals.

## Expected outcomes

- Reporting can convert mixed-currency balances into one explicit reporting currency before
  aggregation
- USD is supported as the initial consolidated reporting currency
- Conversion rules and required exchange-rate inputs are defined clearly for reporting workflows
- Compatibility and aggregated report commands can converge on accounting-correct single-currency
  output where conversion data exists

## Notes

Formerly "Phase 35 (On Hold)" in the old roadmap. Depends on manually-entered exchange rates
already in the data model (see `specs/tech-stack.md` — Exchange Rates).
