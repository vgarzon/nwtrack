# Balance Change Threshold Warning — Validation

## Automated

- `just check` (lint + typecheck + test) passes.
- New/updated unit tests, all passing:
  - `evaluate_balance_change` (or equivalently named helper) covering:
    - No prior balance (`current_balance == 0`) → no warning.
    - Threshold `<= 0` (disabled) → no warning regardless of change size.
    - Change below threshold → no warning.
    - Change above threshold, increase → warning, `increased=True`, correct `pct_change`.
    - Change above threshold, decrease → warning, `increased=False`, correct `pct_change`.
    - Change exactly equal to threshold → no warning (strict `>` semantics).
  - `BalanceUpdater` (CLI use case):
    - Below-threshold amount: `confirm_large_change` is never called; write proceeds.
    - Above-threshold amount + presenter confirms: write proceeds with the entered amount.
    - Above-threshold amount + presenter declines: no write occurs; the use case re-prompts for
      an amount within the same account/loop iteration (does not abort the whole update run).
    - Threshold `0` via config: `confirm_large_change` never called even for large changes.
  - TUI `BalanceUpdateScreen` (or wherever the check lands per plan §4):
    - Same four cases as above, adapted to the modal confirm flow (`ConfirmModal` shown/not
      shown; decline reopens `BalanceEditModal` with the prior amount; accept writes).
  - Config (`tests/infra/config/`):
    - Default `change_warning_threshold_pct` is `20.0` when unset in `config.toml`.
    - `[balances] change_warning_threshold_pct = <n>` in `config.toml` is honored.
    - `NWTRACK_BALANCES__CHANGE_WARNING_THRESHOLD_PCT` env var overrides the file value.
    - `nwtrack config show` lists the field with correct value and source (file/env/default).

## Manual

1. **CLI, no prior balance**: run `nwtrack balances update` (or `just balances-update`) for an
   account/month with no existing balance, enter any amount — no confirmation prompt appears,
   value is saved.
2. **CLI, small change**: for an account with an existing balance, enter a new amount within the
   default 20% threshold — no confirmation prompt, value is saved.
3. **CLI, large increase**: enter an amount > 20% above the current balance — warning shown with
   correct direction ("above") and percentage; confirm → value saved; re-run and decline →
   prompted again for an amount, original value unchanged in the database.
4. **CLI, large decrease**: same as above but for a decrease > 20% ("below" wording), same
   confirm/decline behavior.
5. **TUI equivalent**: repeat cases 1–4 in `nwtrack tui launch` → balance edit flow, confirming
   the `ConfirmModal` message, decline behavior (reopens edit modal with the same value), and
   accept behavior (writes and returns to the balance list).
6. **Config override**: set `[balances] change_warning_threshold_pct = 50` in `config.toml`,
   confirm a 30% change no longer warns; set to `0`, confirm no warning ever appears regardless
   of change size; run `nwtrack config show` and confirm the value/source displayed is correct
   in each case.
7. **Other balance workflows unaffected**: confirm `balances create`, `balances roll`, and
   `balances transfer` behave exactly as before this change (no new prompts) — they are out of
   scope for this spec.

## Tone Check

- Warning copy matches the user's own phrasing: states the percentage, the direction (above/
  below), and asks "Do you want to proceed?" — consistent with existing confirm-prompt tone
  elsewhere in the CLI/TUI (e.g. deletion/transfer confirmations).

## Definition of Done

- All automated tests above pass; `just check` is clean.
- All manual validation steps above performed and confirmed.
- `config.example.toml`, `nwtrack config show`, and `nwtrack config init` (if applicable) reflect
  the new setting.
- No changes to `balances create`, `balances roll`, or `balances transfer` behavior.
- Spec's requirements, plan, and validation are updated in the same change set if implementation
  reveals a better approach than what's written here.
