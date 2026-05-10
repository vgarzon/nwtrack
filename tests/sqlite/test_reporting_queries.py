"""Tests for shared reporting queries."""

from tests.helpers import _uow_factory, init_db_tables_w_entities

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    HistoryAggregationRequest,
    MonthlyCategoryBalance,
    SingleMonthAggregationRequest,
)
from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.domain.value_objects import Month
from nwtrack.infra.persistence.orm.models import (
    Account,
    Balance,
    Institution,
    Status,
    Tag,
)


def _setup_reporting_fixture(base_container, sample_entities):
    """Create a reporting fixture with mixed currency, institutions, and tags."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)
    month = Month(2025, 11)

    with _uow_factory(container) as uow:
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

        uow.balances.insert(
            Balance(
                account_id=4,
                month=month,
                amount=200,
            )
        )
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
                month=month,
                amount=700,
            )
        )

    return container, month


def _setup_history_reporting_fixture(base_container, sample_entities):
    """Create a reporting fixture with a dedicated two-month history range."""
    container, _ = _setup_reporting_fixture(base_container, sample_entities)
    start_month = Month(2026, 1)
    end_month = Month(2026, 2)

    with _uow_factory(container) as uow:
        swiss_account = next(
            account for account in uow.accounts.get_all() if account.name == "swiss_cash"
        )
        uow.balances.insert(Balance(account_id=1, month=start_month, amount=150))
        uow.balances.insert(Balance(account_id=2, month=start_month, amount=450))
        uow.balances.insert(Balance(account_id=3, month=start_month, amount=550))
        uow.balances.insert(
            Balance(account_id=swiss_account.id, month=start_month, amount=650)
        )
        uow.balances.insert(Balance(account_id=1, month=end_month, amount=200))
        uow.balances.insert(Balance(account_id=2, month=end_month, amount=500))
        uow.balances.insert(Balance(account_id=3, month=end_month, amount=600))
        uow.balances.insert(
            Balance(account_id=4, month=end_month, amount=200)
        )
        uow.balances.insert(
            Balance(account_id=swiss_account.id, month=end_month, amount=700)
        )

    return container, start_month, end_month


def test_get_monthly_total_by_category(base_container, sample_entities) -> None:
    """Compatibility category query should still return category DTO rows."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)
    month = Month(2025, 11)

    with _uow_factory(container) as uow:
        rows = uow._reporting.monthly_balance_total_by_category(month)

    checking = next((row for row in rows if row.category.name == "checking"), None)
    assert checking is not None
    assert isinstance(checking, MonthlyCategoryBalance)
    assert checking.month == month
    assert checking.amount == 200


def test_get_month_currencies_honors_status_scope(
    base_container, sample_entities
) -> None:
    """Distinct month currencies should respect the requested status scope."""
    container, month = _setup_reporting_fixture(base_container, sample_entities)

    with _uow_factory(container) as uow:
        active_currencies = uow._reporting.get_month_currencies(
            month, AccountStatusScope.ACTIVE
        )
        all_currencies = uow._reporting.get_month_currencies(
            month, AccountStatusScope.ALL
        )

    assert active_currencies == ["CHF", "USD"]
    assert all_currencies == ["CHF", "USD"]


def test_get_range_currencies_honors_status_scope(base_container, sample_entities) -> None:
    """Distinct range currencies should respect the requested status scope."""
    container, start_month, end_month = _setup_history_reporting_fixture(
        base_container,
        sample_entities,
    )

    with _uow_factory(container) as uow:
        active_currencies = uow._reporting.get_range_currencies(
            start_month,
            end_month,
            AccountStatusScope.ACTIVE,
        )
        all_currencies = uow._reporting.get_range_currencies(
            start_month,
            end_month,
            AccountStatusScope.ALL,
        )

    assert active_currencies == ["CHF", "USD"]
    assert all_currencies == ["CHF", "USD"]


