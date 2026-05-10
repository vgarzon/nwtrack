"""Repository tests for tag admin operations."""

from tests.helpers import _uow_factory, init_db_tables_w_entities

from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.domain.models import Account, Status, Tag


def test_tags_repo_update(base_container, sample_entities) -> None:
    """Tags can be updated through the repository."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        tag = Tag(name="Liquid", description="Quick access")
        tag_id = uow.tags.insert(tag)
        tag.id = tag_id
        tag.name = "Liquid Assets"
        tag.description = "Updated description"
        rowcount = uow.tags.update(tag)
        stored = uow.tags.get_by_id(tag_id)

    assert rowcount == 1
    assert stored is not None
    assert stored.name == "Liquid Assets"
    assert stored.description == "Updated description"


def test_tags_repo_delete_by_id(base_container, sample_entities) -> None:
    """Tags can be deleted by ID."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        tag_id = uow.tags.insert(Tag(name="Delete Me", description="Unused"))
        rowcount = uow.tags.delete_by_id(tag_id)
        stored = uow.tags.get_by_id(tag_id)

    assert rowcount == 1
    assert stored is None


def test_tags_repo_counts_linked_accounts(base_container, sample_entities) -> None:
    """Linked-account counts should reflect account tag assignments."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        first_account = uow.accounts.insert(
            Account(
                name="cash_tagged",
                description="Cash account",
                category_name="checking",
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )
        second_account = uow.accounts.insert(
            Account(
                name="brokerage_tagged",
                description="Brokerage account",
                category_name="checking",
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )
        tag_id = uow.tags.insert(Tag(name="Liquid", description="Quick access"))
        uow.tags.replace_for_account(first_account, [tag_id])
        uow.tags.replace_for_account(second_account, [tag_id])
        count = uow.tags.count_linked_accounts(tag_id)

    assert count == 2


def test_tags_repo_replace_for_account_can_attach_replace_and_clear(
    base_container, sample_entities
) -> None:
    """Replacing account tags should attach, replace, and clear associations."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        account_id = uow.accounts.insert(
            Account(
                name="replace_tags_account",
                description="Replace tags",
                category_name="checking",
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )
        liquid_id = uow.tags.insert(Tag(name="Liquid", description="Quick access"))
        core_id = uow.tags.insert(Tag(name="Core", description="Core holding"))
        uow.tags.replace_for_account(account_id, [liquid_id, liquid_id])
        first_pass = uow.tags.get_for_account(account_id)
        uow.tags.replace_for_account(account_id, [core_id])
        second_pass = uow.tags.get_for_account(account_id)
        uow.tags.replace_for_account(account_id, [])
        third_pass = uow.tags.get_for_account(account_id)

    assert [tag.name for tag in first_pass] == ["Liquid"]
    assert [tag.name for tag in second_pass] == ["Core"]
    assert third_pass == []
