---
name: config-search-order-and-path
status: in-progress
---

## Problem

Reverse the config file search order, and add an optional parameter to set the config path explicitly.

## Notes

- Current search order (first found wins): `user_config_dir("nwtrack")`, `~/.config/nwtrack/`, `./config/nwtrack/`.
- Form of the optional parameter (CLI flag, env var, etc.) not yet decided.
