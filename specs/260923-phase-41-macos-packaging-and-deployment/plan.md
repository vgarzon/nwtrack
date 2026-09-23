# Phase 41: macOS Packaging And Deployment — Plan

## 1. Repo & Packaging Metadata — DONE

1.1. Add an MIT `LICENSE` file at the repo root (repo is confirmed public). — DONE

1.2. Review `pyproject.toml` `[project]` metadata for packaging-readiness: `version`,
     `description`, `readme`, `requires-python`, add `license = "MIT"`, `classifiers`, and
     `[project.urls]` (Repository/Homepage) pointing at `https://github.com/vgarzon/nwtrack`.
     No dependency changes. — DONE

1.3. Confirm `[project.scripts]` still only needs the single `nwtrack` entry (CLI +
     `nwtrack tui launch`); no new script entry required. — DONE (confirmed unchanged)

## 2. Versioning Scheme — DONE

2.1. Adopt semantic versioning (`MAJOR.MINOR.PATCH`) starting from the current `0.1.0`. — DONE
     (documented in `specs/tech-stack.md` Release Process section; `pyproject.toml` already
     at `0.1.0` from Group 1)

2.2. Document the version-bump step as part of the release process (see Group 3) — manual
     edit to `pyproject.toml`'s `version` field, no automated bump tooling. — DONE

## 3. Release Process Documentation — DONE

3.1. Define and document the tagging convention: `vX.Y.Z` git tags on `main`. — DONE

3.2. Document the release steps: bump `version` in `pyproject.toml` → commit → `git tag
     vX.Y.Z` → `git push --tags` → create a GitHub release from that tag (via `gh release
     create` or the GitHub UI). — DONE

3.3. Write this as a short "Releasing" section — placement TBD during implementation
     (README vs. `specs/tech-stack.md` Development Workflow vs. a `CONTRIBUTING.md`); default
     to README unless it clutters the user-facing install docs, in which case put it in
     `specs/tech-stack.md`. — DONE: placed in `specs/tech-stack.md` as a new "Release
     Process" section (maintainer/engineering standard, not end-user README content per
     Documentation Rules)

## 4. Install Path Verification — DONE

4.1. In a throwaway environment (e.g. a temp dir or a scratch venv, not the dev checkout),
     run `uv tool install git+<repo-url>@<test-tag-or-branch>` and confirm `nwtrack` resolves
     on `PATH`. — DONE, tested against `git+file:///Users/victor/repos/nwtrack@<branch>`
     (a local git URL stands in for `https://github.com/...` without pushing anything
     upstream before this PR lands — same `uv tool install git+...` mechanism)

4.2. Confirm `nwtrack --help` and `nwtrack tui launch` both work from the installed tool. —
     DONE: `--help` lists all expected sub-apps; `tui launch` renders the home screen
     (Balances/Reports/Accounts/Admin) correctly

4.3. Confirm first-run directory bootstrap: with no existing config/data/log directories,
     run a command that touches the database (e.g. `nwtrack accounts list`) and confirm the
     `platformdirs`-resolved data/log directories are created automatically, matching Phase
     40 behavior under `uv run`. — DONE, confirmed from a scratch `$HOME` and scratch `cwd`
     outside the source checkout: `config init`, `config show`, and `accounts list` all
     correctly create/report `~/Library/Application Support/nwtrack/` (db + config) and
     `~/Library/Logs/nwtrack/` (log) with no manual setup. **Caveat found**: running the
     installed tool from *inside* the source checkout directory picks up the checkout's
     `./config/nwtrack/config.toml` working-directory-relative fallback (by design, per
     Phase 40 — see `specs/tech-stack.md` Configuration Model) instead of the scratch
     `$HOME` paths. This is expected/correct behavior, not a bug, but worth calling out in
     README so users understand the checkout-relative fallback only applies when running
     from within a checkout.

4.4. If any first-run bootstrap gap is found under the packaged-install context specifically
     (vs. `uv run`), fix it as a minimal, targeted change — do not re-architect config
     resolution. — DONE: no gap found; no code fix needed.

## 5. Upgrade Path Verification — DONE

5.1. With a tool installed at an older tag, test `uv tool upgrade nwtrack` against a newer
     tag/ref and observe actual behavior (does it re-resolve the git ref, or is it a no-op
     because the source is pinned?). — DONE: confirmed `uv tool upgrade nwtrack` is a
     **no-op** ("Nothing to upgrade") when installed against a fixed tag, since the tag ref
     itself doesn't move. (It *does* re-resolve automatically when installed against a
     branch ref instead of a tag — but the documented install command uses tags, so this
     doesn't apply to the supported path.)

5.2. If `uv tool upgrade` does not correctly move the install forward, determine and test the
     correct command (e.g. `uv tool install --reinstall-package nwtrack git+<repo-url>@<new-tag>`).
     — DONE: confirmed `uv tool install --reinstall-package nwtrack git+<repo-url>@<new-tag>`
     correctly upgrades a tag-pinned install to a new tag/version (verified with two test
     tags in the local repo; test tags and the temporary test commit were removed after
     verification — no trace left in history).

5.3. Document whichever command is verified to work as the supported "Upgrading" instructions
     — do not document an unverified command. — DONE (documented in Group 6, README)

## 6. README Documentation — DONE

6.1. Add a new "Installation" subsection (or restructure the existing one) covering the
     packaged install path: prerequisites (`uv`), the `uv tool install git+...@<tag>`
     command, and a first-run pointer to the existing Configuration section. — DONE

6.2. Keep the existing source-checkout (`uv sync` / `uv run nwtrack`) instructions, framed as
     the option for development or running from a checkout. — DONE, kept as "Running from a
     source checkout (development)"

6.3. Add an "Upgrading" subsection documenting the verified command from Group 5. — DONE,
     documents both the `@main`/branch case (where `uv tool upgrade` does help) and the
     tag-pinned case (where `--reinstall-package` is required)

6.4. Add an "Uninstalling" subsection (`uv tool uninstall nwtrack`), including a note that
     config/data/log files under `platformdirs` locations are left in place and must be
     removed manually if desired. — DONE

6.5. (Added during implementation) Documented the checkout-relative config fallback caveat
     found in Group 4.3 directly in the Configuration section.

## 7. Validation Pass

7.1. Run `ruff`, `mypy`, `pytest` — expect no code changes beyond any Group 4.4 fix, so this
     should be a clean pass confirming nothing broke.

7.2. Manually walk through install → first-run → upgrade → uninstall end-to-end per
     `validation.md`.
