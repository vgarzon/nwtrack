"""
Test print summary use case
"""

import re

import pytest

import nwtrack.application.use_cases.print_summary
from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.application.use_cases.print_summary import SummaryService
from nwtrack.bootstrap.container import Container
from nwtrack.infra.config.settings import Settings
from tests.helpers import init_db_tables_w_entities


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


def test_print_summary_run_default_month(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
    capsys,
) -> None:
    """Test print summary service."""
    init_db_tables_w_entities(configured_container, sample_entities)

    def mock_ask(question, **kwargs):
        return "1"

    service: SummaryService = configured_container.resolve(SummaryService)
    monkeypatch.setattr(
        nwtrack.application.use_cases.print_summary.Prompt, "ask", mock_ask
    )
    service.run()
    captured = capsys.readouterr()
    assert re.search(r"Balances 2025-11", captured.out)
    assert re.search(r"Balances 2025-11", captured.out)
    assert re.search(r"credit_cards_1.+revolving_credit.+600", captured.out)
    assert re.search(r"700.+600.+100", captured.out)


def test_print_summary_run_input_month(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
    capsys,
) -> None:
    """Test print summary service."""
    inputs_ask = iter(["A"])
    inputs_int_ask = iter([2025, 10])

    init_db_tables_w_entities(configured_container, sample_entities)

    def mock_ask(question, **kwargs):
        return next(inputs_ask)

    def mock_int_ask(question, **kwargs):
        return next(inputs_int_ask)

    service: SummaryService = configured_container.resolve(SummaryService)
    monkeypatch.setattr(
        nwtrack.application.use_cases.print_summary.Prompt, "ask", mock_ask
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.print_summary.IntPrompt, "ask", mock_int_ask
    )
    service.run()
    captured = capsys.readouterr()
    assert re.search(r"Balances 2025-10", captured.out)
    assert re.search(r"Balances 2025-10", captured.out)
    assert re.search(r"credit_cards_1.+revolving_credit.+700", captured.out)
    assert re.search(r"900.+700.+200", captured.out)
