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
