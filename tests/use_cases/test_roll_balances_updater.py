"""
Test suite for the roll balances forward use case
"""

import re

import pytest
from tests.helpers import init_db_tables_w_entities

# import nwtrack.application.use_cases.roll_balances_forward
from nwtrack.application.use_cases.roll_balances_forward import RollBalancesUpdater
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.ui.factory import Console


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.presentation import BalancesRollForwardPresenter
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.data_loader import InitDataService
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.services.fetch import FetchService
    from nwtrack.entrypoints.cli.adapters.balance_presenters import (
        RichBalancesRollForwardPresenter,
    )
    from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory, ConsoleSettings
    from nwtrack.infra.config.settings import Settings
    from nwtrack.infra.sqlite.sqlalchemy_manager import SQLAlchemySessionManager

    console_default = ConsoleSettings(record=True)

    return (
        base_container.register(
            DBAdminService,
            lambda c: DBAdminService(
                c.resolve(Settings), c.resolve(SQLAlchemySessionManager)
            ),
        )
        .register(
            InitDataService,
            lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            Console,
            lambda _: ConsoleFactory(console_default)(),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            BalancesRollForwardPresenter,
            lambda c: RichBalancesRollForwardPresenter(
                console=c.resolve(Console),
            ),
        )
        .register(
            RollBalancesUpdater,
            lambda c: RollBalancesUpdater(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(BalancesRollForwardPresenter),
            ),
        )
    )


def test_roll_balances_run_defaults(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
    capsys,
) -> None:
    """Test initializing database and loading sample data."""
    import nwtrack.entrypoints.cli.adapters.balance_presenters as balance_presenters

    # TODO: Use common fixture to init DB with entities
    init_db_tables_w_entities(configured_container, sample_entities)
    monkeypatch.setattr(
        balance_presenters.RichBalancesRollForwardPresenter,
        "confirm_target_month",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalancesRollForwardPresenter,
        "select_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        balance_presenters.RichBalancesRollForwardPresenter,
        "prompt_to_confirm_months",
        lambda *args, **kwargs: True,
    )
    configured_container.resolve(RollBalancesUpdater).run()
    captured_out: str = configured_container.resolve(Console).export_text()
    # TODO: mock prompts in presenter to capture more output
    # TODO: check roll forward results in DB
    assert re.search(r"Copied 3 balance entries.", captured_out)
    assert re.search(r"Net Worth Summary 2025-12", captured_out)
    assert re.search(r"700.+600.+100", captured_out)
