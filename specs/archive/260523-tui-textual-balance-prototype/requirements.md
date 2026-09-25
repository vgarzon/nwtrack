# Requirements — TUI Step 2: Textual Balance Update Prototype

## Scope

### In scope

- Add `textual` as a project dependency in `pyproject.toml`
- Add a `nwtrack tui` CLI entry point that launches the Textual application
- Implement a Textual balance update screen wired to the real SQLite database through the
  existing `FetchService` and `UnitOfWork` infrastructure
- The screen presents accounts for a selected month in a scrollable editable grid; the user
  navigates rows with arrow keys and presses Enter to edit an account's balance inline
- A separate TUI composition root (`bootstrap/tui_composition.py` or similar) wires
  `FetchService`, `UnitOfWork`, and any TUI-specific dependencies; the CLI composition root
  is not modified
- The existing `nwtrack balances update` CLI command continues to work unmodified

### Out of scope

- Any screen other than balance update (no home menu, no navigation hierarchy, no other
  workflows — those are Step 3 and Step 4 work)
- Month selection redesign — the prototype can use a simple modal or hardcoded most-recent-month
  to keep the scope small; the full month picker UX can be designed later
- Automated Textual snapshot or UI tests — manual validation only for this phase
- Retiring or modifying any existing CLI presenter adapter or CLI command
- Changes to the domain model, application use cases, or persistence layer

### Key architectural question this prototype must answer

The existing `BalanceUpdatePresenter` Protocol is synchronous and sequential:
`prompt_for_account_id()` and `show_current_balance_and_prompt()` block until the user responds.
Textual is async and event-driven. These models are fundamentally incompatible without
threading or synchronization machinery.

The prototype should attempt to drive the existing `BalanceUpdater.run()` in a Textual worker
thread with synchronization primitives bridging presenter calls to the Textual event loop.
If that is unworkable in practice, the prototype may instead have the Textual screen own the
full workflow (calling `FetchService` and `UnitOfWork` directly) and document the Protocol
compatibility gap as a concrete finding for Step 3 screen design.

Either outcome is valid. The prototype's job is to surface the real constraint, not to assume
the adapter-swap pattern works as originally described.

## Decisions

### Textual as a project dependency (not dev-only)

`textual` is added to the main dependency list because the `nwtrack tui` entry point is a
first-class product feature, not a development tool.

### Separate TUI composition root

A new composition module wires Textual presenter adapters without touching the CLI composition
root. This is the same pattern established by the existing `bootstrap/composition.py` for CLI
commands. The CLI and TUI share the same `FetchService`, `UnitOfWork`, and domain infrastructure.

### Editable grid UX (non-linear, cursor-based)

The balance entry screen presents all accounts for the selected month in a `DataTable` widget.
The cursor moves freely between rows with arrow keys. Pressing Enter on a row opens an inline
input for that account's amount. This departs from the CLI's sequential prompt loop and takes
advantage of the persistent screen context that the TUI provides.

### Prototype is explicitly exploratory

Code structure may be revised during Step 4 (full screen buildout). The prototype is licensed
to take shortcuts — hardcoded screen structure, minimal error handling, simplified month
selection — as long as the core claim (Textual driving the balance update workflow against a
real database) is validated.

### No snapshot or automated UI tests in this phase

Textual snapshot testing exists and is documented, but is deferred. This phase validates
through manual interaction only.

## Findings

### Protocol compatibility spike result

**Finding: the adapter-swap pattern is not viable for interactive prompt methods.**

`BalanceUpdater.run()` was not driven from a Textual `@work` worker thread. Here is why.

The `BalanceUpdatePresenter` Protocol has two blocking prompt methods:
`prompt_for_account_id()` and `show_current_balance_and_prompt()`. Both are expected to
block until the user submits a value. In the CLI they do so by calling Rich's `Prompt.ask()`,
which reads from stdin.

In a Textual application Textual owns the terminal — stdin is not available for arbitrary
blocking reads. A worker-thread approach with `threading.Event` synchronization (worker blocks
on the event; Textual's event handler sets the event after user submission) is theoretically
possible but introduces:

- **Deadlock risk**: If the worker holds a resource the event loop needs, or vice versa, the
  application hangs. With sequential prompt→response cycles this is hard to avoid safely.
- **Complexity without benefit**: The resulting presenter adapter would be difficult to reason
  about, harder to test, and fragile under Textual version updates.
- **Wrong UX model**: Even if synchronization worked, the resulting interaction would be
  sequential (one prompt at a time) — identical to the CLI experience. The goal of the TUI
  is a non-linear grid where the cursor navigates freely and edits any row in any order.

**Conclusion:** The `BalanceUpdatePresenter` Protocol's sequential prompt model is
incompatible with Textual's reactive event-driven model in practice, not just in theory.
The adapter-swap pattern applies cleanly to display-only presenter methods (tables, headers,
net worth display) but cannot be applied to the interactive prompt methods without significant
synchronization machinery.

**Implemented approach:** The `BalanceUpdateScreen` owns the full workflow. It calls
`FetchService` and `UnitOfWork` directly — no `BalanceUpdater.run()` involved. The DataTable
provides a non-linear cursor-driven grid; pressing Enter opens an inline `Input` pre-filled
with the current amount; submission writes through `UnitOfWork` and refreshes the row and net
worth label reactively.

**Implications for Step 3 and Step 4:**

- Display-only presenter methods can be ported to Textual adapters straightforwardly.
- Interactive-prompt presenter methods need to be redesigned around Textual's event model
  (event handlers + reactive state) rather than wrapped in synchronization machinery.
- Future screens should own their workflow logic directly, calling services and the UoW from
  event handlers, rather than driving existing `run()` methods through adapter presenters.

## Context

- This is Step 2 of the TUI transition sequence defined in `specs/tui-scope.md`
- The prototype should be honest about what the adapter-swap pattern requires in practice;
  documenting a finding is as valuable as proving the pattern works
- The Python stack (SQLAlchemy, uv, mypy, ruff) is unchanged; Textual is the only new dependency
- The balance update workflow is the highest-value interactive workflow in the product and
  benefits most from the reactive, non-linear grid model
- Existing patterns to follow: `bootstrap/composition.py` for DI wiring;
  `entrypoints/cli/adapters/balance_presenters.py` for adapter structure
