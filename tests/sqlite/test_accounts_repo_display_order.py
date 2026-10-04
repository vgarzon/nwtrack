"""Account repository tests for display order and hidden flag."""

from collections.abc import Mapping
from typing import Any

from tests.helpers import _uow_factory, init_db_tables_w_entities

from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.domain.models import Account, Status


def _setup(base_container, sample_entities):
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)
    return container


def _names(container) -> list[str]:
    with _uow_factory(container) as uow:
        return [a.name for a in uow.accounts.get_all()]


def _slots(container) -> list[int]:
    with _uow_factory(container) as uow:
        return [a.display_order for a in uow.accounts.get_all()]


def test_sample_accounts_get_contiguous_slots_in_insert_order(
    base_container, sample_entities
) -> None:
    container = _setup(base_container, sample_entities)
    n = len(_names(container))
    assert _slots(container) == list(range(1, n + 1))


def test_new_account_is_appended_visible(base_container, sample_entities) -> None:
    container = _setup(base_container, sample_entities)
    n = len(_names(container))
    with _uow_factory(container) as uow:
        new_id = uow.accounts.insert(
            Account(
                name="cash_wallet",
                description="",
                category_name="checking",
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )
        stored = uow.accounts.get_by_id(new_id)
    assert stored is not None
    assert stored.display_order == n + 1
    assert stored.is_hidden is False
    assert _names(container)[-1] == "cash_wallet"


def test_move_swaps_with_neighbour_and_noops_at_edges(
    base_container, sample_entities
) -> None:
    container = _setup(base_container, sample_entities)
    before = _names(container)
    with _uow_factory(container) as uow:
        first, second = uow.accounts.get_all()[:2]
        assert uow.accounts.move(first.id, -1) is False
        assert uow.accounts.move(uow.accounts.get_all()[-1].id, 1) is False
        assert uow.accounts.move(first.id, 1) is True
        assert uow.accounts.move(99999, 1) is False
    after = _names(container)
    assert after[:2] == [before[1], before[0]]
    assert after[2:] == before[2:]
    assert _slots(container) == list(range(1, len(after) + 1))


def test_delete_closes_gap(base_container, sample_entities) -> None:
    container = _setup(base_container, sample_entities)
    with _uow_factory(container) as uow:
        victim_id = uow.accounts.insert(
            Account(
                name="temp",
                description="",
                category_name="checking",
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )
        # Move to the middle so deleting it leaves a gap to close.
        uow.accounts.move(victim_id, -1)
        uow.accounts.move(victim_id, -1)
    assert "temp" in _names(container)
    with _uow_factory(container) as uow:
        assert uow.accounts.delete_by_id(victim_id) == 1
    assert "temp" not in _names(container)
    assert _slots(container) == list(range(1, len(_names(container)) + 1))


def test_set_hidden_round_trips_and_does_not_filter_get_all(
    base_container, sample_entities
) -> None:
    container = _setup(base_container, sample_entities)
    with _uow_factory(container) as uow:
        target = uow.accounts.get_all()[0]
        assert uow.accounts.set_hidden(target.id, True) == 1
    with _uow_factory(container) as uow:
        accounts = uow.accounts.get_all()
    assert [a.is_hidden for a in accounts][0] is True
    assert len(accounts) == len(_names(container))


def test_hydrate_parses_optional_display_columns(base_container) -> None:
    container = build_data_services_container(base_container)
    base = {
        "name": "x",
        "description": "",
        "category": "checking",
        "currency": "USD",
        "status": "active",
    }
    with _uow_factory(container) as uow:
        legacy = uow.accounts.hydrate(base)
        full = uow.accounts.hydrate({**base, "display_order": "7", "is_hidden": "True"})
    assert (legacy.display_order, legacy.is_hidden) == (0, False)
    assert (full.display_order, full.is_hidden) == (7, True)


def test_hydrate_many_assigns_slots_to_records_without_one(base_container) -> None:
    container = build_data_services_container(base_container)
    base = {"description": "", "category": "checking", "currency": "USD"}
    records: list[Mapping[str, Any]] = [
        {**base, "name": "x", "status": "active"},
        {**base, "name": "y", "status": "active", "display_order": "5"},
        {**base, "name": "z", "status": "active"},
    ]
    with _uow_factory(container) as uow:
        accounts = uow.accounts.hydrate_many(records)
    assert [a.display_order for a in accounts] == [6, 5, 7]
