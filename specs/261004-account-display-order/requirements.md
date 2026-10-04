# Account Display Order — Requirements

## Scope

Let the user choose the order in which accounts are listed, and hide accounts from everyday
TUI views without deactivating them.

- Two new columns on `accounts`:

| Column | Type | Default | Meaning |
|---|---|---|---|
| `display_order` | INTEGER NOT NULL | backfilled from `id` rank | 1-based slot; unique, contiguous |
| `is_hidden` | BOOLEAN NOT NULL | `false` | Hidden from TUI account lists unless "show hidden" is on |

- One Alembic revision adds the columns and backfills `display_order` by increasing `id`.
- All account listings use `display_order` instead of account id: TUI balance table, accounts
  list, account pickers in modals (transfer, balance create/edit), and CLI listings.
- TUI screens that list accounts hide `is_hidden` accounts by default and offer a "show hidden"
  toggle key. The toggle is per screen and not persisted.
- Totals that sum the visible rows of a table follow that screen's toggle.
- New admin TUI screen (Admin menu → "Account order"): lists all accounts (hidden ones included,
  marked), with keys to move the selected account up/down one slot and to toggle hidden.
  Neighbours shift automatically so `display_order` stays contiguous.
- New accounts are appended (`max(display_order) + 1`), visible. Deleting an account closes
  the gap.
- `display_order` and `is_hidden` are exported/imported with the `accounts` CSV.

## Non-goals

- No change to net worth, aggregation or history report math: they always include hidden
  accounts. Hiding is a display preference only.
- CLI never hides accounts and gets no `--show-hidden` flag (CLI is slated for retirement).
- No per-screen persisted visibility, no per-month ordering, no category/institution grouping
  order.
- No move-to-slot-N modal; reordering is up/down keys only.

## Decisions

- **Columns on `accounts`, not a side table.** The data is strictly 1:1 with an account; a side
  table needs a row created/deleted with every account, a join in every account query, and a
  new CSV table. Columns avoid all three and ride the existing accounts CSV round trip.
- **Contiguous 1..N order, maintained by the repository.** Move up/down is a swap with the
  neighbour; insert appends; delete renumbers. No gaps keeps swap logic trivial.
- **Hidden is cosmetic.** Accounting Correctness (mission) outweighs convenience: net worth must
  never silently change because of a view toggle.
- **Ordering lives in the repository/query layer** (`ORDER BY display_order`), so every caller
  gets it without per-screen sorting.

## Context

- Layering: repository methods in `infra/persistence/repositories/accounts.py`, use case or
  service method for reorder/toggle, screen under `entrypoints/tui/screens/` resolved from
  `bootstrap/tui_composition.py`, linked from `admin_menu.py`.
- Currently no account query has an `ORDER BY` (`get_all`, `get_active`, `get_month_balances`
  rely on id/insertion order); the balance-month query orders by `Balance.month, Balance.account_id`.
- Migrations: exactly one new revision after `0002`; SQLite batch mode; pass `table_args`
  explicitly (accounts has named constraints). Pre-migration backup is automatic.
- Models: new fields use `Mapped[...]` with `default` values so existing `Account(...)`
  constructions keep working.
- TUI pattern to imitate: `institutions.py` / `tags.py` list screens (DataTable, bindings,
  restore cursor after refresh).

## Assumptions and open questions

1. The balance-update screen currently has **no** row-sum total — only a net-worth label for
   all accounts. Assumed: add a "Visible total" line there that follows the toggle, and leave the
   net-worth label unchanged (all accounts). Correct me if you want no new line.
2. Hidden accounts are still included in the startup forward-fill and roll-forward; they just
   aren't shown. Assumed.
3. Pickers (transfer, balance create/edit modals) hide hidden accounts with no toggle inside
   the modal, except that a pre-selected account (e.g. prefilled From) is always kept. Assumed.
4. Account create/edit form does not expose `display_order`/`is_hidden`; only the new admin
   screen does.
5. Old accounts CSVs without the two columns must still import (order by id, not hidden).
   Assumed.
6. Toggle key: `h`. To be confirmed against existing bindings during implementation.
7. Admin menu label: "Account order". Naming open.
