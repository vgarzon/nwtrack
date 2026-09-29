# Balance Change Threshold Warning — Requirements

## Problem

Entering a new balance for an account is a plain numeric prompt with no sanity check. A typo
(e.g. `1000` instead of `100`) silently overwrites the account's balance for the month. There is
no confirmation step today, in either the CLI or the TUI.

## Scope

**In scope**

- The "update balance" workflow only:
  - CLI: `nwtrack balances update` (`BalanceUpdater` / `update_balances.py`)
  - TUI: the balance edit flow in `BalanceUpdateScreen` / `BalanceEditModal`
- A new configurable percent-change threshold setting.
- When the user enters a new amount whose percent change from the prior balance for that
  account/month exceeds the threshold (in either direction — increase or decrease), show a
  warning naming the direction and percentage, and ask the user to confirm or cancel before the
  write happens.
- Accepting proceeds with the write exactly as today. Cancelling returns the user to re-enter an
  amount (CLI: re-prompt in the same loop iteration; TUI: reopen the edit modal / return to the
  amount input) rather than aborting the whole use case.

**Out of scope (non-goals)**

- `balances create`, `balances roll` (roll-forward), and `balances transfer` are not covered by
  this spec. They may reuse the same threshold-check building block later, but that is a
  separate change.
- Per-account thresholds — only a single global threshold setting.
- Absolute-amount thresholds (e.g. "warn if change > $X") — percent-based only, matching the
  motivating typo scenario (order-of-magnitude entry errors).
- Any change to `balances_aggregate`/reporting.

## Data / Domain Impact

No schema or domain entity changes. This is a workflow-level guard between "user enters an
amount" and "the amount is persisted," implemented in the use case / screen layer using existing
`current_balance` and `new_amount` values that are already fetched/computed today.

## Decisions

1. **Threshold source**: a new `config.toml` setting, following the existing flat-`Settings`-
   dataclass pattern (`src/nwtrack/infra/config/settings.py`, `load.py`):
   - Section: `[balances]`
   - Key: `change_warning_threshold_pct` (float, percent, e.g. `20.0` = 20%)
   - Default: `20.0`
   - Env override: `NWTRACK_BALANCES__CHANGE_WARNING_THRESHOLD_PCT`
   - Documented in `config.example.toml` (commented out, matching the existing convention),
     wired into `describe_settings()` for `nwtrack config show`, and into `init_config.py` if
     that use case enumerates settings explicitly.
   - `load.py` currently only has int/str/path typed getters — this requires adding a float
     getter (e.g. `_float_value`) following the existing `_int_value` pattern.
   - A threshold of `0` disables the check entirely (no warning ever shown) — this gives users
     an explicit off switch without a separate boolean setting.

2. **Percent-change formula**: `pct_change = abs(new_amount - current_balance) / abs(current_balance) * 100`,
   compared against the configured threshold. Warn when `pct_change > threshold`.

3. **No prior balance**: if there is no existing balance for that account/month
   (`current_balance == 0`, per the existing `_update_single_balance` sentinel-zero
   convention) or `current_balance == 0` explicitly, skip the check — there's no meaningful
   percent change to compute against a zero base, and this matches "first entry for the
   account" cases identified during research.

4. **Where the check lives**: a small, presenter/UI-agnostic helper (e.g.
   `application/services/` or a pure function colocated with `update_balances.py`) that takes
   `current_balance`, `new_amount`, `threshold_pct` and returns whether to warn plus the computed
   percent change and direction (increase/decrease). Both the CLI use case and the TUI screen
   call this helper, keeping the math in one place per the "shared logic below the UI layer"
   convention in `specs/tech-stack.md`.

5. **CLI UX**: extend `BalanceUpdatePresenter` (`application/ports/presentation.py`) with a new
   method, e.g. `confirm_large_change(account_name: str, current_balance: int, new_amount: int,
   pct_change: float, increased: bool) -> bool`, implemented in `RichBalanceUpdatePresenter`
   using the existing `prompt_to_confirm_action` helper from
   `entrypoints/cli/ui/prompts.py` (same pattern as `prompt_to_confirm_deletion` /
   `prompt_to_confirm_transfer`). On decline, `_update_single_balance` loops back to
   `show_current_balance_and_prompt` to re-enter an amount rather than aborting the whole
   update loop.

6. **TUI UX**: reuse the existing generic `ConfirmModal` (`entrypoints/tui/screens/
   confirm_modal.py`) via `push_screen_wait`, same pattern already used for `MonthPickerModal`/
   `RollForwardModal`/`TransferModal` in `balance_update.py`. On decline, reopen
   `BalanceEditModal` with the same current amount rather than dismissing the whole edit flow.
   `BalanceUpdateScreen` will need access to `Settings` (or the threshold value) resolved via
   `bootstrap/tui_composition.py`, following the existing DI pattern.

7. **Message copy**: "The value you entered is {pct}% {above/below} the current balance
   ({current} → {new}). Do you want to proceed?" — concrete numbers included, direction stated
   explicitly, matching the user's example phrasing.

## Context

- Follows `specs/tech-stack.md`'s configuration model: TOML + `tomllib`, no new dependencies,
  env-var override convention, `platformdirs` resolution — this feature adds one setting, no new
  config subsystem.
- Follows the existing confirm-prompt conventions in both the CLI (`prompt_to_confirm_action`)
  and TUI (`ConfirmModal`) rather than inventing a new interaction pattern.
- `BalanceUpdateScreen` currently bypasses the presenter/use-case layer entirely and talks to
  `FetchService`/`UnitOfWork` directly (per its own docstring) — the TUI implementation must
  fit that existing shape rather than force it through `BalanceUpdater`.
- This is a guard-rail feature, not a validation-correctness feature: declining never blocks a
  legitimate large change, it just requires one extra confirmation.
