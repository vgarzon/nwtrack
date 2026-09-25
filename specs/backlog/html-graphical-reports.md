---
name: html-graphical-reports
status: ready
---

## Problem

Current reporting output is limited to terminal tables (Rich/Textual) and CSV. Some reporting
needs — sharing a trend visually, reviewing net worth trajectory graphically — are better served
by a chart than a table.

## Scope

Add the ability to export the net worth history report and the single-account balance history
report ([[account-balance-history]], shipped) as self-contained HTML files with embedded charts,
triggered from both the CLI and the TUI.

Per the local-first, dependency-light standard in `specs/tech-stack.md`, generated HTML files
must be self-contained: viewable offline in a browser with no network calls, using an embedded
minimal charting library rather than a CDN dependency.

## Expected outcomes

- A new export use case renders the net worth history report as a single self-contained HTML
  file with an embedded line chart (net worth, assets, and liabilities over time), with no
  external network dependency required to view it
- The same export path supports the single-account balance history report as a line chart of
  balance over time
- A new CLI command (e.g. `nwtrack reports export-html`) accepts a report selection and target
  file path, mirroring the existing CSV export command pattern
- A TUI action on the relevant report screens triggers the same export use case and reports the
  output file path to the user
- Output-format and file-path handling preserve current default behavior for existing report
  commands; HTML export is strictly additive
- `ruff`, `mypy`, and `pytest` pass

## Notes

Formerly "Phase 42" in the old roadmap. No blockers — can be picked up next.
