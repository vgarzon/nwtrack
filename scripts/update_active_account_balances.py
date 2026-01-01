"""
Update active account balances interactively
"""

from nwtrack.compose import build_sqlite_uow_container
from nwtrack.use_cases import BalanceUpdater


def main() -> None:
    container = build_sqlite_uow_container()
    updater = BalanceUpdater(container)
    updater.run()


if __name__ == "__main__":
    main()
