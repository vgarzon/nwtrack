---
name: transfer-modal-focus-stays-on-destination
status: reported
severity: minor
---

## Symptom

In the TUI transfer balances modal, after the user selects the destination account, keyboard
focus stays on the destination account selector instead of moving to the amount text box.

## Repro steps

1. Launch the TUI and open the transfer balances modal.
2. Select a destination account.

## Expected vs actual

- Expected: focus moves to the amount input so the user can type the amount immediately.
- Actual: focus remains on the destination account selector.

## Version / environment

Not provided.

## Suspected area

`src/nwtrack/entrypoints/tui/screens/transfer.py` (destination selection handler).

## Diagnosis
