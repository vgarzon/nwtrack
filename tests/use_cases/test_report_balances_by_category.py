"""
Test print summary use case
"""

import re

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import BalancesByCategoryPresenter
from nwtrack.application.use_cases.report_balances_by_category import (
    ReportBalancesByCategory,
)
from nwtrack.bootstrap.container import Container
from nwtrack.domain.value_objects import Month


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Configure container."""
    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.data_loader import InitDataService
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.use_cases.report_balances_by_category import (
        FetchService,
    )
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.entrypoints.cli.adapters.report_presenters import (
        Console,
        RichBalancesByCategoryPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings
    from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory
    from nwtrack.infra.config.settings import Settings

    console_default = ConsoleSettings(record=True)

    return (
        base_container.register(
            DBAdminService,
            lambda c: DBAdminService(
                c.resolve(Settings), c.resolve(DBConnectionManager)
            ),
        )
        .register(
            InitDataService,
            lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            Console,
            lambda _: ConsoleFactory(default_settings=console_default)(),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            BalancesByCategoryPresenter,
            lambda c: RichBalancesByCategoryPresenter(
                fetcher=c.resolve(FetchService),
                console=c.resolve(Console),
            ),
        )
        .register(
            ReportBalancesByCategory,
            lambda c: ReportBalancesByCategory(
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(BalancesByCategoryPresenter),
            ),
        )
    )


def test_print_summary_run_default_month(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Test print summary service."""
    import nwtrack.entrypoints.cli.adapters.report_presenters as report_presenters
    from nwtrack.entrypoints.cli.adapters.report_presenters import Console

    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        report_presenters.RichBalancesByCategoryPresenter,
        "prompt_for_month_choice",
        lambda *args, **kwargs: Month(2025, 11),
    )
    result: OperationResult = configured_container.resolve(
        ReportBalancesByCategory
    ).run()
    captured_output: str = configured_container.resolve(Console).export_text()
    assert result.success
    assert re.search(r"Balances 2025-11", captured_output)
    assert re.search(r"Balances 2025-11", captured_output)
    assert re.search(r"credit_cards_1.+revolving_credit.+600", captured_output)
    assert re.search(r"700.+600.+100", captured_output)
