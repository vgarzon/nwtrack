"""Rich-output tests for the history aggregated balances report."""

import re

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.dto import (
    AggregationDimension,
    HistoryAggregationResult,
    OperationResult,
)
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.report_balances_aggregate_history import (
    HistoryAggregatedBalanceReport,
)
from nwtrack.application.use_cases.report_history_aggregation import (
    ReportHistoryAggregation,
)
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.adapters.report_presenters import (
    RichHistoryAggregationReportPresenter,
)
from nwtrack.entrypoints.cli.ui.factory import Console, ConsoleFactory, ConsoleSettings
from nwtrack.infra.persistence.orm.models import (
    Account,
    Balance,
    Institution,
    Status,
    Tag,
)


def _setup_reporting_fixture(base_container, sample_entities):
    """Create mixed-currency, institution, and tag data for history report tests."""
    container = base_container
    init_db_tables_w_entities(container, sample_entities)
    start_month = Month(2026, 1)
    end_month = Month(2026, 2)

    with container.resolve(UnitOfWork) as uow:
        chase_id = uow.institutions.insert(
            Institution(name="Chase", description="Primary bank")
        )
        fidelity_id = uow.institutions.insert(
            Institution(name="Fidelity", description="Brokerage")
        )
        liquid_id = uow.tags.insert(Tag(name="liquid", description="Quick access"))
        core_id = uow.tags.insert(Tag(name="core", description="Core holding"))

        checking = uow.accounts.get_by_id(1)
        savings = uow.accounts.get_by_id(2)
        credit_card = uow.accounts.get_by_id(3)
        assert checking is not None
        assert savings is not None
        assert credit_card is not None

        checking.institution_id = chase_id
        savings.institution_id = fidelity_id
        credit_card.institution_id = None
        uow.tags.replace_for_account(checking.id, [liquid_id])
        uow.tags.replace_for_account(savings.id, [liquid_id, core_id])
        uow.tags.replace_for_account(credit_card.id, [])

        swiss_account_id = uow.accounts.insert(
            Account(
                name="swiss_cash",
                description="Swiss cash",
                category_name="checking",
                currency_code="CHF",
                status=Status.ACTIVE,
            )
        )

        uow.balances.insert(Balance(account_id=1, month=start_month, amount=150))
        uow.balances.insert(Balance(account_id=2, month=start_month, amount=450))
        uow.balances.insert(Balance(account_id=3, month=start_month, amount=550))
        uow.balances.insert(
            Balance(account_id=swiss_account_id, month=start_month, amount=650)
        )
        uow.balances.insert(Balance(account_id=1, month=end_month, amount=200))
        uow.balances.insert(Balance(account_id=2, month=end_month, amount=500))
        uow.balances.insert(Balance(account_id=3, month=end_month, amount=600))
        uow.balances.insert(Balance(account_id=4, month=end_month, amount=200))
        uow.balances.insert(
            Balance(account_id=swiss_account_id, month=end_month, amount=700)
        )

    return container, start_month, end_month


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Configure a container with a recordable Rich console for history report tests."""
    from nwtrack.bootstrap.composition import build_data_services_container

    container = build_data_services_container(base_container)
    console_defaults = ConsoleSettings(record=True)
    container.register(
        Console,
        lambda _: ConsoleFactory(default_settings=console_defaults)(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ReportHistoryAggregation,
        lambda c: ReportHistoryAggregation(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        RichHistoryAggregationReportPresenter,
        lambda c: RichHistoryAggregationReportPresenter(
            fetcher=c.resolve(FetchService),
            console=c.resolve(Console),
        ),
    ).register(
        HistoryAggregatedBalanceReport,
        lambda c: HistoryAggregatedBalanceReport(
            fetcher=c.resolve(FetchService),
            aggregation_report=c.resolve(ReportHistoryAggregation),
            presenter=c.resolve(RichHistoryAggregationReportPresenter),
        ),
    )
    return container


def test_category_history_report_renders_grouped_balances_table(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Category history aggregation should render a grouped history table."""
    container, start_month, end_month = _setup_reporting_fixture(
        configured_container,
        sample_entities,
    )

    result = container.resolve(HistoryAggregatedBalanceReport).run(
        start_month=start_month,
        end_month=end_month,
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
        allow_interactive=False,
    )
    output = container.resolve(Console).export_text()

    assert result.success
    assert "Grouped History Balance Report" in output
    assert re.search(
        r"Grouped Balances\s+2026-01 to\s+2026-02 by\s+category \(USD\)",
        output,
    )
    assert "Month" in output
    assert "Category" in output
    assert "Amount" in output
    assert "2026-01" in output
    assert "2026-02" in output
    assert "checking" in output
    assert "revolving_credit" in output
    assert "savings" in output


def test_currency_history_report_renders_month_and_currency_columns(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Currency history aggregation should not imply one report currency."""
    container, start_month, end_month = _setup_reporting_fixture(
        configured_container,
        sample_entities,
    )

    result = container.resolve(HistoryAggregatedBalanceReport).run(
        start_month=start_month,
        end_month=end_month,
        dimension=AggregationDimension.CURRENCY,
        allow_interactive=False,
    )
    output = container.resolve(Console).export_text()

    assert result.success
    assert re.search(r"Grouped Balances\s+2026-01 to\s+2026-02 by currency", output)
    assert "(USD)" not in output
    assert "Month" in output
    assert "Currency" in output
    assert "Amount" in output
    assert "CHF" in output
    assert "USD" in output


def test_history_reports_preserve_special_group_labels(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Institution and tag history labels should render unchanged."""
    container, start_month, end_month = _setup_reporting_fixture(
        configured_container,
        sample_entities,
    )
    workflow = container.resolve(HistoryAggregatedBalanceReport)

    institution_result = workflow.run(
        start_month=start_month,
        end_month=end_month,
        dimension=AggregationDimension.INSTITUTION,
        currency_code="USD",
        allow_interactive=False,
    )
    tag_result = workflow.run(
        start_month=start_month,
        end_month=end_month,
        dimension=AggregationDimension.TAG,
        currency_code="USD",
        allow_interactive=False,
    )
    output = container.resolve(Console).export_text()

    assert institution_result.success
    assert tag_result.success
    assert "Unassigned" in output
    assert "Untagged" in output


def test_empty_history_results_show_no_data_message_without_rendering_table(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Empty valid history requests should show no-data feedback instead of a table."""
    container = configured_container
    init_db_tables_w_entities(container, sample_entities)

    result: OperationResult[HistoryAggregationResult] = container.resolve(
        HistoryAggregatedBalanceReport
    ).run(
        start_month=Month(2030, 1),
        end_month=Month(2030, 3),
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
        allow_interactive=False,
    )
    output: str = container.resolve(Console).export_text()

    assert result.success
    assert (
        "No grouped balances found from 2030-01 to 2030-03 by category in USD."
        in output
    )
    assert "Grouped Balances 2030-01 to 2030-03 by category (USD)" not in output