def test_aggregate_single_month_by_category(base_container, sample_entities) -> None:
    """Category aggregation should filter by currency and return sorted groups."""
    container, month = _setup_reporting_fixture(base_container, sample_entities)

    with _uow_factory(container) as uow:
        result = uow._reporting.aggregate_single_month(
            SingleMonthAggregationRequest(
                month=month,
                dimension=AggregationDimension.CATEGORY,
                currency_code="USD",
            )
        )

    assert result.currency_code == "USD"
    assert [(group.label, group.amount) for group in result.groups] == [
        ("checking", 200),
        ("revolving_credit", 600),
        ("savings", 500),
    ]


def test_aggregate_single_month_by_side_orders_asset_before_liability(
    base_container, sample_entities
) -> None:
    """Side aggregation should keep accounting order and support inactive inclusion."""
    container, month = _setup_reporting_fixture(base_container, sample_entities)

    with _uow_factory(container) as uow:
        result = uow._reporting.aggregate_single_month(
            SingleMonthAggregationRequest(
                month=month,
                dimension=AggregationDimension.SIDE,
                currency_code="USD",
                status_scope=AccountStatusScope.ALL,
            )
        )

    assert [(group.label, group.amount) for group in result.groups] == [
        ("asset", 700),
        ("liability", 800),
    ]


def test_aggregate_single_month_by_institution_includes_unassigned_bucket(
    base_container, sample_entities
) -> None:
    """Institution aggregation should keep accounts without an institution."""
    container, month = _setup_reporting_fixture(base_container, sample_entities)

    with _uow_factory(container) as uow:
        result = uow._reporting.aggregate_single_month(
            SingleMonthAggregationRequest(
                month=month,
                dimension=AggregationDimension.INSTITUTION,
                currency_code="USD",
            )
        )

    assert [(group.label, group.amount) for group in result.groups] == [
        ("Chase", 200),
        ("Fidelity", 500),
        ("Unassigned", 600),
    ]


def test_aggregate_single_month_by_currency(base_container, sample_entities) -> None:
    """Currency aggregation should keep currencies separate."""
    container, month = _setup_reporting_fixture(base_container, sample_entities)

    with _uow_factory(container) as uow:
        result = uow._reporting.aggregate_single_month(
            SingleMonthAggregationRequest(
                month=month,
                dimension=AggregationDimension.CURRENCY,
            )
        )

    assert result.currency_code is None
    assert [(group.label, group.amount) for group in result.groups] == [
        ("CHF", 700),
        ("USD", 1300),
    ]


def test_aggregate_single_month_by_tag_includes_untagged_and_duplicates_multi_tag_amount(  # noqa: E501
    base_container,
    sample_entities,
) -> None:
    """Tag aggregation should duplicate multi-tag balances and include untagged."""
    container, month = _setup_reporting_fixture(base_container, sample_entities)

    with _uow_factory(container) as uow:
        result = uow._reporting.aggregate_single_month(
            SingleMonthAggregationRequest(
                month=month,
                dimension=AggregationDimension.TAG,
                currency_code="USD",
            )
        )

    assert [(group.label, group.amount) for group in result.groups] == [
        ("core", 500),
        ("liquid", 700),
        ("Untagged", 600),
    ]


def test_aggregate_history_by_category(base_container, sample_entities) -> None:
    """Category history aggregation should return ordered rows across the range."""
    container, start_month, end_month = _setup_history_reporting_fixture(
        base_container,
        sample_entities,
    )

    with _uow_factory(container) as uow:
        result = uow._reporting.aggregate_history(
            HistoryAggregationRequest(
                start_month=start_month,
                end_month=end_month,
                dimension=AggregationDimension.CATEGORY,
                currency_code="USD",
            )
        )

    assert result.currency_code == "USD"
    assert [(row.month, row.label, row.amount) for row in result.rows] == [
        (start_month, "checking", 150),
        (start_month, "revolving_credit", 550),
        (start_month, "savings", 450),
        (end_month, "checking", 200),
        (end_month, "revolving_credit", 600),
        (end_month, "savings", 500),
    ]


