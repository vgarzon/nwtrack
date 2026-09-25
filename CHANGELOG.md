# Changelog

Notable shipped features, most recent first. This replaces the "Current Baseline" and completed
phase list formerly kept in `specs/roadmap.md` — see `specs/backlog.md` for what's still open.

- macOS packaging and deployment via `uv tool install`, with documented install/upgrade/uninstall
  paths and `just tool-install` / `just tool-uninstall` for local smoke-testing
- TOML-based configuration (`config.toml`, resolved via `platformdirs`), replacing `.env`
- Single account balance history report (CLI and TUI), with month-over-month deltas and trend
  summary stats
- TUI visual design system: shared theme module, dark/light mode toggle, consistent modal/error
  styling, filter-bar toolbar, colored deltas
- Account status history (`account_status_history` table) so historical reports apply each
  account's status as of the reporting month, plus a TUI status-scope selector
- Full TUI screen coverage: balance operations (roll-forward, delete, transfer), account and
  admin screens (categories, institutions, tags), report screens, home navigation shell
- Institutions and tags as first-class reference data, with CLI CRUD and account associations
- Shared balance-aggregation query core (single-month and history), with net worth and category
  reporting converged onto it
- CSV export/import round-trip covering the full current schema (including institutions and
  tags), with a first-class `import tables-csv` command
- Presenter-protocol migration completed for all interactive use cases, decoupling business logic
  from Rich console I/O ahead of the TUI

For full historical detail, see `specs/roadmap.md` in git history prior to the switch to
`specs/backlog.md`.
