"""
Test account service methods.
"""

import pytest
from nwtrack.container import Container
from nwtrack.services import AccountService
from tests.test_services import init_db_tables_w_entities


def test_get_all(test_container: Container, test_entities: dict[str, list]) -> None:
    """Test retrieving accounts."""
    init_db_tables_w_entities(test_container, test_entities)
    svc: AccountService = test_container.resolve(AccountService)

    active_accounts = svc.get_all(active_only=True)
    assert len(active_accounts) == 3
    assert active_accounts[-1].id == 3
    assert active_accounts[-1].name == "credit_cards_1"

    all_accounts = svc.get_all(active_only=False)
    assert len(all_accounts) == 4
    assert all_accounts[-1].id == 4
    assert all_accounts[-1].name == "mortgage_1"


def test_get_by_id(test_container: Container, test_entities: dict[str, list]) -> None:
    """Test retrieving account by ID."""
    init_db_tables_w_entities(test_container, test_entities)
    svc: AccountService = test_container.resolve(AccountService)

    account = svc.get_by_id(2)
    assert account is not None
    assert account.name == "bank_2_savings"
    assert account.category_name == "savings"
    assert str(account.status) == "active"

    account = svc.get_by_id(4)
    assert account is not None
    assert account.name == "mortgage_1"
    assert account.category_name == "mortgage"
    assert str(account.status) == "inactive"

    non_existent_account = svc.get_by_id(999)
    assert non_existent_account is None, "Account with ID 999 should not exist"


def test_get_by_name(test_container: Container, test_entities: dict[str, list]) -> None:
    """Test retrieving account by name."""
    init_db_tables_w_entities(test_container, test_entities)
    svc: AccountService = test_container.resolve(AccountService)

    account = svc.get_by_name("credit_cards_1")
    assert account is not None
    assert account.id == 3
    assert account.category_name == "revolving_credit"
    assert str(account.status) == "active"

    account = svc.get_by_name("mortgage_1")
    assert account is not None
    assert account.id == 4
    assert account.category_name == "mortgage"
    assert str(account.status) == "inactive"

    non_existent_account = svc.get_by_name("non_existent_account")
    assert non_existent_account is None


def test_create_account(
    test_container: Container, test_entities: dict[str, list]
) -> None:
    """Test inserting a new account."""
    init_db_tables_w_entities(test_container, test_entities)
    svc: AccountService = test_container.resolve(AccountService)

    new_account = svc.create(
        name="bank_3_checking",
        description="Test checking account",
        category_name="checking",
        currency_code="USD",
        status_str="active",
    )

    assert new_account.id == 5
    assert new_account.name == "bank_3_checking"
    assert new_account.category_name == "checking"
    assert str(new_account.status) == "active"


def test_create_account_invalid_category(
    test_container: Container, test_entities: dict[str, list]
) -> None:
    """Test inserting a new account with an invalid category."""
    init_db_tables_w_entities(test_container, test_entities)
    svc: AccountService = test_container.resolve(AccountService)

    with pytest.raises(ValueError) as exc_info:
        svc.create(
            name="invalid_category_account",
            description="Test account with invalid category",
            category_name="invalid_category",
            currency_code="USD",
            status_str="active",
        )
    assert "Category not found" in str(exc_info.value)


def test_create_account_invalid_status(
    test_container: Container, test_entities: dict[str, list]
) -> None:
    """Test inserting a new account with an invalid status."""
    init_db_tables_w_entities(test_container, test_entities)
    svc: AccountService = test_container.resolve(AccountService)

    with pytest.raises(ValueError) as exc_info:
        svc.create(
            name="invalid_status_account",
            description="Test account with invalid status",
            category_name="checking",
            currency_code="USD",
            status_str="invalid_status",
        )
    assert "Status must be 'active'" in str(exc_info.value)


def test_create_account_invalid_currency(
    test_container: Container, test_entities: dict[str, list]
) -> None:
    """Test inserting a new account with an invalid currency."""
    init_db_tables_w_entities(test_container, test_entities)
    svc: AccountService = test_container.resolve(AccountService)

    with pytest.raises(ValueError) as exc_info:
        svc.create(
            name="invalid_currency_account",
            description="Test account with invalid currency",
            category_name="checking",
            currency_code="INVALID",
            status_str="active",
        )
    assert "Currency not found" in str(exc_info.value)


def test_create_duplicate_account(
    test_container: Container, test_entities: dict[str, list]
) -> None:
    """Test inserting a duplicate account."""
    init_db_tables_w_entities(test_container, test_entities)
    svc: AccountService = test_container.resolve(AccountService)

    with pytest.raises(ValueError) as exc_info:
        svc.create(
            name="bank_1_checking",
            description="Duplicate account",
            category_name="checking",
            currency_code="USD",
            status_str="active",
        )
    assert "Account with name 'bank_1_checking' already exists" in str(exc_info.value)
