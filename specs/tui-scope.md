# TUI Transition Scope

## Purpose

This document captures the scope, rationale, and sequencing for transitioning nwtrack from a
Typer-based CLI to a Textual-based terminal user interface (TUI).

The TUI direction is already established in `specs/mission.md`:

> The longer-term direction is a terminal user interface (TUI), not a web app or hosted service.

This document defines what that means concretely, what the transition requires architecturally, and
how to phase the work safely alongside the existing CLI.

## Framework Decision: Textual

**Selected framework: Textual** (https://textual.textualize.io)

Textual is the modern Python TUI framework built by Textualize, the same team behind Rich.
Since Rich is already in the stack, Textual is an extension of the existing investment rather than
a replacement of it.

### Why Textual

- Rich renderables (tables, panels, text markup) work natively inside Textual widgets
- Reactive, component-based model with a CSS-like layout system
- First-class async event handling suited to interactive workflows
- Built-in widgets covering the full range of nwtrack's interactive needs: tables, inputs,
  selection lists, confirmation dialogs, data grids
- Active development with stable API and good documentation
- No dependency on external C libraries; pure Python install

### Frameworks considered and rejected

| Framework    | Reason rejected                                                           |
|--------------|---------------------------------------------------------------------------|
| ncurses      | Low-level C binding; requires significant boilerplate for basic layouts   |
| urwid        | Aging; minimal active development; Rich incompatible                      |
| blessed      | Terminal utility library, not a full application framework                |
| Prompt Toolkit | Better suited to REPL and line-editing use cases than full-screen apps  |

## Benefits of the Transition

### Reactive and interactive

Monthly balance workflows are iterative: select a month, cycle through accounts, update amounts,
see running totals. A Textual app can make this feel fluid — live net worth recalculation as
amounts are entered, keyboard navigation between fields, no round-trip re-renders.

### Improved usability

The current CLI requires users to know command names and option flags. A TUI can expose the same
workflows through a navigable screen hierarchy with visible affordances, making the product more
accessible without removing CLI power for users who prefer it.

### Better data visualization

Rich tables in the CLI are static output. Textual's DataTable widget supports scrolling,
sorting, and selection — useful for account lists, balance history, and aggregated reports that
currently require paging through long terminal output.

## Architectural Readiness

The architecture is already partially positioned for a TUI transition. The ports-and-adapters
presenter pattern means use cases depend on Protocol interfaces, not on Rich or Typer directly.
Textual presenter adapters can be added alongside existing Rich/CLI adapters without modifying
use case or domain code.

### What is already in place

- Presenter Protocol interfaces in `application/ports/presentation.py` define UI contracts
  independently of any rendering technology
- Rich adapter implementations in `entrypoints/cli/adapters/` are already swappable — a
  Textual adapter implementing the same Protocol is a drop-in at the dependency injection layer
- Domain and application layers are fully independent of CLI concerns
- The bootstrap container supports registering different adapters per composition root

### What is incomplete

The presenter migration is complete as of Phase 24. All interactive use cases accept a presenter
via constructor and have no direct console imports in their use case class bodies. Rich imports
that remain in use case modules are scoped to `main()` DI wiring functions only and do not
affect the use case class logic or TUI adapter compatibility.

## Dual-Mode Strategy

The CLI and TUI should coexist during the transition. This is achievable because the same use
cases and presenter Protocols serve both interfaces — only the adapter implementations differ.

Proposed entry points:

- `nwtrack <command>` — existing CLI surface, unchanged
- `nwtrack tui` — launches the full Textual application

This approach allows the TUI to be developed and validated incrementally without disrupting the
working CLI. Workflows can migrate to Textual one screen at a time.

The CLI surface should be retired only after the TUI covers its full workflow scope and has been
validated against real usage.

## Proposed Sequencing

### ~~Step 1: Complete presenter protocol migration (prerequisite)~~ ✓ Done (Phase 24)

#### Audit results (final, as of 2026-05-23)

The presenter migration is complete. All interactive use cases accept a presenter via constructor
and have no direct console imports in use case class bodies. Every defined Protocol has a
corresponding Rich adapter.

**Migrated:** all account, category, institution, tag, balance, report, admin, database init,
import CSV, and export CSV use cases — including `roll_balances_forward`, which was migrated
prior to the audit.

**Not applicable:** `report_single_month_aggregation.py` and `report_history_aggregation.py` are
data-only query wrappers with no UI interaction; no presenter is needed.

#### Deliverables (completed)

- `ImportTablesCSVPresenter` Protocol defined in `application/ports/presentation.py`
- `ExportTablesCSVPresenter` Protocol defined in `application/ports/presentation.py`
- `RichImportTablesCSVPresenter` adapter implemented in `entrypoints/cli/adapters/csv_presenters.py`
- `RichExportTablesCSVPresenter` adapter implemented in `entrypoints/cli/adapters/csv_presenters.py`
- Both use cases refactored to accept presenter via constructor; direct console imports removed
- Both use cases unit-testable via mock presenter without a real terminal

### ~~Step 2: Prototype one Textual screen~~ ✓ Done (Phase 25)

#### Findings (final, as of 2026-05-24)

The prototype validated that Textual can drive the balance update workflow against a real
SQLite database. The adapter-swap pattern does **not** apply to interactive-prompt presenter
methods: `BalanceUpdatePresenter.prompt_for_account_id()` and `show_current_balance_and_prompt()`
are synchronous blocking calls incompatible with Textual's async event model without complex,
fragile synchronization machinery.

The correct pattern is **screen-owned workflow**: screens call `FetchService` and `UnitOfWork`
directly from event handlers rather than driving existing `run()` methods through a presenter
adapter. Display-only presenter methods could still be ported as adapters, but interactive
prompt methods must be replaced by Textual event handlers wired to reactive state.

Full findings documented in:
- `specs/260523-phase-25-tui-textual-balance-prototype/requirements.md` (Findings section)
- `specs/tui-prototype.md` (implementation patterns, API notes, deferred items)

#### Deliverables (completed)

- `textual>=3.0.0` added to `pyproject.toml` as a main dependency
- `bootstrap/tui_composition.py` wires `FetchService` and `UnitOfWork` for the TUI without
  modifying the CLI composition root
- `entrypoints/tui/app.py` — `NWTrackApp` Textual application
- `entrypoints/tui/screens/balance_update.py` — `BalanceUpdateScreen` with editable grid,
  inline input on Enter, row and net worth updates after submission
- `entrypoints/cli/commands/tui.py` — `nwtrack tui launch` CLI entry point
- Existing `nwtrack balances update` CLI command confirmed unmodified; `just check` passes

### Step 3: Design the TUI screen model

A TUI is not a visual port of CLI commands. Screens, navigation, and state do not map 1:1 to
individual command invocations. The interaction model should be designed before building it.

This step should define:
- Top-level navigation structure (screen hierarchy or tab model)
- Which workflows are primary (monthly balance entry, reports) versus administrative (account
  management, institution and tag CRUD)
- Keyboard navigation conventions
- How report output integrates with the interactive workflow (e.g., live net worth panel visible
  during balance update)

Deliverables:
- Screen inventory and navigation design document
- Wireframe or textual mockup of the primary workflow screen
- Keyboard shortcut conventions

### Step 4: Incremental screen buildout

Build remaining Textual screens one workflow at a time, following the presenter-adapter pattern
proven in Step 2. Prioritize by usage frequency.

Suggested order:
1. Balance update (Step 2 prototype, already done)
2. Reports — single-month and history aggregation
3. Account list and management
4. Balance roll-forward, delete, transfer
5. Administrative CRUD — categories, institutions, tags

### Step 5: CLI retirement

Once the TUI covers the full workflow scope and has been validated against real data, deprecate
and remove the CLI entry points. The application composition root, Typer app registration, and
CLI-specific presenter adapters can all be removed at this point.

The `nwtrack tui` entry point becomes `nwtrack`.

## Out of Scope for This Exploration

- Web interface of any kind
- Mouse-driven interaction beyond what Textual supports by default
- Multi-user or remote terminal support
- Changes to the domain model, persistence layer, or use case logic as part of TUI work
- Automated testing of Textual widget rendering (snapshot tests are possible but deferred)

## Roadmap Integration

The TUI transition should be reflected in `specs/roadmap.md` as one or more phases once the
screen design (Step 3) is complete and the scope is concrete enough to phase. The current open
phases (24–26) are independent of the TUI work and should proceed on their existing schedule.

A suggested insertion point is after Phase 26, once the reporting model is stable, since the
TUI will need to render the full reporting surface to be considered complete.

## Design Decisions

The following questions were evaluated and resolved before implementation begins.

### Navigation model: screen stack

The TUI uses Textual's native screen stack. The home screen is a menu; selecting a workflow pushes
a new screen. Escape pops back to the previous screen. This model is native to Textual, well-suited
to multi-step confirmation flows (balance entry, transfers, deletions), and avoids the layout
complexity of maintaining a persistent tab bar while workflows are in progress.

```
┌─────────────────────────────────────┐
│  nwtrack                     [q quit]│
├─────────────────────────────────────┤
│                                     │
│   > Balances                        │
│     Reports                         │
│     Accounts                        │
│     Admin                           │
│                                     │
└─────────────────────────────────────┘
  (enter → pushes workflow screen)
```

### Report rendering: dedicated screens

Reports are full screens, not panels embedded in other workflows. The user navigates to a report
screen, views scrollable output, and presses Escape to return. This keeps report screens simple
and focused, and avoids the layout and reactivity complexity of a split-panel design.

A live net worth summary panel alongside balance entry is explicitly deferred. It can be
considered after the core screen model is proven.

```
┌─────────────────────────────────────┐
│  ← Reports / Net Worth History      │
├─────────────────────────────────────┤
│ Month    Assets    Liab     Net      │
│ 2025-01  120,000   40,000   80,000   │
│ 2025-02  121,500   39,800   81,700   │
│ 2025-03  119,000   39,500   79,500   │
│ ...                                 │
│ [scrollable]                        │
└─────────────────────────────────────┘
```

### Balance entry UX: editable grid

The balance entry screen presents all accounts for the selected month in a scrollable editable
grid. The cursor navigates freely between rows; pressing Enter on a row opens an inline edit input
for that account's amount. This is a deliberate departure from the CLI's sequential prompt loop —
the grid model is non-linear, faster for experienced users, and takes advantage of the persistent
screen context that the TUI provides.

```
┌─────────────────────────────────────┐
│ Update Balances — 2025-03           │
├──────────────────────┬──────────────┤
│ Account              │ Amount       │
├──────────────────────┼──────────────┤
│ Checking             │ $ 5,200      │
│ Savings              │ $ 15,000     │
│▶ TFSA                │ [  8,300   ] │
│ Mortgage             │ $ 240,000    │
└──────────────────────┴──────────────┘
  (↑↓ navigate, enter to edit)
```

### Keybinding conventions: Textual defaults

The TUI follows Textual's default keybinding conventions without custom overrides:

| Key        | Action                     |
|------------|----------------------------|
| `q`        | Quit / close               |
| `Escape`   | Back / cancel              |
| `Tab`      | Next focusable element     |
| `Shift+Tab`| Previous focusable element |
| `↑` `↓`   | Navigate list              |
| `Enter`    | Confirm / select           |
| `?`        | Show help                  |

Custom bindings may be added for application-specific shortcuts (e.g., a hotkey to jump directly
to balance entry), but the baseline navigation layer follows Textual's conventions so users
familiar with other TUI tools have no relearning cost.
