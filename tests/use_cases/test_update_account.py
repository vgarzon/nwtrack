"""
Tests for account creator use case
"""

import re
import pytest
import nwtrack.application.use_cases.create_account
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.infra.config.settings import Settings
from nwtrack.bootstrap.container import Container
from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases.update_account_info import UpdateAccountInfo
from tests.helpers import init_db_tables_w_entities


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    return base_container.register(
        DBAdminService,
        lambda c: DBAdminService(c.resolve(Settings), c.resolve(DBConnectionManager)),
    ).register(
        UpdateAccountInfo,
        lambda c: UpdateAccountInfo(uow=lambda: c.resolve(UnitOfWork)),
    )


def test_account_creator_run_success_defaults(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
    capsys,
) -> None:
    # TODO: Use common fixture to init DB with entities
    input_prompt = iter(
        [
            "bank_1_savings",  # Account name
            "Savings account at bank 1",  # Account description
        ]
    )
    input_int_prompt = iter(
        [
            "1",  # Account ID
            "2",  # Account type: Savings
            "2",  # Currency: CHF
            "2",  # Status: Inactive
        ]
    )
    input_confirm_prompt = iter(
        [
            "y",  # Proeed with update y/n
        ]
    )

    def mock_prompt(question, **kwargs):
        return next(input_prompt)

    def mock_int_prompt(question, **kwargs):
        return int(next(input_int_prompt))

    def mock_confirm_prompt(question, **kwargs):
        return next(input_confirm_prompt)

    init_db_tables_w_entities(configured_container, sample_entities)
    updater: UpdateAccountInfo = configured_container.resolve(UpdateAccountInfo)
    monkeypatch.setattr(
        nwtrack.application.use_cases.update_account_info.Prompt,
        "ask",
        mock_prompt,
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.update_account_info.IntPrompt,
        "ask",
        mock_int_prompt,
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.update_account_info.Confirm,
        "ask",
        mock_confirm_prompt,
    )
    updater.run()
    captured = capsys.readouterr()
    # TODO: Enable assertions through direct database queries
    assert re.search(r"Account ID: 1", captured.out)
    assert re.search(r"Account name: bank_1_savings", captured.out)
    assert re.search(r"Savings account at bank 1", captured.out)
    assert re.search(r"Currency: CHF", captured.out)
    assert re.search(r"Category: savings", captured.out)
    assert re.search(r"Status: inactive", captured.out)
    assert re.search(r"Account updated successfully", captured.out)
