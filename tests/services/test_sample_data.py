"""Tests for the sample dataset and its load path."""

import pytest

from nwtrack.application.ports.schema import SchemaManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.sample_data import (
    N_MONTHS,
    build_sample_records,
    sample_months,
)
from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.bootstrap.container import Container
from nwtrack.domain.value_objects import Month

TODAY = Month(2026, 10)


def test_sample_months_are_consecutive_and_end_today() -> None:
    months = sample_months(TODAY)
    assert len(months) == N_MONTHS
    assert months[-1] == TODAY
    assert months[0] == Month(2025, 11)
    for earlier, later in zip(months, months[1:], strict=False):
        assert earlier.increment() == later


def test_dataset_shape() -> None:
    records = build_sample_records(TODAY)
    assert {r["code"] for r in records["currencies"]} == {"USD", "CHF"}
    assert 2 <= len(records["institutions"]) <= 3
    assert 2 <= len(records["tags"]) <= 3
    assert 6 <= len(records["accounts"]) <= 8
    sides = {r["side"] for r in records["categories"]}
    assert sides == {"asset", "liability"}
    assert all(a["institution_id"] for a in records["accounts"])
    assert any(a["status"] == "inactive" for a in records["accounts"])
    assert records["account_tags"]
    category_names = {c["name"] for c in records["categories"]}
    assert all(a["category"] in category_names for a in records["accounts"])
    assert all(
        isinstance(b["amount"], int) and b["amount"] > 0 for b in records["balances"]
    )
    months = {b["month"] for b in records["balances"]}
    assert months == {str(m) for m in sample_months(TODAY)}


def test_inactive_account_has_matching_status_history() -> None:
    records = build_sample_records(TODAY)
    inactive_ids = {a["id"] for a in records["accounts"] if a["status"] == "inactive"}
    history = [
        h for h in records["account_status_history"] if h["account_id"] in inactive_ids
    ]
    assert {h["status"] for h in history} == {"active", "inactive"}
    last_inactive = max(
        h["effective_month"] for h in history if h["status"] == "inactive"
    )
    for balance in records["balances"]:
        if balance["account_id"] in inactive_ids:
            assert balance["month"] < last_inactive


def test_records_load_through_import_path(base_container: Container) -> None:
    container = build_data_services_container(base_container)
    container.resolve(SchemaManager).create_all_tables()
    records = build_sample_records(TODAY)

    container.resolve(InitDataService).import_records(records)

    uow: UnitOfWork
    with container.resolve(UnitOfWork) as uow:
        assert len(uow.accounts.get_all()) == len(records["accounts"])


def test_import_records_rejects_missing_tables(base_container: Container) -> None:
    container = build_data_services_container(base_container)
    with pytest.raises(ValueError, match="Missing import tables"):
        container.resolve(InitDataService).import_records({"currencies": []})
