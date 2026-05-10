"""Schema tests for tag persistence foundations."""

from typing import cast

import pytest
from sqlalchemy import delete, insert, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from tests.helpers import _uow_factory, init_db_tables_w_entities

from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.domain.models import Account, Status, Tag
from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
from nwtrack.infra.persistence.orm.models import account_tags_table
from nwtrack.infra.persistence.uow import SQLAlchemyUnitOfWork


def _session_from_uow(uow: SQLAlchemyUnitOfWork) -> Session:
    """Return the active SQLAlchemy session for low-level association tests."""
    assert uow._session is not None
    return uow._session


def test_schema_includes_tags_table(base_container) -> None:
    """Ensure metadata-driven schema creation includes the tags table."""
    engine = base_container.resolve(SQLiteSessionManager).engine
    inspector = inspect(engine)

    table_names = inspector.get_table_names()
    tag_columns = {column["name"] for column in inspector.get_columns("tags")}

    assert "tags" in table_names
    assert tag_columns == {"id", "name", "description"}


def test_schema_includes_account_tags_table(base_container) -> None:
    """Ensure metadata-driven schema creation includes the account_tags table."""
    engine = base_container.resolve(SQLiteSessionManager).engine
    inspector = inspect(engine)

    table_names = inspector.get_table_names()
    account_tag_columns = {
        column["name"] for column in inspector.get_columns("account_tags")
    }
    unique_constraints = inspector.get_unique_constraints("account_tags")

    assert "account_tags" in table_names
    assert account_tag_columns == {"account_id", "tag_id"}
    assert unique_constraints == [
        {
            "name": "uq_account_tags_account_tag",
            "column_names": ["account_id", "tag_id"],
        }
    ]


def test_account_tags_support_many_to_many_links(
    base_container, sample_entities
) -> None:
    """Accounts and tags should support many-to-many associations."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        session = _session_from_uow(cast(SQLAlchemyUnitOfWork, uow))
        checking = uow.accounts.insert(
            Account(
                name="cash_account",
                description="Cash",
                category_name="checking",
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )
        brokerage = uow.accounts.insert(
            Account(
                name="brokerage_account",
                description="Brokerage",
                category_name="checking",
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )
        emergency = Tag(name="Emergency Fund", description="Cash reserve")
        liquid = Tag(name="Liquid", description="Quick access")
        session.add_all([emergency, liquid])
        session.flush()
        session.execute(
            insert(account_tags_table),
            [
                {"account_id": checking, "tag_id": emergency.id},
                {"account_id": checking, "tag_id": liquid.id},
                {"account_id": brokerage, "tag_id": liquid.id},
            ],
        )

        first_account = uow.accounts.get_by_id(checking)
        second_account = uow.accounts.get_by_id(brokerage)

    assert first_account is not None
    assert sorted(tag.name for tag in first_account.tags) == [
        "Emergency Fund",
        "Liquid",
    ]
    assert second_account is not None
    assert [tag.name for tag in second_account.tags] == ["Liquid"]


def test_account_tags_reject_duplicate_links(base_container, sample_entities) -> None:
    """One account should not be able to hold the same tag twice."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with pytest.raises(IntegrityError):
        with _uow_factory(container) as uow:
            session = _session_from_uow(cast(SQLAlchemyUnitOfWork, uow))
            account_id = uow.accounts.insert(
                Account(
                    name="duplicate_link_account",
                    description="Duplicate link test",
                    category_name="checking",
                    currency_code="USD",
                    status=Status.ACTIVE,
                )
            )
            tag = Tag(name="Liquid", description="Quick access")
            session.add(tag)
            session.flush()
            session.execute(
                insert(account_tags_table).values(account_id=account_id, tag_id=tag.id)
            )
            session.execute(
                insert(account_tags_table).values(account_id=account_id, tag_id=tag.id)
            )
            session.flush()


def test_deleting_account_removes_only_account_tag_links(
    base_container, sample_entities
) -> None:
    """Deleting an account should clean up only its association rows."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        session = _session_from_uow(cast(SQLAlchemyUnitOfWork, uow))
        account_id = uow.accounts.insert(
            Account(
                name="delete_account_test",
                description="Delete account",
                category_name="checking",
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )
        tag = Tag(name="Retain Tag", description="Should survive account deletion")
        session.add(tag)
        session.flush()
        session.execute(
            insert(account_tags_table).values(account_id=account_id, tag_id=tag.id)
        )
        session.execute(delete(Account).where(Account.id == account_id))

        remaining_links = session.execute(select(account_tags_table)).all()
        remaining_tags = session.execute(select(Tag)).scalars().all()

    assert remaining_links == []
    assert [stored_tag.name for stored_tag in remaining_tags] == ["Retain Tag"]


def test_deleting_tag_removes_only_account_tag_links(
    base_container, sample_entities
) -> None:
    """Deleting a tag should clean up only its association rows."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        session = _session_from_uow(cast(SQLAlchemyUnitOfWork, uow))
        account_id = uow.accounts.insert(
            Account(
                name="delete_tag_test",
                description="Delete tag",
                category_name="checking",
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )
        tag = Tag(name="Delete Me", description="Should not remove account")
        session.add(tag)
        session.flush()
        session.execute(
            insert(account_tags_table).values(account_id=account_id, tag_id=tag.id)
        )
        session.execute(delete(Tag).where(Tag.id == tag.id))

        remaining_links = session.execute(select(account_tags_table)).all()
        remaining_accounts = session.execute(select(Account)).scalars().all()

    assert remaining_links == []
    assert any(account.name == "delete_tag_test" for account in remaining_accounts)
