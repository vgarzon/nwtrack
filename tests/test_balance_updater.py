"""
Test suite for the balance updater use case
"""

import re

from nwtrack.compose import build_data_services_container
from nwtrack.container import Container
from nwtrack.use_cases.balance_updater import BalanceUpdater
from tests.test_services import init_db_tables_w_entities


def test_update_balances_loop(
    test_container: Container, test_entities: dict[str, list], monkeypatch, capsys
) -> None:
    """Test initializing database and loading sample data."""
    container = build_data_services_container(test_container)
    init_db_tables_w_entities(container, test_entities)

    inputs = iter(
        [
            "2025 11",  # Input month
            "1",  # Update account ID 1
            "300",  # New balance
            "3",  # Update account ID 2
            "500",  # New balance
            "q",  # Quit
        ]
    )

    updater = BalanceUpdater(test_container)

    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    updater.run()
    captured = capsys.readouterr()

    assert re.search(r"Net Worth: 300", captured.out)
