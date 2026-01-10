"""
Test print summary use case
"""

import re
import pytest

from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.infra.config.settings import Settings
from nwtrack.bootstrap.container import Container
from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.ports.uow import UnitOfWork
from tests.helpers import init_db_tables_w_entities
from nwtrack.application.use_cases.print_summary import SummaryService


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Configure container."""
    return (
        base_container.register(
            DBAdminService,
            lambda c: DBAdminService(
                c.resolve(Settings), c.resolve(DBConnectionManager)
            ),
        )
        .register(
            InitDataService,
            lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            SummaryService,
            lambda c: SummaryService(uow=lambda: c.resolve(UnitOfWork)),
        )
    )


def test_print_summary_run_select_month(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
    capsys,
) -> None:
    """Test print summary service."""
    # TODO: Use common fixture to init DB with entities
    init_db_tables_w_entities(configured_container, sample_entities)
    inputs = iter(["0"])  # Select first month in the list
    service: SummaryService = configured_container.resolve(SummaryService)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    service.run()
    captured = capsys.readouterr()
    assert re.search(r"Balances for 2025-11", captured.out)
    assert re.search(r"revolving_credit.+liability.+600", captured.out)
    assert re.search(r"Net Worth Summary for 2025-11", captured.out)
    assert re.search(r"Assets:\s+700", captured.out)


def test_print_summary_run_input_month(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
    capsys,
) -> None:
    """Test print summary service."""
    # TODO: Use common fixture to init DB with entities
    init_db_tables_w_entities(configured_container, sample_entities)
    inputs = iter(["A", "2025 11"])  # Input month directly
    service: SummaryService = configured_container.resolve(SummaryService)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    service.run()
    captured = capsys.readouterr()
    assert re.search(r"Balances for 2025-11", captured.out)
    assert re.search(r"revolving_credit.+liability.+600", captured.out)
    assert re.search(r"Net Worth Summary for 2025-11", captured.out)
    assert re.search(r"Assets:\s+700", captured.out)
