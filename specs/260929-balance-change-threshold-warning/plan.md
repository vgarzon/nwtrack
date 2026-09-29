# Balance Change Threshold Warning — Plan

## 1. Config

1.1. Add `_float_value` typed getter in `src/nwtrack/infra/config/load.py`, following the
     existing `_int_value` pattern.

1.2. Add `change_warning_threshold_pct: float` field to `Settings`
     (`src/nwtrack/infra/config/settings.py`), default `20.0`.

1.3. In `load.py`'s `_resolve()`: read `data.get("balances", {})`, resolve
     `change_warning_threshold_pct` via `_float_value`, register the
     `NWTRACK_BALANCES__CHANGE_WARNING_THRESHOLD_PCT` env var in `_ENV_VARS`, and track its
     `ConfigValueSource`.

1.4. Add the field to `describe_settings()` (for `nwtrack config show`) with a description.

1.5. Document `[balances] change_warning_threshold_pct` (commented out, default noted) in
     `config.example.toml`, matching the `[database]`/`[logging]` style.

1.6. Update `init_config.py` if it enumerates settings/sections explicitly, so `nwtrack config
     init` output stays consistent.

## 2. Shared threshold-check logic

2.1. Add a small pure function, e.g. `evaluate_balance_change(current_balance: int, new_amount:
     int, threshold_pct: float) -> BalanceChangeWarning | None` (a small dataclass/NamedTuple
     with `pct_change: float` and `increased: bool`, or `None` if no warning is needed).
     Location: colocate with `update_balances.py` in `application/use_cases/`, or a new
     `application/services/` helper if that fits existing conventions better — confirm during
     implementation which is more consistent with current module boundaries.

2.2. Rules: return `None` if `current_balance == 0` (no prior balance) or `threshold_pct <= 0`
     (disabled). Otherwise compute `pct_change = abs(new_amount - current_balance) /
     abs(current_balance) * 100`; return a warning if `pct_change > threshold_pct`.

2.3. Unit tests for this function: no-prior-balance skip, disabled-threshold skip, under-
     threshold no-warning, over-threshold increase, over-threshold decrease, exact-boundary
     (`pct_change == threshold_pct` → no warning, since the rule is strictly `>`).

## 3. CLI (`BalanceUpdater`)

3.1. Extend `BalanceUpdatePresenter` protocol
     (`application/ports/presentation.py`) with `confirm_large_change(account_name: str,
     current_balance: int, new_amount: int, pct_change: float, increased: bool) -> bool`.

3.2. Implement `RichBalanceUpdatePresenter.confirm_large_change` using
     `prompt_to_confirm_action` from `entrypoints/cli/ui/prompts.py`, with the message copy from
     `requirements.md` §7.

3.3. Wire `Settings` (or just the resolved threshold float) into `BalanceUpdater`'s constructor,
     following the existing DI pattern in `main()` (`update_balances.py`).

3.4. In `_update_single_balance`: after `show_current_balance_and_prompt` returns `new_amount`
     and before the `uow().balances.update(...)` call, run `evaluate_balance_change(...)`; if it
     returns a warning, call `presenter.confirm_large_change(...)`; on decline, loop back to
     re-prompt for an amount (do not proceed to the write, do not abort the whole update loop).

## 4. TUI (`BalanceUpdateScreen` / `BalanceEditModal`)

4.1. Resolve the threshold value into `BalanceUpdateScreen` via `bootstrap/tui_composition.py`
     (same pattern as its existing `FetchService`/`UnitOfWork` access).

4.2. After `BalanceEditModal` returns a non-`None` amount (`balance_update.py`, currently around
     line 149-164) and before `uow().balances.update(...)`, call
     `evaluate_balance_change(...)`.

4.3. If a warning is returned, `await self.push_screen_wait(ConfirmModal(message))` with the
     copy from `requirements.md` §7; on `False`, reopen `BalanceEditModal` with the same
     `current_amount` instead of writing.

## 5. Tests

5.1. Unit tests for `evaluate_balance_change` (see 2.3).

5.2. `BalanceUpdater`/CLI use case tests: confirm-declined path re-prompts and does not write;
     confirm-accepted path writes; below-threshold path never calls the confirm presenter
     method; disabled-threshold (`0`) never calls it.

5.3. TUI screen tests (`tests/entrypoints/tui/`): equivalent coverage for the modal-confirm path,
     using existing TUI test patterns (e.g. however `RollForwardModal`/`TransferModal` are
     tested today).

5.4. Config tests (`tests/infra/config/`): default value, TOML override, env-var override,
     `config show` reflects the new field and its source.

## 6. Docs

6.1. Update `CHANGELOG.md` per the usual "Upcoming work" convention once merged (per project
     workflow, not part of this spec's own deliverable — done at ship time per the backlog
     skill's completion step).
