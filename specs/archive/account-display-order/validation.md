# Account Display Order — Validation

## Automated
- `just check` (ruff, mypy, pytest) passes.
- Migration test: build a pre-`0003` database (accounts with non-contiguous ids, some deleted),
  run `ensure_current_schema()`; assert columns exist, `display_order` is 1..N by id, nothing
  hidden, a `.bak-*` backup was taken, and balances/tags/status history are intact.
- Repository: insert appends at max+1; `move` up/down swaps with neighbour; first-up and
  last-down are no-ops; delete renumbers contiguously; `get_all`/`get_active` ordered.
- Fetch: `include_hidden=False` omits hidden accounts; default includes them; month balances
  follow `display_order`.
- Reports: net worth and aggregations are identical with and without hidden accounts.
- CSV: export includes both columns; import of an old CSV without them succeeds; round trip
  preserves order and hidden flags.
- TUI: balance table order follows `display_order`; hidden rows absent until toggle, present
  after; visible total changes with the toggle while the net-worth label does not; admin screen
  move/toggle persists and cursor follows the moved row; transfer modal lists accounts in order
  and keeps a hidden prefilled From account.

## Manual
- Launch the TUI on a copy of a real database: confirm migration backup, order unchanged at
  first, reorder a few accounts, hide one, confirm it disappears from balances/transfer and
  reappears with the toggle, confirm net worth unchanged.
- Run `nwtrack accounts list` / `balances update` in the CLI: new order, hidden accounts shown.

## Definition of done
- All automated checks pass, manual walkthrough done, `CLAUDE.md` and `CHANGELOG.md` updated,
  PR into `devel` open.

## Results (final validation)

- `just check` equivalents run: ruff clean, mypy clean, full pytest green.
- Automated coverage added: migration backfill (stamped and untracked pre-0003 DB, backup taken),
  repository order/move/edge no-ops/delete renumber/hidden/hydrate slots, FetchService
  filtering and net-worth invariance, CSV export columns and legacy-header import, TUI order
  screen (move up/down with cursor following, hide toggle, admin menu route), balance screen
  toggle and visible-total (per currency, liabilities negative), accounts list toggle, transfer
  modal (hidden omitted; hidden prefilled From kept).
- Manual (CLI, temp sample DB): `admin create-sample-db` yields slots 1..N and stamps `0003`;
  `accounts list` runs. Found and fixed during this walkthrough: CSV import/sample paths use
  `session.merge`, bypassing `insert`, leaving slots at 0 — fixed in `hydrate_many`.
- Not exercised: an interactive TUI session on a real database copy (covered only by Textual
  pilot tests), and the CLI `balances update` command visually.
- Drift from spec: no `ReorderAccounts` use case (screen calls the repository via the UoW like
  the tags/institutions screens); no DB unique constraint on `display_order`.
