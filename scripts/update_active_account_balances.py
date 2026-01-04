"""
Update active account balances interactively
"""

from nwtrack.compose import build_base_sqlite_uow_container
from nwtrack.use_cases.balance_updater import BalanceUpdater
from nwtrack.unitofwork import UnitOfWork


def main() -> None:
    container = build_base_sqlite_uow_container()
    container.register(
        BalanceUpdater,
        lambda c: BalanceUpdater(uow=lambda: c.resolve(UnitOfWork)),
    )
    updater: BalanceUpdater = container.resolve(BalanceUpdater)
    updater.run()


if __name__ == "__main__":
    main()
