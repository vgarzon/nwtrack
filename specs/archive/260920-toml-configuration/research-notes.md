# Research Notes: Config Management on macOS

Source: user-provided research, used as a starting point (not a final design — see
`requirements.md` for the decisions actually adopted for this phase).

## Data, config, and cache locations

Don't hand-roll `~/.mytool/`. Use the `platformdirs` library — it computes the correct
OS-specific paths for you:

```python
from platformdirs import user_config_dir, user_data_dir, user_cache_dir, user_log_dir

CONFIG_DIR = user_config_dir("mytool")   # ~/Library/Application Support/mytool
DATA_DIR   = user_data_dir("mytool")     # ~/Library/Application Support/mytool
CACHE_DIR  = user_cache_dir("mytool")    # ~/Library/Caches/mytool
LOG_DIR    = user_log_dir("mytool")      # ~/Library/Logs/mytool
```

On macOS, native convention puts config and data both under
`~/Library/Application Support/<AppName>/`, separate from `~/Library/Caches/` (disposable,
safe to delete) and `~/Library/Logs/`. This matters because:

- Time Machine and cleanup tools treat `Caches/` as expendable — don't put anything there
  you'd be upset to lose.
- `Application Support/` is backed up and persistent — that's where config and real data
  belong.

If you have a personal preference for Unix-y dotfiles instead (some CLI tool authors target
`~/.config/mytool/` even on macOS, following XDG conventions since many CLI users are used
to that from Linux), `platformdirs` also supports forcing XDG paths — just be consistent and
document it.

## Config file itself

- **Format**: TOML is the best fit for CLI config in the Python ecosystem —
  human-editable, unambiguous types, and `tomllib` is in the standard library since
  Python 3.11 (use `tomli` as a backport if you support older versions).
- **Validation**: Use `pydantic` (or `attrs` + `cattrs`) to define a schema and
  validate/parse the config on load, rather than trusting raw dicts. This catches typos and
  gives you good error messages.
- **Defaults + first-run**: On first run, if no config exists, write out a default config
  file rather than silently using in-memory defaults — it gives the user something to
  discover and edit.
- **Schema versioning**: Include a `version` key in the config file from day one. Even for
  personal tools, you'll thank yourself later when you change a field name and need to
  migrate old configs automatically instead of getting a cryptic crash.

## What this phase adopted vs. deferred

- `platformdirs` for path resolution: **adopted**.
- TOML format via stdlib `tomllib`: **adopted**.
- `pydantic` validation: **deferred** — stays dataclass-only, consistent with the existing
  `Settings` dataclass and `specs/tech-stack.md`'s "keep local workflows fast and
  dependency-light" standard. No new validation dependency in this phase.
- Auto-write default config on first run: **adopted, but explicit** — first run without a
  config.toml falls back to in-code defaults and prints/logs guidance rather than writing a
  file implicitly; a file is only written via the new `nwtrack config init` command.
- `version` schema key: **deferred** — can be added later if a breaking schema change
  actually happens.
- `cache_dir`: **deferred** — nothing in nwtrack uses a cache today; not wired up until a
  feature needs it.
