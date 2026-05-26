"""Tests for AccountStatusHistoryRepository and schema seeding."""

from tests.helpers import _uow_factory, init_db_tables_w_entities

from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.domain.models import AccountStatusHistory, Status
from nwtrack.domain.value_objects import Month
from nwtrack.infra.persistence.schema import SchemaManager


def _make_entry(account_id: int, status: Status, month: Month) -> AccountStatusHistory:
    return AccountStatusHistory(
        account_id=account_id,
        status=status,
        effective_month=month,
    )


class TestAccountStatusHistoryRepository:
    def test_insert_and_get_all_round_trip(
        self, base_container, sample_entities
    ) -> None:
        container = build_data_services_container(base_container)
        init_db_tables_w_entities(container, sample_entities)

        with _uow_factory(container) as uow:
            entry = _make_entry(1, Status.ACTIVE, Month(2025, 6))
            entry_id = uow.account_status_history.insert(entry)

        with _uow_factory(container) as uow:
            all_rows = uow.account_status_history.get_all()
            rows = [r for r in all_rows if r.account_id == 1]

        assert any(r.id == entry_id for r in rows)
        inserted = next(r for r in rows if r.id == entry_id)
        assert inserted.status == Status.ACTIVE
        assert inserted.effective_month == Month(2025, 6)

    def test_insert_many_and_get_all(self, base_container, sample_entities) -> None:
        container = build_data_services_container(base_container)
        init_db_tables_w_entities(container, sample_entities)

        with _uow_factory(container) as uow:
            uow.account_status_history.insert_many([
                _make_entry(1, Status.INACTIVE, Month(2025, 6)),
                _make_entry(2, Status.INACTIVE, Month(2025, 6)),
            ])
            rows = uow.account_status_history.get_all()

        assert any(
            r.account_id == 1 and r.effective_month == Month(2025, 6) for r in rows
        )
        assert any(
            r.account_id == 2 and r.effective_month == Month(2025, 6) for r in rows
        )

    def test_get_effective_status_exact_month_match(
        self, base_container, sample_entities
    ) -> None:
        container = build_data_services_container(base_container)
        init_db_tables_w_entities(container, sample_entities)

        with _uow_factory(container) as uow:
            uow.account_status_history.insert(
                _make_entry(1, Status.ACTIVE, Month(2025, 6))
            )
            result = uow.account_status_history.get_effective_status(1, Month(2025, 6))

        assert result == Status.ACTIVE

    def test_get_effective_status_returns_most_recent_prior_row(
        self, base_container, sample_entities
    ) -> None:
        container = build_data_services_container(base_container)
        init_db_tables_w_entities(container, sample_entities)

        with _uow_factory(container) as uow:
            uow.account_status_history.insert_many([
                _make_entry(1, Status.ACTIVE, Month(2023, 6)),
                _make_entry(1, Status.INACTIVE, Month(2024, 3)),
            ])
            result = uow.account_status_history.get_effective_status(1, Month(2024, 6))

        assert result == Status.INACTIVE

    def test_get_effective_status_returns_none_when_no_prior_row(
        self, base_container, sample_entities
    ) -> None:
        container = build_data_services_container(base_container)
        init_db_tables_w_entities(container, sample_entities)

        with _uow_factory(container) as uow:
            uow.account_status_history.insert(
                _make_entry(1, Status.ACTIVE, Month(2025, 1))
            )
            result = uow.account_status_history.get_effective_status(1, Month(2020, 1))

        assert result is None

    def test_hydrate_and_hydrate_many_round_trip(
        self, base_container, sample_entities
    ) -> None:
        container = build_data_services_container(base_container)
        init_db_tables_w_entities(container, sample_entities)

        record = {
            "id": "999",
            "account_id": "1",
            "status": "active",
            "effective_month": "2024-07",
        }
        with _uow_factory(container) as uow:
            entity = uow.account_status_history.hydrate(record)
            entities = uow.account_status_history.hydrate_many([record])

        assert entity.id == 999
        assert entity.account_id == 1
        assert entity.status == Status.ACTIVE
        assert entity.effective_month == Month(2024, 7)
        assert len(entities) == 1
        assert entities[0].effective_month == Month(2024, 7)


class TestSchemaSeeding:
    def test_seeding_creates_one_row_per_account_with_earliest_balance_month(
        self, base_container
    ) -> None:
        from sqlalchemy import text

        from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager

        engine = base_container.resolve(SQLiteSessionManager).engine

        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO currencies (code, description) VALUES ('USD', 'US Dollar')"
            ))
            conn.execute(text(
                "INSERT INTO categories (name, side) VALUES ('checking', 'asset')"
            ))
            conn.execute(text(
                "INSERT INTO accounts (id, name, description, category, "
                "currency, status) VALUES "
                "(10, 'acct_a', '', 'checking', 'USD', 'active')"
            ))
            conn.execute(text(
                "INSERT INTO accounts (id, name, description, category, "
                "currency, status) VALUES "
                "(11, 'acct_b', '', 'checking', 'USD', 'inactive')"
            ))
            conn.execute(text(
                "INSERT INTO balances (account_id, month, amount) "
                "VALUES (10, '2023-03', 100)"
            ))
            conn.execute(text(
                "INSERT INTO balances (account_id, month, amount) "
                "VALUES (10, '2023-01', 200)"
            ))

        SchemaManager(engine)._seed_account_status_history()

        from sqlalchemy import select
        from sqlalchemy.orm import Session

        from nwtrack.infra.persistence.orm.models import AccountStatusHistory

        with Session(engine) as session:
            rows = session.execute(
                select(AccountStatusHistory)
                .where(AccountStatusHistory.account_id.in_([10, 11]))
                .order_by(AccountStatusHistory.account_id)
            ).scalars().all()

        assert len(rows) == 2
        acct_a = next(r for r in rows if r.account_id == 10)
        acct_b = next(r for r in rows if r.account_id == 11)
        assert acct_a.effective_month == Month(2023, 1)
        assert acct_a.status == Status.ACTIVE
        assert acct_b.effective_month == Month(1900, 1)
        assert acct_b.status == Status.INACTIVE

    def test_seeding_is_idempotent(self, base_container) -> None:
        from sqlalchemy import text

        from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager

        engine = base_container.resolve(SQLiteSessionManager).engine

        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO currencies (code, description) VALUES ('USD', 'US Dollar')"
            ))
            conn.execute(text(
                "INSERT INTO categories (name, side) VALUES ('checking', 'asset')"
            ))
            conn.execute(text(
                "INSERT INTO accounts (id, name, description, category, "
                "currency, status) VALUES "
                "(20, 'acct_c', '', 'checking', 'USD', 'active')"
            ))

        schema_mgr = SchemaManager(engine)
        schema_mgr._seed_account_status_history()
        schema_mgr._seed_account_status_history()

        from sqlalchemy import select
        from sqlalchemy.orm import Session

        from nwtrack.infra.persistence.orm.models import AccountStatusHistory

        with Session(engine) as session:
            rows = session.execute(
                select(AccountStatusHistory).where(
                    AccountStatusHistory.account_id == 20
                )
            ).scalars().all()

        assert len(rows) == 1
