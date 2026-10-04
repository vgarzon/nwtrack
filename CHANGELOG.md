# Changelog

Notable shipped features, most recent first. This replaces the "Current Baseline" and completed
phase list formerly kept in `specs/roadmap.md` — see `specs/backlog.md` for what's still open.

- Fixed: TUI balances screen columns no longer collapse to header width after a transfer
- Sample database command: `nwtrack admin create-sample-db PATH` creates a new database with a
  minimal fictional dataset (never overwrites an existing path, never touches the configured
  database) and prints how to activate it via `config.toml` or `NWTRACK_DATABASE__DB_FILE_PATH`
- Startup balance check: on TUI launch, if months are missing between the latest balance month and
  the current month, a single confirmation forward-fills them (each month from its predecessor,
  skipping accounts inactive that month) in one transaction, then offers to open the balance
  update screen
- Config file selection: the `config.toml` search order is reversed (`./config/nwtrack/`, then
  `~/.config/nwtrack/`, then the standard per-OS location last), and `--config-file` /
  `NWTRACK_CONFIG_FILE` select an explicit file (flag wins). **Behavior change:** a config in
  `./config/nwtrack/` or `~/.config/nwtrack/` now takes priority over the standard location
- Alembic-backed schema migrations: `SchemaManager` now applies versioned Alembic migrations
  instead of the hand-rolled `Base.metadata.create_all()` + legacy-column shim, auto-adopting
  untracked existing databases and taking an automatic pre-migration backup before any real
  schema change
- Balance change threshold warning: `nwtrack balances update` (CLI) and the TUI balance edit flow
  confirm before saving when a new balance's percent change from the prior balance exceeds a
  configurable threshold (`[balances] change_warning_threshold_pct`, default 20%), to catch typo
  entry errors
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
