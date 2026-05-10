"""Rich-output tests for the single-month aggregated balances report."""

import re

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.dto import (
    AggregationDimension,
    OperationResult,
    SingleMonthAggregationResult,
)
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.report_balances_aggregate import (
    SingleMonthAggregatedBalanceReport,
)
from nwtrack.application.use_cases.report_single_month_aggregation import (
    ReportSingleMonthAggregation,
)
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.adapters.report_presenters import (
    RichSingleMonthAggregationReportPresenter,
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
    """Create mixed-currency, institution, and tag data for report output tests."""
    container = base_container
    init_db_tables_w_entities(container, sample_entities)
    month = Month(2025, 11)

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

        uow.balances.insert(Balance(account_id=4, month=month, amount=200))
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
            Balance(account_id=swiss_account_id, month=month, amount=700)
        )

    return container, month


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Configure a container with a recordable Rich console for report output tests."""
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
        ReportSingleMonthAggregation,
        lambda c: ReportSingleMonthAggregation(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        RichSingleMonthAggregationReportPresenter,
        lambda c: RichSingleMonthAggregationReportPresenter(
            fetcher=c.resolve(FetchService),
            console=c.resolve(Console),
        ),
    ).register(
        SingleMonthAggregatedBalanceReport,
        lambda c: SingleMonthAggregatedBalanceReport(
            fetcher=c.resolve(FetchService),
            aggregation_report=c.resolve(ReportSingleMonthAggregation),
            presenter=c.resolve(RichSingleMonthAggregationReportPresenter),
        ),
    )
    return container


def test_category_report_renders_grouped_balances_table(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Category aggregation should render a grouped balances table."""
    container, month = _setup_reporting_fixture(configured_container, sample_entities)

    result = container.resolve(SingleMonthAggregatedBalanceReport).run(
        month=month,
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
        allow_interactive=False,
    )
    output = container.resolve(Console).export_text()

    assert result.success
    assert "Grouped Balance Report" in output
    assert re.search(r"Grouped Balances\s+2025-11 by\s+category \(USD\)", output)
    assert "Category" in output
    assert "Amount" in output
    assert "checking" in output
    assert "revolving_credit" in output
    assert "savings" in output
    assert "200" in output
    assert "500" in output
    assert "600" in output


def test_currency_report_renders_one_currency_column(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Currency aggregation should not imply one report currency."""
    container, month = _setup_reporting_fixture(configured_container, sample_entities)

    result = container.resolve(SingleMonthAggregatedBalanceReport).run(
        month=month,
        dimension=AggregationDimension.CURRENCY,
        allow_interactive=False,
    )
    output = container.resolve(Console).export_text()

    assert result.success
    assert re.search(r"Grouped Balances\s+2025-11 by currency", output)
    assert "(USD)" not in output
    assert "Currency" in output
    assert "Amount" in output
    assert "CHF" in output
    assert "USD" in output
    assert "700" in output
    assert "1,300" in output


def test_institution_and_tag_reports_preserve_special_group_labels(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Institution and tag group labels should render unchanged."""
    container, month = _setup_reporting_fixture(configured_container, sample_entities)
    workflow = container.resolve(SingleMonthAggregatedBalanceReport)

    institution_result = workflow.run(
        month=month,
        dimension=AggregationDimension.INSTITUTION,
        currency_code="USD",
        allow_interactive=False,
    )
    tag_result = workflow.run(
        month=month,
        dimension=AggregationDimension.TAG,
        currency_code="USD",
        allow_interactive=False,
    )
    output = container.resolve(Console).export_text()

    assert institution_result.success
    assert tag_result.success
    assert "Unassigned" in output
    assert "Untagged" in output


def test_empty_results_show_no_data_message_without_rendering_table(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Empty valid requests should show no-data feedback instead of an empty table."""
    container = configured_container
    init_db_tables_w_entities(container, sample_entities)

    result: OperationResult[SingleMonthAggregationResult] = container.resolve(
        SingleMonthAggregatedBalanceReport
    ).run(
        month=Month(2030, 1),
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
        allow_interactive=False,
    )
    output: str = container.resolve(Console).export_text()

    assert result.success
    assert "No grouped balances found for 2030-01 by category in USD." in output
    assert "Grouped Balances 2030-01 by category (USD)" not in output
