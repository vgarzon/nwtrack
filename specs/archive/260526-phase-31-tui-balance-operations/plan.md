# Phase 31 Plan: TUI Balance Operations

## Task Groups

### 1. BalanceUpdateScreen — new bindings ✓

1.1 ✓ Add `Binding("r", "roll_forward", "Roll forward")` to `BalanceUpdateScreen.BINDINGS`  
1.2 ✓ Add `Binding("t", "transfer", "Transfer")` to `BalanceUpdateScreen.BINDINGS`  
1.3 ✓ Implement `action_roll_forward`: push `RollForwardModal`; on return, if a new month
    was produced, set `self._month` to the target month and refresh  
1.4 ✓ Implement `action_transfer`: push `TransferModal(month=self._month)`; on return
    refresh table and net worth

---

### 2. Roll-forward screen ✓

2.1 ✓ Implemented `RollForwardModal(ModalScreen[Month | None])` in
    `entrypoints/tui/screens/roll_forward.py`  
  - Constructor: `fetcher: FetchService`, `uow: Callable[[], UnitOfWork]`,
    `source_month: Month`  
  - On mount: computes `target_month` (latest month + 1); warns if target already has balances  
  - Source month changeable via `MonthPickerModal` (binding `m`)  
  - `Ctrl+S` executes roll-forward; `self.dismiss(target_month)` on success  
  - Escape cancels: `self.dismiss(None)`  
  - Guard: if target has balances, or source has no balances, confirm is blocked  
2.2 ✓ `BalanceUpdateScreen.action_roll_forward` receives the dismissed `Month | None`; if
    non-None, sets `self._month = result` and refreshes table + net worth + header

---

### 3. Transfer screen ✓

3.1 ✓ Implemented `TransferModal(ModalScreen[bool])` in
    `entrypoints/tui/screens/transfer.py`  
  - Constructor: `fetcher: FetchService`, `uow: Callable[[], UnitOfWork]`, `month: Month`  
  - Compose: month label (changeable via `m`), From-account `Select`, To-account `Select`,
    Amount `Input`, preview `Label`, error `Label`, hint `Label`  
  - From/to accounts: all active accounts; missing balance treated as 0  
  - Preview panel: shows computed deltas after Ctrl+S validation  
  - `Ctrl+S` to execute: validates (accounts differ, amount > 0), applies deltas atomically  
  - Escape cancels: `self.dismiss(False)`  
  - Delta computation: `_compute_deltas` module-level function with side-aware formula  
  - Missing balance handling: inserts new `Balance` record rather than updating  
3.2 ✓ `BalanceUpdateScreen.action_transfer`: after `TransferModal` returns, refreshes
    table and net worth

---

### 4. Tests ✓

4.1 ✓ All tests consolidated in `tests/entrypoints/tui/test_balance_operations.py`  
  - `TestBalanceUpdateScreenBindings`: r → `RollForwardModal`, t → `TransferModal`,
    r no-op when no month data  
  - `TestRollForwardModal`: target month computation, confirm calls copy_by_month,
    cancel no write, blocked when target has balances, blocked when no data,
    blocked when source has no balances  
  - `TestTransferModal`: cancel no write, same account rejected, zero amount rejected,
    ASSET→ASSET deltas, ASSET→LIABILITY deltas, missing balance inserts new record  
  - `TestComputeDeltas`: all four side combinations  
  - 19 tests, all passing

---

## Recommended Implementation Order

Groups 1 → 2 → 3 → 4.  
Groups 2 and 3 are independent once Group 1 bindings exist.  
Tests in Group 4 can be written alongside each group.
