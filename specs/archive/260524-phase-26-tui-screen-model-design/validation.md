# Phase 26 — TUI Screen Model Design: Validation

## Definition of Done

Phase 26 is complete when:

1. All three open questions from `specs/tui-prototype.md` are answered in `requirements.md`
   with explicit decisions and rationale — not deferred.
2. The screen inventory table covers all screens required for Phases 27–29.
3. The navigation transition diagram shows all push/pop paths for the near-term screen set.
4. Detailed ASCII wireframes exist for `HomeScreen`, `BalanceUpdateScreen`,
   `MonthPickerModal`, and `BalanceEditModal`.
5. Sketch-level wireframes exist for `ReportsMenuScreen`, `NetworthHistoryScreen`, and
   `SingleMonthAggScreen`.
6. Keyboard conventions are documented and confirm that no custom bindings beyond `m`
   (month picker) are introduced in Phases 27–28.
7. The design document is reviewed before Phase 27 implementation begins.

---

## Automated Quality Gates

No production code is written in this phase. The quality gates confirm that the existing
codebase is unmodified:

```bash
just check   # ruff + mypy + pytest must all pass unchanged
```

Run this after the spec files are committed to confirm no accidental code changes.

---

## Manual Review Checklist

Before marking Phase 26 complete, verify each item:

### Decisions
- [ ] Month selection UX decision is documented with rationale in `requirements.md`
- [ ] Edit input UX decision is documented with rationale in `requirements.md`
- [ ] Navigation model is confirmed and the transition diagram matches `tui-scope.md`'s
      screen-stack design decision

### Screen inventory
- [ ] All seven near-term screens are in the inventory table
- [ ] Every row has phase, workflow, pushed-from, and pops-to columns filled in
- [ ] The transition diagram is consistent with the inventory table

### Wireframes
- [ ] `HomeScreen` wireframe shows: menu items limited to Balances and Reports (only
      workflows available in Phases 27–28), `q` binding hint
- [ ] `BalanceUpdateScreen` wireframe shows: account grid, net worth footer, month in header,
      `[m month]` binding hint
- [ ] `MonthPickerModal` wireframe shows: month grid, pre-selected current month,
      Cancel/Select, Escape cancels
- [ ] `BalanceEditModal` wireframe shows: account name, current amount, input field,
      error line (hidden by default), Cancel/Save, Escape cancels
- [ ] Report screen sketches are present even if lower fidelity

### Keyboard conventions
- [ ] Table lists all Textual default bindings used
- [ ] `m` is documented as the only application-specific binding added through Phase 28
- [ ] No undocumented custom bindings appear in any wireframe

### Blocking items for Phase 27
- [ ] `MonthPickerModal` resolves as `ModalScreen[Month | None]` — return type is explicit
- [ ] `BalanceEditModal` resolves as `ModalScreen[int | None]` — return type is explicit
- [ ] Error display behaviour on invalid input is specified (show error in modal, do not dismiss)
- [ ] The `reactive[int]` net_worth cleanup is noted as Phase 27 code work

---

## Regression Risk

This phase has no code changes. The only regression risk is accidentally touching a source file
during spec writing. Running `just check` after committing spec files confirms the baseline is
intact.
