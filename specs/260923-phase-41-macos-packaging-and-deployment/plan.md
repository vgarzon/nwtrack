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

## 4. Install Path Verification

4.1. In a throwaway environment (e.g. a temp dir or a scratch venv, not the dev checkout),
     run `uv tool install git+<repo-url>@<test-tag-or-branch>` and confirm `nwtrack` resolves
     on `PATH`.

4.2. Confirm `nwtrack --help` and `nwtrack tui launch` both work from the installed tool.

4.3. Confirm first-run directory bootstrap: with no existing config/data/log directories,
     run a command that touches the database (e.g. `nwtrack accounts list`) and confirm the
     `platformdirs`-resolved data/log directories are created automatically, matching Phase
     40 behavior under `uv run`.

4.4. If any first-run bootstrap gap is found under the packaged-install context specifically
     (vs. `uv run`), fix it as a minimal, targeted change — do not re-architect config
     resolution.

## 5. Upgrade Path Verification

5.1. With a tool installed at an older tag, test `uv tool upgrade nwtrack` against a newer
     tag/ref and observe actual behavior (does it re-resolve the git ref, or is it a no-op
     because the source is pinned?).

5.2. If `uv tool upgrade` does not correctly move the install forward, determine and test the
     correct command (e.g. `uv tool install --reinstall-package nwtrack git+<repo-url>@<new-tag>`).

5.3. Document whichever command is verified to work as the supported "Upgrading" instructions
     — do not document an unverified command.

## 6. README Documentation

6.1. Add a new "Installation" subsection (or restructure the existing one) covering the
     packaged install path: prerequisites (`uv`), the `uv tool install git+...@<tag>`
     command, and a first-run pointer to the existing Configuration section.

6.2. Keep the existing source-checkout (`uv sync` / `uv run nwtrack`) instructions, framed as
     the option for development or running from a checkout.

6.3. Add an "Upgrading" subsection documenting the verified command from Group 5.

6.4. Add an "Uninstalling" subsection (`uv tool uninstall nwtrack`), including a note that
     config/data/log files under `platformdirs` locations are left in place and must be
     removed manually if desired.

## 7. Validation Pass

7.1. Run `ruff`, `mypy`, `pytest` — expect no code changes beyond any Group 4.4 fix, so this
     should be a clean pass confirming nothing broke.

7.2. Manually walk through install → first-run → upgrade → uninstall end-to-end per
     `validation.md`.
