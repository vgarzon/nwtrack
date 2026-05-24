# Phase 26 — TUI Screen Model Design: Plan

## Overview

This is a design-only phase. All tasks produce documentation in `specs/`. No production code
is written or modified.

---

## Task Group 1 — Settle the Three Open Decisions

These are the questions `specs/tui-prototype.md` explicitly requires Phase 26 to answer before
Phase 27 begins.

1.1 Confirm month selection UX decision (modal picker) and document rationale in `requirements.md`.
1.2 Confirm edit input UX decision (overlay modal) and document rationale in `requirements.md`.
1.3 Confirm navigation model (screen stack, per `tui-scope.md`) and document it with the
    transition diagram in `requirements.md`.

---

## Task Group 2 — Screen Inventory

2.1 Write screen inventory table covering all near-term screens (Phases 27–29):
    `HomeScreen`, `BalanceUpdateScreen`, `MonthPickerModal`, `BalanceEditModal`,
    `ReportsMenuScreen`, `NetworthHistoryScreen`, `SingleMonthAggScreen`.
2.2 For each screen record: phase, primary workflow, pushed-from, pops-to.
2.3 Write navigation transition diagram showing all push/pop paths between the above screens.

---

## Task Group 3 — Detailed Wireframes (Phase 27/28 targets)

3.1 `HomeScreen` wireframe: menu items (Balances, Reports), keybinding hints, quit binding.
3.2 `BalanceUpdateScreen` wireframe: account grid, net worth footer, month label in header,
    `[m month]` binding hint.
3.3 `MonthPickerModal` wireframe: month grid, pre-selected current month, Cancel/Select actions.
3.4 `BalanceEditModal` wireframe: account name, current amount, input field, error line,
    Cancel/Save actions.

---

## Task Group 4 — Sketch Wireframes (Phase 29 targets)

4.1 `ReportsMenuScreen` wireframe: list items (Net Worth History, By Dimension), Escape binding.
4.2 `NetworthHistoryScreen` wireframe: scrollable month/assets/liabilities/net table.
4.3 `SingleMonthAggScreen` wireframe: month and dimension header, grouped balance table.
    Note: month and dimension selection mechanism for Phase 29 is left as a TBD in the spec
    (to be resolved before Phase 29 begins).

---

## Task Group 5 — Keyboard Conventions

5.1 Produce keyboard conventions table confirming Textual defaults apply.
5.2 Document the one custom binding added: `m` for month picker on `BalanceUpdateScreen`.
5.3 Confirm no other custom bindings are introduced in Phase 27 or 28.

---

## Task Group 6 — Validation Document

6.1 Write `validation.md` with definition of done, manual review checklist, and quality gates.

---

## Notes

- Task groups 1–5 feed into `requirements.md`; task group 6 produces `validation.md`.
- All wireframes are ASCII; no external diagramming tools required.
- The `reactive[int]` cleanup for net_worth (removing the unused declaration) is documented
  as an implementation note in `requirements.md` but is deferred to Phase 27 as code work.
