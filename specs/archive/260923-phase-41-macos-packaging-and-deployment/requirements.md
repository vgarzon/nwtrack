# Phase 41: macOS Packaging And Deployment — Requirements

## Scope

Keep this phase simple. It covers four things, and nothing beyond them:

1. **Installation via `uv`** — a documented, working `uv tool install` path from the
   `nwtrack` GitHub repository (not PyPI).
2. **Configuration** — largely already done in Phase 40 (TOML config resolved via
   `platformdirs`). This phase only verifies that first-run directory bootstrap (config,
   data, log directories) works correctly under a `uv tool install`-installed binary, since
   that's a different execution context than `uv run` from a source checkout.
3. **Instructions / documentation** — README install, upgrade, and uninstall sections, plus
   a documented GitHub release process (tagging convention) that produces the refs the
   install command points at.
4. **Upgradeability** — a documented, working `uv tool upgrade` (or equivalent reinstall)
   path, backed by a defined versioning scheme.

### In scope

| Area | Included |
|---|---|
| Install source | `uv tool install git+https://github.com/vgarzon/nwtrack@<ref>` (git-based, not PyPI) |
| Entry points | Existing single `nwtrack` console script (already covers both CLI and `nwtrack tui launch`) — verified under a packaged install, not re-architected |
| First-run bootstrap | Verification that config/data/log directories are created automatically on first run when installed via `uv tool install` (mechanism already exists from Phase 40; this phase confirms it holds outside a source checkout) |
| Packaging metadata | `pyproject.toml` reviewed for packaging-readiness: version field, classifiers, project URLs |
| Versioning scheme | Semantic versioning (`MAJOR.MINOR.PATCH`), manually bumped in `pyproject.toml` per release, starting from the current `0.1.0` |
| Release process | Documented convention: bump version → tag (`vX.Y.Z`) → push tag → create GitHub release; this is what the `@<ref>` in the install command points at |
| Upgrade path | `uv tool upgrade nwtrack` documented as the supported upgrade command; spec must confirm during validation whether this actually re-resolves a git-sourced tool pinned to a tag, or whether `uv tool install --reinstall-package nwtrack git+...@<new-tag>` is the correct command, and document whichever is accurate |
| Documentation | README "Installation" section rewritten to cover the packaged install path (source-checkout `uv sync` instructions are kept alongside it, not replaced — Phase 42/future-CLI-retirement concerns are out of scope) |

### Out of scope

- Publishing to PyPI (explicitly deferred; install is git-based for this phase)
- Code signing and notarization (explicitly out of scope per roadmap)
- A compiled/bundled binary or `.app`/`.pkg` installer
- Any change to the CLI/TUI entry-point structure itself
- Windows/Linux packaging (macOS is the target per roadmap phase title; the mechanism is
  cross-platform in practice via `uv`, but validation and documentation focus on macOS)
- Automated CI-driven release publishing (release process is manual/documented, not automated
  in this phase)

## Decisions

- **Install source is Git, not PyPI.** `uv tool install git+https://github.com/vgarzon/nwtrack@<tag>`
  is the supported install command (plain HTTPS, since the repo is public). Avoids a
  publishing pipeline for this phase while still giving users a `PATH`-available `nwtrack`
  command without a manual clone.
- **Add an MIT `LICENSE` file.** The repo has none today; a public install command implies a
  public license. MIT is chosen as a permissive, low-friction default appropriate for a
  personal/learning project with no prior license commitments.
- **Upgrade path is `uv tool upgrade`,** confirmed and documented precisely (see Validation) —
  if `uv tool upgrade` does not correctly move a git-tag-pinned install forward, the README
  documents the accurate reinstall command instead of a command that doesn't work.
- **Versioning is manual semantic versioning.** No automated version-bump tooling in this
  phase; `pyproject.toml`'s `version` field is bumped by hand as part of the release process.
- **Release process is a documented manual convention**, not new tooling: bump version in
  `pyproject.toml` → commit → `git tag vX.Y.Z` → `git push --tags` → create a GitHub release
  from that tag. The install/upgrade commands reference the tag.
- **First-run bootstrap is verification, not new implementation.** Phase 40 already wires
  `platformdirs`-based directory creation; this phase's job is to prove it holds when
  `nwtrack` runs as a `uv tool install`-installed entry point (different working directory
  and Python environment than `uv run` from a checkout), and fix it only if it doesn't.

## Context

- Builds directly on Phase 40 (TOML config via `platformdirs`) — do not re-litigate config
  resolution order or precedence; only verify it holds under the new install mechanism.
- Per `specs/tech-stack.md`, keep local workflows fast and dependency-light — no new runtime
  dependencies are expected for this phase.
- Per `specs/tech-stack.md` Documentation Rules, README content stays user-oriented;
  long-lived architectural direction stays out of README and in the constitution docs.
- Repo remote is `git@github.com:vgarzon/nwtrack.git`; the repo is **public**, so the
  documented install command is plain HTTPS: `uv tool install git+https://github.com/vgarzon/nwtrack@<tag>`
  — no SSH or PAT auth needed in the README.
- No `LICENSE` file currently exists in the repo. Since this phase documents a public-facing
  install command, **add a `LICENSE` file (MIT)** as part of the packaging metadata work in
  Group 1, and reference it from `pyproject.toml`'s classifiers.
