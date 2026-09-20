# Phase 38: Single Account Balance History Report — Requirements

## Scope

Add a new report, `reports account-history`, that shows one account's balance
trajectory over a `YYYY-MM` month range, available from both the CLI and the TUI.

### In scope

- A per-month table for one selected account across a start/end month range:
  - `month`
  - `balance` (blank/`—` for months with no balance record)
  - `delta` (month-over-month change, computed against the account's last
    *actual* recorded balance, skipping over any gap months rather than
    treating a gap as zero)
- A trend summary block computed over the months that have actual balance
  records in the range:
  - minimum balance
  - maximum balance
  - average balance
  - total change (last recorded balance in range − first recorded balance in
    range)
- Header context: account name, category, currency, institution (if any) —
  for readability, since the report is scoped to a single account.
- CLI command: `nwtrack reports account-history` accepting account selection
  (`--account-id` or `--account-name`) and `--start` / `--end` month options.
- TUI screen reachable from the Reports menu, with an account picker
  (`Select`) and start/end month inputs, following the existing report screen
  pattern (`AggregationScreen`, `NetWorthHistoryScreen`).
- Default `AccountStatusScope.HISTORICAL` filtering is implied by using the
  account's own status-history record; no status-scope selector is exposed
  since the report is already scoped to one account (a report for an account
  that was inactive for part of the range still shows its balance history —
  status scope in this report is about which account can be *selected*, not
  about filtering rows out).

### Out of scope (this phase)

- Multi-account comparison or overlay views (single account only).
- Charting/graphical output (deferred to Phase 40: HTML Graphical Reports,
  which explicitly plans to reuse this report's data for a line chart).
- CSV export of this report (deferred to Phase 34, currently on hold).
- Editing balances from this screen (read-only report).

## Decisions

- **Dedicated per-account query, not the shared aggregation core.** The
  shared aggregation model (Phase 16) groups balances *across* accounts by an
  attribute (category, side, institution, currency, tag). A single-account
  history is not a cross-account grouping — it is a per-account time series.
  Routing it through the aggregation core would force an artificial
  single-value grouping dimension for no benefit, so this phase adds a
  focused use case and repository query instead. This preserves the
  aggregation core's purpose rather than overloading it.
- **Gap handling: carry the last known balance for delta math, but display a
  blank for the gap month itself.** This matches how a user reading a bank
  statement would expect trend math to work — a missing month is a missing
  entry, not implicitly zero. Contrast with `AccountStatusScope.ALL`
  aggregation reporting elsewhere, which *does* treat inactive-account gaps
  as zero for cross-account net worth totals; that convention doesn't apply
  here because this report is about one account's own data, not net worth
  composition.
- **Trend stats are computed only over months with actual balance records.**
  Including blank/gap months in min/max/average would silently pull those
  stats toward zero and misrepresent the account's real trend.
- **CLI command lives under `reports`, not `accounts`.** It's read-only
  reporting output shaped like the other `reports` commands
  (`balances-aggregate-history`, `networth-history`), so it belongs alongside
  them for discoverability, even though the underlying query is scoped to a
  single account.
- **No status-scope selector on this report.** Existing report screens
  (`NetWorthHistoryScreen`, `AggregationScreen`) expose a status-scope
  selector because they aggregate across many accounts and the scope changes
  *which accounts* are included. Here, the account is already chosen
  explicitly by the user, so there is nothing for a scope selector to filter.

## Context

- Follow the existing use-case pattern: constructor-injected `UoW` factory
  (or `FetchService`, if read-only queries fit there) + presenter protocol,
  `run()` returning `OperationResult[T]`, `main()` for CLI wiring. See
  `src/nwtrack/application/use_cases/report_networth_history.py` for the
  closest existing pattern (history report over a month range, presenter
  injected, `AccountStatusScope` handling).
- Follow the existing presenter/adapter split
  (`application/ports/presentation.py` protocol +
  `entrypoints/cli/adapters/report_presenters.py` Rich adapter). No use case
  should import Rich directly, consistent with the completed presenter
  migration (Phase 24).
- CLI command file: `src/nwtrack/entrypoints/cli/commands/reports.py`
  (existing `reports` Typer sub-app).
- TUI screen file: new module under `src/nwtrack/entrypoints/tui/screens/`,
  reachable from `reports_menu.py`, following the screen-owned-workflow
  pattern (Phase 25) and the existing report screens
  (`networth_history.py`, `aggregation.py`) for widget/layout conventions
  (DataTable for the per-month rows, a summary area for trend stats, month
  inputs consistent with existing month-picker conventions).
- Money remains integer smallest-unit amounts per `specs/tech-stack.md`;
  display formatting (decimal conversion) happens in the presenter/screen
  layer, not the use case.
- This phase does not touch the shared aggregation query layer, existing
  `reports networth-history` / `reports balances-aggregate*` commands, or any
  currently-on-hold Phase 34–37 work.
