"""Tests for institution repository operations."""

from collections.abc import Mapping
from typing import Any

from tests.helpers import _uow_factory, init_db_tables_w_entities

from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.domain.models import Account, Institution, Status


def test_insert_and_get_institution(base_container, sample_entities) -> None:
    """Institutions can be inserted and read by id and name."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    institution = Institution(name="Chase", description="Primary bank")

    with _uow_factory(container) as uow:
        institution_id = uow.institutions.insert(institution)
        by_id = uow.institutions.get_by_id(institution_id)
        by_name = uow.institutions.get_by_name("Chase")

    assert institution_id == 1
    assert by_id is not None
    assert by_id.name == "Chase"
    assert by_id.description == "Primary bank"
    assert by_name is not None
    assert by_name.id == institution_id


def test_list_count_and_hydrate_institutions(base_container, sample_entities) -> None:
    """Institutions support the baseline repository surface from the spec."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    records: list[Mapping[str, Any]] = [
        {"id": 1, "name": "Chase", "description": "Primary bank"},
        {"id": 2, "name": "Fidelity", "description": ""},
    ]

    with _uow_factory(container) as uow:
        institutions = uow.institutions.hydrate_many(records)
        uow.institutions.insert_many(institutions)
        stored = uow.institutions.get_all()
        count = uow.institutions.count()

    assert [institution.name for institution in stored] == ["Chase", "Fidelity"]
    assert stored[1].description is None
    assert count == 2


def test_account_can_link_to_valid_institution(base_container, sample_entities) -> None:
    """Accounts can persist a valid institution reference."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    institution = Institution(name="Vanguard", description="Brokerage")

    with _uow_factory(container) as uow:
        institution_id = uow.institutions.insert(institution)
        account_id = uow.accounts.insert(
            Account(
                name="brokerage_account",
                description="Taxable brokerage",
                category_name="checking",
                institution_id=institution_id,
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )
        stored_account = uow.accounts.get_by_id(account_id)

    assert stored_account is not None
    assert stored_account.institution_id == institution_id
