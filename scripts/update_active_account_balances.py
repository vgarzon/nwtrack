"""
Update active account balances interactively
"""

from nwtrack.compose import build_base_sqlite_uow_container
from nwtrack.use_cases.balance_updater import BalanceUpdater
from nwtrack.unitofwork import UnitOfWork
from nwtrack.services import ReportService, UpdateService


def main() -> None:
    container = build_base_sqlite_uow_container()
    container.register(
        UpdateService,
        lambda c: UpdateService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ReportService,
        lambda c: ReportService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        BalanceUpdater,
        lambda c: BalanceUpdater(
            uow=lambda: c.resolve(UnitOfWork),
            report_svc=c.resolve(ReportService),
            update_svc=c.resolve(UpdateService),
        ),
    )
    updater = container.resolve(BalanceUpdater)
    updater.run()


if __name__ == "__main__":
    main()
