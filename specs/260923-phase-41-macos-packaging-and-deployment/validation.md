# Phase 41: macOS Packaging And Deployment — Validation

## Progress Log

### Group 1: Repo & Packaging Metadata — DONE

- Added `LICENSE` (MIT).
- Added `license = "MIT"`, `license-files`, `classifiers`, and `[project.urls]` to
  `pyproject.toml`; no dependency changes.
- `uv sync` succeeds with the updated metadata.
- `uv build` succeeds, producing a valid sdist and wheel (`nwtrack-0.1.0.tar.gz`,
  `nwtrack-0.1.0-py3-none-any.whl`) in a scratch output directory.
- `just check` (ruff, mypy, pytest — 423 tests) passes with no changes needed.

### Groups 2 & 3: Versioning Scheme & Release Process — DONE

- Added a "Release Process" section to `specs/tech-stack.md` (after Development Workflow):
  semantic versioning convention, `vX.Y.Z` tagging, and the bump → commit → tag → push →
  GitHub release steps.
- No code changes; documentation only.

### Groups 4 & 5: Install & Upgrade Path Verification — DONE

- Installed `nwtrack` as a `uv tool` from a local `git+file://` URL (stand-in for
  `git+https://github.com/vgarzon/nwtrack`) into an isolated environment; confirmed `nwtrack`
  resolves on `PATH`, `--help` lists all sub-apps, and `nwtrack tui launch` renders correctly.
- Confirmed first-run directory bootstrap works from a scratch `$HOME`/`cwd` outside the
  source checkout (`config init`, `config show`, `accounts list` all correctly
  create/report `platformdirs`-resolved paths). No code changes needed.
- Found and documented a real but expected nuance: running the installed tool from inside
  the dev checkout directory picks up `./config/nwtrack/config.toml` (the intentional
  Phase-40 working-directory-relative fallback) — not a bug, but worth a README callout.
- Confirmed `uv tool upgrade nwtrack` is a no-op for a tag-pinned install (tags are
  immutable refs). Confirmed `uv tool install --reinstall-package nwtrack git+<repo-url>@<new-tag>`
  correctly moves the install to a new tag/version. This is the command documented in the
  README's "Upgrading" section.
- All test installs, test tags (`v0.0.1-test`, `v0.1.1-test`), and one temporary test commit
  were fully cleaned up afterward — `git log` and `git tag` show no trace.

## Automated

- `ruff` passes with no new findings.
- `mypy` passes with no new findings.
- `pytest` passes (full suite) — this phase is expected to be documentation/metadata-only
  unless Group 4.4 (first-run bootstrap gap) requires a code fix, in which case that fix
  needs its own targeted test(s) under `tests/`.
- If `pyproject.toml` metadata changes (classifiers, `[project.urls]`), confirm `uv sync`
  and `uv build` (or `uv tool install .` from the checkout) still succeed — a malformed
  `pyproject.toml` should fail loudly here, not silently.

## Manual

Perform this walkthrough in a throwaway location (temp directory or scratch venv), **not**
the primary dev checkout, so it exercises the same conditions a real user hits:

1. **Fresh install**: `uv tool install git+<repo-url>@<tag-or-branch>` succeeds and `nwtrack`
   resolves on `PATH` in a new shell.
2. **CLI entry point**: `nwtrack --help` runs and lists the expected sub-apps (`accounts`,
   `balances`, `categories`, `institutions`, `tags`, `reports`, `export`, `import`, `admin`,
   `tui`, `config`).
3. **TUI entry point**: `nwtrack tui launch` opens the Textual application.
4. **First-run bootstrap**: with no pre-existing `nwtrack` config/data/log directories,
   `nwtrack accounts list` (or equivalent) creates the `platformdirs`-resolved data and log
   directories automatically, without error, matching documented Phase 40 behavior.
5. **Config init**: `nwtrack config init` writes a default `config.toml` to the expected
   `platformdirs`-resolved location from the installed tool's context (not the dev
   checkout's `./config/nwtrack/` fallback, since there's no working-directory checkout in
   this context).
6. **Config show**: `nwtrack config show` reports the active config path and resolved
   settings correctly from the installed context.
7. **Upgrade**: after a newer tagged commit exists, run the documented upgrade command (per
   plan.md Group 5) and confirm `nwtrack --version` (or equivalent) reflects the new version,
   or that behavior tied to the newer commit is present.
8. **Uninstall**: `uv tool uninstall nwtrack` removes the tool from `PATH`; confirm
   config/data/log files are left untouched (by design) and note this in the README.
9. **README walkthrough**: follow the README's Installation, Upgrading, and Uninstalling
   sections verbatim, as if a new user, and confirm every command in them works exactly as
   written with no missing steps.

## Definition of Done

- `uv tool install git+<repo-url>@<tag>` is a proven, working install path for a clean
  environment with no source checkout.
- The upgrade command documented in the README is the one actually verified to work in
  Group 5 of `plan.md` — not an assumed/unverified `uv tool upgrade` if that turns out not to
  apply cleanly to a git-pinned install.
- First-run directory bootstrap is confirmed working (or fixed) under a packaged install,
  not just under `uv run` from a checkout.
- `pyproject.toml` carries packaging-ready metadata (version, classifiers, project URLs) and
  a defined semantic-versioning convention.
- A documented release process (tag → GitHub release) exists and was exercised at least once
  to produce the tag used in manual validation.
- README's Installation/Upgrading/Uninstalling sections are accurate end-to-end, verified by
  literally following them, and the existing source-checkout (`uv sync`) instructions remain
  intact alongside the new packaged-install path.
- `ruff`, `mypy`, `pytest` pass.
