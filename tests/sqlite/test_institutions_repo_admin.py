"""Repository tests for institution admin operations."""

from tests.helpers import _uow_factory, init_db_tables_w_entities

from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.domain.models import Account, Institution, Status


def test_institutions_repo_update(base_container, sample_entities) -> None:
    """Institutions can be updated through the repository."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        institution = Institution(name="Chase", description="Primary bank")
        institution_id = uow.institutions.insert(institution)
        institution.id = institution_id
        institution.name = "Chase Bank"
        institution.description = "Updated description"
        rowcount = uow.institutions.update(institution)
        stored = uow.institutions.get_by_id(institution_id)

    assert rowcount == 1
    assert stored is not None
    assert stored.name == "Chase Bank"
    assert stored.description == "Updated description"


def test_institutions_repo_delete_by_id(base_container, sample_entities) -> None:
    """Institutions can be deleted by ID when allowed."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        institution_id = uow.institutions.insert(
            Institution(name="Fidelity", description="Brokerage")
        )
        rowcount = uow.institutions.delete_by_id(institution_id)
        stored = uow.institutions.get_by_id(institution_id)

    assert rowcount == 1
    assert stored is None


def test_institutions_repo_counts_linked_accounts(
    base_container, sample_entities
) -> None:
    """Linked-account counts should reflect account institution assignments."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        institution_id = uow.institutions.insert(
            Institution(name="Vanguard", description="Brokerage")
        )
        uow.accounts.insert(
            Account(
                name="vanguard_taxable",
                description="Taxable brokerage",
                category_name="checking",
                institution_id=institution_id,
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )
        count = uow.institutions.count_linked_accounts(institution_id)

    assert count == 1
