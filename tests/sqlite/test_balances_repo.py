"""
Test suite for Balances repository operations
"""

from tests.helpers import _uow_factory, init_db_tables_w_entities

from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.domain.models import AccountStatusHistory, Status
from nwtrack.domain.value_objects import Month

# TODO: add tests for other balance repo methods


def test_insert_single_balance(base_container, sample_entities) -> None:
    """Test inserting a single balance entry."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)
    account_id = 1
    month_str = "2025-12"
    month = Month.parse(month_str)
    new_balance_data = {
        "id": 0,  # will be set by the database
        "account_id": account_id,
        "month": month_str,
        "amount": 300,
    }
    with _uow_factory(container) as uow:
        new_balance = uow.balances.hydrate(new_balance_data)
        last_id = uow.balances.insert(new_balance)
        inserted_balance = uow.balances.get_by_account_id(
            month=month, account_id=account_id
        )
    assert last_id == 43
    assert inserted_balance is not None
    assert inserted_balance.account_id == new_balance_data["account_id"]
    assert str(inserted_balance.month) == new_balance_data["month"]
    assert inserted_balance.amount == new_balance_data["amount"]


def test_count_balances_entries(base_container, sample_entities) -> None:
    """Test counting entries in the balances repository."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        cnt = uow.balances.count()

    assert cnt == 42


def test_count_balances_per_month(base_container, sample_entities) -> None:
    """Test counting balances entries per month."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        cnts = uow.balances.count_per_month()

    assert len(cnts) == 12
    earliest = min(cnts, key=lambda x: x[0])
    assert earliest == (Month(2024, 6), 4)
    latest = max(cnts, key=lambda x: x[0])
    assert latest == (Month(2025, 11), 3)


def _latest_month_and_ids(uow) -> tuple[Month, list[int]]:
    latest = max(m for m, _ in uow.balances.count_per_month())
    ids = sorted(
        b.account_id for b in uow.balances.get_month(latest, active_only=False)
    )
    return latest, ids


class TestCopyActiveByMonth:
    def test_copies_all_accounts_without_history(
        self, base_container, sample_entities
    ) -> None:
        container = build_data_services_container(base_container)
        init_db_tables_w_entities(container, sample_entities)

        with _uow_factory(container) as uow:
            latest, ids = _latest_month_and_ids(uow)
            target = latest.increment()
            copied = uow.balances.copy_active_by_month(latest, target)
            copied_ids = sorted(
                b.account_id for b in uow.balances.get_month(target, active_only=False)
            )

        assert copied == len(ids)
        assert copied_ids == ids

    def test_excludes_account_inactive_in_target_month(
        self, base_container, sample_entities
    ) -> None:
        container = build_data_services_container(base_container)
        init_db_tables_w_entities(container, sample_entities)

        with _uow_factory(container) as uow:
            latest, ids = _latest_month_and_ids(uow)
            target = latest.increment()
            closed_id = ids[0]
            uow.account_status_history.insert(
                AccountStatusHistory(
                    account_id=closed_id,
                    status=Status.INACTIVE,
                    effective_month=target,
                )
            )
            copied = uow.balances.copy_active_by_month(latest, target)
            copied_ids = sorted(
                b.account_id for b in uow.balances.get_month(target, active_only=False)
            )

        assert copied == len(ids) - 1
        assert closed_id not in copied_ids

    def test_account_closed_after_target_is_still_copied(
        self, base_container, sample_entities
    ) -> None:
        container = build_data_services_container(base_container)
        init_db_tables_w_entities(container, sample_entities)

        with _uow_factory(container) as uow:
            latest, ids = _latest_month_and_ids(uow)
            target = latest.increment()
            uow.account_status_history.insert(
                AccountStatusHistory(
                    account_id=ids[0],
                    status=Status.INACTIVE,
                    effective_month=target.increment(),
                )
            )
            copied = uow.balances.copy_active_by_month(latest, target)

        assert copied == len(ids)

    def test_does_not_overwrite_existing_target_rows(
        self, base_container, sample_entities
    ) -> None:
        container = build_data_services_container(base_container)
        init_db_tables_w_entities(container, sample_entities)

        with _uow_factory(container) as uow:
            latest, ids = _latest_month_and_ids(uow)
            target = latest.increment()
            existing = uow.balances.hydrate(
                {
                    "id": 0,
                    "account_id": ids[0],
                    "month": str(target),
                    "amount": 12345,
                }
            )
            uow.balances.insert(existing)
            copied = uow.balances.copy_active_by_month(latest, target)
            kept = uow.balances.get_by_account_id(month=target, account_id=ids[0])

        assert copied == len(ids) - 1
        assert kept is not None
        assert kept.amount == 12345
