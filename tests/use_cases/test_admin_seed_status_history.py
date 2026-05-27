"""Tests for SeedAccountStatusHistory use case."""

from unittest.mock import MagicMock

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.dto import OperationResult, SeedStatusHistoryResult
from nwtrack.application.ports.presentation import AdminSeedStatusHistoryPresenter
from nwtrack.application.use_cases.admin_seed_status_history import (
    SeedAccountStatusHistory,
)
from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.bootstrap.container import Container
from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl


@pytest.fixture
def schema_manager(base_container: Container) -> SchemaManagerImpl:
    from sqlalchemy.engine import Engine

    engine: Engine = base_container.resolve(SQLiteSessionManager).engine
    return SchemaManagerImpl(engine)


def test_seed_use_case_returns_success_result(
    base_container: Container,
    sample_entities: dict[str, list],
    schema_manager: SchemaManagerImpl,
) -> None:
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    presenter = MagicMock(spec=AdminSeedStatusHistoryPresenter)
    use_case = SeedAccountStatusHistory(
        schema_manager=schema_manager,
        presenter=presenter,
    )

    result: OperationResult[SeedStatusHistoryResult] = use_case.run()

    assert result.success
    assert result.data is not None
    presenter.show_header.assert_called_once()
    presenter.show_result.assert_called_once_with(result.data)


def test_seed_use_case_seeds_accounts_with_no_history(
    base_container: Container,
    schema_manager: SchemaManagerImpl,
) -> None:
    from sqlalchemy import text
    from sqlalchemy.engine import Engine

    engine: Engine = base_container.resolve(SQLiteSessionManager).engine

    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO currencies (code, description) VALUES ('USD', 'US Dollar')"
        ))
        conn.execute(text(
            "INSERT INTO categories (name, side) VALUES ('checking', 'asset')"
        ))
        conn.execute(text(
            "INSERT INTO accounts (id, name, description, category, currency, status)"
            " VALUES (50, 'acct_seed', '', 'checking', 'USD', 'active')"
        ))
        conn.execute(text(
            "INSERT INTO balances (account_id, month, amount)"
            " VALUES (50, '2024-01', 100)"
        ))

    presenter = MagicMock(spec=AdminSeedStatusHistoryPresenter)
    use_case = SeedAccountStatusHistory(
        schema_manager=schema_manager, presenter=presenter
    )
    result = use_case.run()

    assert result.success
    assert result.data is not None
    assert result.data.seeded == 1
    assert result.data.migrated == 0


def test_seed_use_case_skips_already_seeded_accounts(
    base_container: Container,
    sample_entities: dict[str, list],
    schema_manager: SchemaManagerImpl,
) -> None:
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    # sample_entities already loads account_status_history rows — all accounts seeded
    presenter = MagicMock(spec=AdminSeedStatusHistoryPresenter)
    use_case = SeedAccountStatusHistory(
        schema_manager=schema_manager, presenter=presenter
    )
    result = use_case.run()

    assert result.success
    assert result.data is not None
    # Account 4 is inactive with a single old-style history row at 2024-01 and has
    # balances from 2024-06 to 2024-11 (distinct first/last), so it gets migrated.
    assert result.data.seeded == 0
    assert result.data.migrated == 1
    assert result.data.skipped == 3  # accounts 1–3 are active with existing rows
