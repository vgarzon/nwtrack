"""
Entry point for nwtrack cli application.
"""

import sys

from nwtrack.entrypoints.cli.app import app


def main():
    try:
        app()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
