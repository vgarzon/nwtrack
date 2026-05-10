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
from nwtrack.domain.models import Account, Balance, Status
from nwtrack.domain.value_objects import Month


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Configure container."""
    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.data_loader import InitDataService
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.use_cases.report_balances_by_category import (
        FetchService,
    )
    from nwtrack.application.use_cases.report_single_month_aggregation import (
        ReportSingleMonthAggregation,
    )
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.entrypoints.cli.adapters.report_presenters import (
        Console,
        RichBalancesByCategoryPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings
    from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory
    from nwtrack.infra.config.settings import Settings
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

    console_default = ConsoleSettings(record=True)

    return (
        base_container.register(
            SchemaManager,
            lambda c: SchemaManagerImpl(engine=c.resolve(SQLiteSessionManager).engine),
        )
        .register(
            DBAdminService,
            lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
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
            ReportSingleMonthAggregation,
            lambda c: ReportSingleMonthAggregation(uow=lambda: c.resolve(UnitOfWork)),
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
                aggregation_report=c.resolve(ReportSingleMonthAggregation),
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


def test_print_summary_mixed_currency_month_fails_clearly(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Mixed-currency compatibility reporting should fail before grouped totals."""
    import nwtrack.entrypoints.cli.adapters.report_presenters as report_presenters
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.entrypoints.cli.adapters.report_presenters import Console

    init_db_tables_w_entities(configured_container, sample_entities)

    with configured_container.resolve(UnitOfWork) as uow:
        swiss_account_id = uow.accounts.insert(
            Account(
                name="swiss_cash",
                description="Swiss cash",
                category_name="checking",
                currency_code="CHF",
                status=Status.ACTIVE,
            )
        )
        uow.balances.insert(
            Balance(
                account_id=swiss_account_id,
                month=Month(2025, 11),
                amount=700,
            )
        )

    monkeypatch.setattr(
        report_presenters.RichBalancesByCategoryPresenter,
        "prompt_for_month_choice",
        lambda *args, **kwargs: Month(2025, 11),
    )

    result: OperationResult = configured_container.resolve(
        ReportBalancesByCategory
    ).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    assert not result.success
    assert (
        "Mixed-currency compatibility reporting is not supported yet."
        in captured_output
    )
    assert "Summary by Category 2025-11" not in captured_output
    assert "Net Worth Summary 2025-11 (USD)" not in captured_output
    assert re.search(
        r"conversion-based\s+consolidated reporting is not available yet",
        captured_output.lower(),
    )


def test_print_summary_no_month_selected_preserves_existing_feedback(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Cancelling month selection should still exit with the legacy warning."""
    import nwtrack.entrypoints.cli.adapters.report_presenters as report_presenters
    from nwtrack.entrypoints.cli.adapters.report_presenters import Console

    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        report_presenters.RichBalancesByCategoryPresenter,
        "prompt_for_month_choice",
        lambda *args, **kwargs: None,
    )

    result: OperationResult = configured_container.resolve(
        ReportBalancesByCategory
    ).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    assert not result.success
    assert "No month selected. Exiting report." in captured_output
