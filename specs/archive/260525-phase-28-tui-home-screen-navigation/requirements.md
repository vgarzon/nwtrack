# Phase 28: TUI Home Screen and Navigation Shell — Requirements

## Scope

### What this phase delivers

- A `HomeScreen` that replaces the direct launch into `BalanceUpdateScreen`
- `NWTrackApp.on_mount` pushes `HomeScreen`; `BalanceUpdateScreen` is reached by selecting
  Balances from the home menu
- A `StubScreen` for placeholder menu items so Escape-back navigation is exercised end-to-end
  for all four menu entries
- Escape from any workflow screen (including stub screens) pops back to home
- Escape from the home screen quits the app
- App title in the Textual header; keybinding footer visible on all screens

### Menu items

| Item     | Phase 28 behaviour                        |
|----------|-------------------------------------------|
| Balances | Pushes `BalanceUpdateScreen`              |
| Reports  | Pushes `StubScreen("Reports")`            |
| Accounts | Pushes `StubScreen("Accounts")`           |
| Admin    | Pushes `StubScreen("Admin")`              |

### What this phase does NOT deliver

- Functional report, account management, or admin screens — those are Phases 29 and 30
- CSS file or visual styling beyond Textual defaults and `Header`/`Footer` widgets
- Changes to domain, application, or infrastructure layers
- Changes to the CLI entry point or any CLI command
- Automated snapshot tests for Textual widget rendering (deferred per tui-scope.md)

## Decisions

### Widget: `ListView` for the home menu

Textual's built-in `ListView` is used for the home screen menu. It provides keyboard navigation
out of the box, fires `ListView.Selected` on Enter, and requires no custom widget code.

### Escape semantics

- **Home screen**: Escape quits the app (`action_app.quit`). There is no previous screen to
  return to from home.
- **Workflow screens** (`BalanceUpdateScreen`, `StubScreen`): Escape pops back to home
  (`action_app.pop_screen`). The app-level `q` binding (`NWTrackApp.BINDINGS`) handles quit
  from anywhere.

### `BalanceUpdateScreen` binding change

`BalanceUpdateScreen.BINDINGS` currently binds `escape,q` to `app.quit`. In Phase 28 this
must change: Escape should pop back to home, not quit. The `q`-to-quit behaviour is preserved
by the app-level binding on `NWTrackApp`.

### Stub screen

`StubScreen` is a single reusable `Screen` subclass that accepts a section name string and
displays a "not yet implemented" notice. It uses `Header`, `Footer`, and a centred `Label`.
Its Escape binding pops back to home. This proves the full Escape-back navigation path for
every menu item in Phase 28.

### Minimal polish

`Header` and `Footer` are yielded on all screens, matching the `tui-scope.md` wireframe.
The app `TITLE = "nwtrack"` is already set. No custom CSS or `.tcss` file is introduced
in this phase.

## Context

### Patterns to follow

- Screen-owned workflow pattern from `specs/tui-prototype.md`: screens receive `FetchService`
  and `UnitOfWork` via constructor injection from the TUI composition root
- `NWTrackApp` passes services down to `BalanceUpdateScreen` as before; `HomeScreen` also
  receives these services so it can pass them when pushing `BalanceUpdateScreen`
- `StubScreen` does not need services — it has no data dependencies

### Files expected to change

| File | Change |
|------|--------|
| `entrypoints/tui/app.py` | `on_mount` pushes `HomeScreen` instead of `BalanceUpdateScreen` |
| `entrypoints/tui/screens/balance_update.py` | Escape binding changed from `app.quit` to `app.pop_screen` |
| `entrypoints/tui/screens/home.py` | New file — `HomeScreen` |
| `entrypoints/tui/screens/stub.py` | New file — `StubScreen` |

### Stack constraints

- Python 3.12+, Textual ≥ 3.0.0 (already in `pyproject.toml`)
- No new dependencies
- No raw SQL; no domain or persistence changes
