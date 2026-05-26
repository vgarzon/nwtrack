# Phase 28: TUI Home Screen and Navigation Shell — Validation

## Automated Tests

### Required test coverage

- `HomeScreen` pilot smoke test: app mounts without error and `HomeScreen` is the active screen
- Selecting "Balances" from the home menu pushes `BalanceUpdateScreen` onto the screen stack
- Selecting "Reports", "Accounts", or "Admin" from the home menu pushes `StubScreen` with the
  correct section label
- Escape from `HomeScreen` fires the `app.quit` action
- `StubScreen` renders with the section name visible (in sub_title or label content)
- Escape from `StubScreen` pops the screen stack (screen stack depth returns to 1 after pop)
- Existing `BalanceUpdateScreen` tests continue to pass after the Escape binding change

### Commands

```bash
just test
just lint
just typecheck
# or equivalently:
just check
```

## Manual Validation

### Full navigation walkthrough

1. `uv run nwtrack tui launch`
2. Confirm: `HomeScreen` is shown with Balances, Reports, Accounts, Admin menu items
3. Confirm: app `TITLE = "nwtrack"` visible in header; Footer shows keybindings (q Quit,
   Escape Back or Quit depending on context)
4. Press ↓ to move to "Reports", press Enter
5. Confirm: stub screen appears with "Reports — not yet implemented" (or equivalent)
6. Press Escape
7. Confirm: back at home screen — not quit
8. Press Enter on "Balances"
9. Confirm: `BalanceUpdateScreen` is shown with balance grid for the most recent month
10. Press Escape
11. Confirm: back at home screen — not quit
12. Press Escape (or `q`) from home screen
13. Confirm: app exits cleanly

### Edge cases

- Pressing `q` from any screen exits the app (app-level binding on `NWTrackApp`)
- `BalanceUpdateScreen` month picker and balance edit modals still work after the Escape
  binding change on the parent screen
- No regression: `nwtrack balances update` CLI command still works (`just check` covers this)

## Definition of Done

- [ ] `HomeScreen` is the entry point when `nwtrack tui launch` runs
- [ ] All four menu items are listed; Balances navigates to `BalanceUpdateScreen`
- [ ] Reports, Accounts, Admin push `StubScreen` with the correct section name
- [ ] Escape from any workflow screen returns to home; Escape from home quits
- [ ] `q` quits from any screen
- [ ] `Header` and `Footer` are visible on home screen, balance update screen, and stub screens
- [ ] `just check` passes (ruff + mypy + pytest)
- [ ] Manual walkthrough completed against a real database
