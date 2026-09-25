# Phase 28: TUI Home Screen and Navigation Shell — Plan

## Task Groups

### 1. New screens ✓

1.1 Create `entrypoints/tui/screens/stub.py`
   - `StubScreen(Screen)` — accepts `section: str` in constructor
   - `compose()` yields `Header()`, a centred `Label(f"{section} — not yet implemented")`,
     and `Footer()`
   - `BINDINGS = [Binding("escape", "app.pop_screen", "Back")]`
   - `sub_title` set to section name in `on_mount`

1.2 Create `entrypoints/tui/screens/home.py`
   - `HomeScreen(Screen)` — accepts `fetcher: FetchService` and `uow: Callable[[], UnitOfWork]`
     in constructor so it can pass them when pushing `BalanceUpdateScreen`
   - `BINDINGS = [Binding("escape,q", "app.quit", "Quit")]`
   - `compose()` yields `Header()`, `ListView` with four `ListItem` entries
     (Balances, Reports, Accounts, Admin), and `Footer()`
   - `on_list_view_selected` dispatches on item label:
     - `"Balances"` → `self.app.push_screen(BalanceUpdateScreen(self._fetcher, self._uow))`
     - `"Reports"` / `"Accounts"` / `"Admin"` → `self.app.push_screen(StubScreen(label))`

### 2. Update existing files ✓

2.1 Update `entrypoints/tui/screens/balance_update.py`
   - Change `BINDINGS` entry for Escape from `Binding("escape,q", "app.quit", "Quit")` to
     `Binding("escape", "app.pop_screen", "Back")`
   - Remove `q` from this screen's bindings (handled at app level)

2.2 Update `entrypoints/tui/app.py`
   - Import `HomeScreen` instead of `BalanceUpdateScreen`
   - Change `on_mount` to `self.push_screen(HomeScreen(self._fetcher, self._uow))`

### 3. Tests ✓

3.1 Add `tests/entrypoints/tui/test_home_screen.py`
   - Test that `HomeScreen` composes without error (pilot smoke test)
   - Test that selecting "Balances" pushes `BalanceUpdateScreen`
   - Test that selecting "Reports" pushes a screen with "not yet implemented" content
   - Test that Escape from `HomeScreen` triggers app quit action

3.2 Add or update `tests/entrypoints/tui/test_stub_screen.py`
   - Test that `StubScreen` renders with the section name in sub_title or label
   - Test that Escape from `StubScreen` pops back (screen stack depth decreases)

3.3 Verify existing `BalanceUpdateScreen` tests still pass after the binding change

### 4. Quality gates ✓

4.1 `just lint` passes (ruff)
4.2 `just typecheck` passes (mypy)
4.3 `just test` passes (pytest)
