"""Tests for tag repository operations."""

from collections.abc import Mapping
from typing import Any

from tests.helpers import _uow_factory, init_db_tables_w_entities

from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.domain.models import Account, Status, Tag


def test_insert_and_get_tag(base_container, sample_entities) -> None:
    """Tags can be inserted and read by id and name."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    tag = Tag(name="Liquid", description="Quick access")

    with _uow_factory(container) as uow:
        tag_id = uow.tags.insert(tag)
        by_id = uow.tags.get_by_id(tag_id)
        by_name = uow.tags.get_by_name("Liquid")

    assert tag_id == 1
    assert by_id is not None
    assert by_id.name == "Liquid"
    assert by_id.description == "Quick access"
    assert by_name is not None
    assert by_name.id == tag_id


def test_list_count_and_hydrate_tags(base_container, sample_entities) -> None:
    """Tags support the baseline repository surface from the spec."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    records: list[Mapping[str, Any]] = [
        {"id": 1, "name": "Liquid", "description": "Quick access"},
        {"id": 2, "name": "Emergency", "description": ""},
    ]

    with _uow_factory(container) as uow:
        tags = uow.tags.hydrate_many(records)
        uow.tags.insert_many(tags)
        stored = uow.tags.get_all()
        count = uow.tags.count()

    assert [tag.name for tag in stored] == ["Liquid", "Emergency"]
    assert stored[1].description is None
    assert count == 2


def test_get_for_account_returns_assigned_tags(base_container, sample_entities) -> None:
    """Tags repository should list tags for a specific account."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        account_id = uow.accounts.insert(
            Account(
                name="tagged_account",
                description="Tagged account",
                category_name="checking",
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )
        first_tag = uow.tags.insert(Tag(name="Liquid", description="Quick access"))
        second_tag = uow.tags.insert(Tag(name="Emergency", description="Rainy day"))
        uow.tags.replace_for_account(account_id, [second_tag, first_tag])
        stored = uow.tags.get_for_account(account_id)

    assert [tag.name for tag in stored] == ["Liquid", "Emergency"]
