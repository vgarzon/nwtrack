"""Account repository tests for optional institution linkage."""

from tests.helpers import _uow_factory, init_db_tables_w_entities

from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.domain.models import Account, Status


def test_account_repo_hydrate_accepts_missing_institution_id(base_container) -> None:
    """Hydrating legacy-style account records should default institution_id to None."""
    container = build_data_services_container(base_container)

    with _uow_factory(container) as uow:
        account = uow.accounts.hydrate(
            {
                "id": 1,
                "name": "legacy_account",
                "description": "Imported from existing CSV",
                "category": "checking",
                "currency": "USD",
                "status": "active",
            }
        )

    assert account.institution_id is None


def test_account_repo_persists_account_without_institution(
    base_container, sample_entities
) -> None:
    """Accounts remain valid when no institution is assigned."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    new_account = Account(
        name="cash_wallet",
        description="Local cash account",
        category_name="checking",
        currency_code="USD",
        status=Status.ACTIVE,
    )

    with _uow_factory(container) as uow:
        account_id = uow.accounts.insert(new_account)
        stored_account = uow.accounts.get_by_id(account_id)

    assert stored_account is not None
    assert stored_account.name == "cash_wallet"
    assert stored_account.institution_id is None