def test_aggregate_history_by_side_orders_asset_before_liability_within_month(
    base_container,
    sample_entities,
) -> None:
    """Side history aggregation should keep accounting order within each month."""
    container, start_month, end_month = _setup_history_reporting_fixture(
        base_container,
        sample_entities,
    )

    with _uow_factory(container) as uow:
        result = uow._reporting.aggregate_history(
            HistoryAggregationRequest(
                start_month=start_month,
                end_month=end_month,
                dimension=AggregationDimension.SIDE,
                currency_code="USD",
                status_scope=AccountStatusScope.ALL,
            )
        )

    assert [(row.month, row.label, row.amount) for row in result.rows] == [
        (start_month, "asset", 600),
        (start_month, "liability", 550),
        (end_month, "asset", 700),
        (end_month, "liability", 800),
    ]


def test_aggregate_history_by_institution_includes_unassigned_bucket(
    base_container,
    sample_entities,
) -> None:
    """Institution history aggregation should retain the unassigned bucket per month."""
    container, start_month, end_month = _setup_history_reporting_fixture(
        base_container,
        sample_entities,
    )

    with _uow_factory(container) as uow:
        result = uow._reporting.aggregate_history(
            HistoryAggregationRequest(
                start_month=start_month,
                end_month=end_month,
                dimension=AggregationDimension.INSTITUTION,
                currency_code="USD",
            )
        )

    assert [(row.month, row.label, row.amount) for row in result.rows] == [
        (start_month, "Chase", 150),
        (start_month, "Fidelity", 450),
        (start_month, "Unassigned", 550),
        (end_month, "Chase", 200),
        (end_month, "Fidelity", 500),
        (end_month, "Unassigned", 600),
    ]


def test_aggregate_history_by_currency(base_container, sample_entities) -> None:
    """Currency history aggregation should keep month and currency totals distinct."""
    container, start_month, end_month = _setup_history_reporting_fixture(
        base_container,
        sample_entities,
    )

    with _uow_factory(container) as uow:
        result = uow._reporting.aggregate_history(
            HistoryAggregationRequest(
                start_month=start_month,
                end_month=end_month,
                dimension=AggregationDimension.CURRENCY,
            )
        )

    assert result.currency_code is None
    assert [(row.month, row.label, row.amount) for row in result.rows] == [
        (start_month, "CHF", 650),
        (start_month, "USD", 1150),
        (end_month, "CHF", 700),
        (end_month, "USD", 1300),
    ]


def test_aggregate_history_by_tag_includes_untagged_and_duplicates_multi_tag_amount(
    base_container,
    sample_entities,
) -> None:
    """Tag history aggregation should retain untagged rows and duplicate multi-tag balances."""  # noqa: E501
    container, start_month, end_month = _setup_history_reporting_fixture(
        base_container,
        sample_entities,
    )

    with _uow_factory(container) as uow:
        result = uow._reporting.aggregate_history(
            HistoryAggregationRequest(
                start_month=start_month,
                end_month=end_month,
                dimension=AggregationDimension.TAG,
                currency_code="USD",
            )
        )

    assert [(row.month, row.label, row.amount) for row in result.rows] == [
        (start_month, "core", 450),
        (start_month, "liquid", 600),
        (start_month, "Untagged", 550),
        (end_month, "core", 500),
        (end_month, "liquid", 700),
        (end_month, "Untagged", 600),
    ]


def test_aggregate_single_month_empty_result(base_container, sample_entities) -> None:
    """Valid requests with no matching balances should return an empty group list."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        result = uow._reporting.aggregate_single_month(
            SingleMonthAggregationRequest(
                month=Month(2030, 1),
                dimension=AggregationDimension.CATEGORY,
                currency_code="USD",
            )
        )

    assert result.groups == []


def test_aggregate_history_empty_result(base_container, sample_entities) -> None:
    """Valid history requests with no matching balances should return an empty row list."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        result = uow._reporting.aggregate_history(
            HistoryAggregationRequest(
                start_month=Month(2030, 1),
                end_month=Month(2030, 3),
                dimension=AggregationDimension.CATEGORY,
                currency_code="USD",
            )
        )

    assert result.rows == []
