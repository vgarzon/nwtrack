---
name: cli-retirement
status: idea
---

## Problem

Retire the CLI entry points once the TUI covers the full workflow scope and has been validated
against real usage.

`tui-scope.md` defines CLI retirement as the final step: the `nwtrack tui` entry point becomes
`nwtrack`. This is optional — the CLI and TUI may coexist indefinitely if the dual-mode workflow
proves useful in practice. Should not be picked up until the TUI has been validated against real
data over time.

## Expected outcomes

- All Typer command groups and CLI presenter adapters are removed
- `bootstrap/composition.py` CLI-specific registrations are removed or folded into the TUI
  composition root
- `[project.scripts]` in `pyproject.toml` points `nwtrack` at the TUI entry point
- Existing `tests/entrypoints/` CLI tests are removed or migrated to TUI equivalents
- `ruff`, `mypy`, and `pytest` pass with no orphaned CLI references

## Notes

Formerly "Phase 36 (On Hold, Optional)" in the old roadmap.
