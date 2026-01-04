"""
Update active account balances interactively
"""

from nwtrack.compose import build_base_sqlite_uow_container
from nwtrack.use_cases.balance_updater import BalanceUpdater
from nwtrack.unitofwork import UnitOfWork
from nwtrack.services import (
    AccountService,
    ReportService,
    UpdateService,
)


def main() -> None:
    container = build_base_sqlite_uow_container()
    container.register(
        UpdateService,
        lambda c: UpdateService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ReportService,
        lambda c: ReportService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        AccountService,
        lambda c: AccountService(uow=lambda: c.resolve(UnitOfWork)),
    )
    updater = BalanceUpdater(container)
    updater.run()


if __name__ == "__main__":
    main()
