"""
Tests for account creator use case
"""

import re

import pytest
from rich.console import Console
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.update_account_info import UpdateAccountInfo
from nwtrack.bootstrap.container import Container
from nwtrack.domain.models import Institution, Tag
from nwtrack.entrypoints.cli.adapters.account_presenters import (
    RichAccountUpdatePresenter,
)
from nwtrack.entrypoints.cli.ui.console import ConsoleSettings, build_console


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""

    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.infra.config.settings import Settings
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

    return (
        base_container.register(
            SchemaManager,
            lambda c: SchemaManagerImpl(engine=c.resolve(SQLiteSessionManager).engine),
        )
        .register(
            DBAdminService,
            lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
        )
        .register(
            Console,
            lambda _: build_console(ConsoleSettings(record=True)),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            RichAccountUpdatePresenter,
            lambda c: RichAccountUpdatePresenter(
                console=c.resolve(Console),
                fetcher=c.resolve(FetchService),
            ),
        )
        .register(
            UpdateAccountInfo,
            lambda c: UpdateAccountInfo(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(RichAccountUpdatePresenter),
            ),
        )
    )


def _patch_update_prompts(
    monkeypatch,
    *,
    prompt_values: list[str],
    int_values: list[int],
    confirm_values: list[bool],
    prompt_calls: list[str] | None = None,
) -> None:
    """Patch Rich prompt classes for account update workflow tests."""
    input_prompt = iter(prompt_values)
    input_int_prompt = iter(int_values)
    input_confirm_prompt = iter(confirm_values)

    def mock_prompt(*args, **kwargs):
        if prompt_calls is not None and len(args) > 1:
            prompt_calls.append(str(args[1]))
        return next(input_prompt)

    def mock_int_prompt(*args, **kwargs):
        return next(input_int_prompt)

    def mock_confirm_prompt(*args, **kwargs):
        return next(input_confirm_prompt)

    from rich.prompt import Confirm, IntPrompt, Prompt

    monkeypatch.setattr(Prompt, "ask", mock_prompt)
    monkeypatch.setattr(IntPrompt, "ask", mock_int_prompt)
    monkeypatch.setattr(Confirm, "ask", mock_confirm_prompt)


def test_account_updater_run_success_with_no_institutions(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    _patch_update_prompts(
        monkeypatch,
        prompt_values=[
            "bank_1_savings",
            "Savings account at bank 1",
        ],
        int_values=[
            1,
            2,
            2,
            2,
        ],
        confirm_values=[True],
    )

    init_db_tables_w_entities(configured_container, sample_entities)

    result: OperationResult[None] = configured_container.resolve(
        UpdateAccountInfo
    ).run()

    assert result.success

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        updated_account = uow.accounts.get_by_id(1)
    assert updated_account is not None
    assert updated_account.institution_id is None

    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()

    assert re.search(r"Account ID: 1", captured_output)
    assert re.search(r"Account name: bank_1_savings", captured_output)
    assert re.search(r"Savings account at bank 1", captured_output)
    assert re.search(r"Currency: CHF", captured_output)
    assert re.search(r"Category: savings", captured_output)
    assert re.search(r"Status: inactive", captured_output)
    assert re.search(r"Institution: None", captured_output)
    assert re.search(r"Account updated successfully", captured_output)
    assert re.search(
        r"No institutions available\. Continuing with no institution assigned\.",
        captured_output,
    )
    assert re.search(
        r"No tags available\. Continuing with no tags assigned\.",
        captured_output,
    )


def test_account_updater_can_add_institution(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    prompt_order: list[str] = []

    setup_uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with setup_uow as uow:
        institution_id = uow.institutions.insert(
            Institution(name="Chase", description="Primary bank")
        )

    _patch_update_prompts(
        monkeypatch,
        prompt_values=[
            "1",
            "bank_1_checking",
            "bank_1 checking",
        ],
        int_values=[
            1,
            1,
            1,
            1,
        ],
        confirm_values=[True],
        prompt_calls=prompt_order,
    )

    result: OperationResult[None] = configured_container.resolve(
        UpdateAccountInfo
    ).run()

    assert result.success

    refresh_uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with refresh_uow as uow:
        updated_account = uow.accounts.get_by_id(1)
    assert updated_account is not None
    assert updated_account.institution_id == institution_id
    assert "institution index" in prompt_order[0]

    captured_output: str = configured_container.resolve(Console).export_text()
    assert re.search(r"Institution: Chase", captured_output)


def test_account_updater_can_change_institution(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)

    setup_uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with setup_uow as uow:
        chase_id = uow.institutions.insert(
            Institution(name="Chase", description="Primary bank")
        )
        fidelity_id = uow.institutions.insert(
            Institution(name="Fidelity", description="Brokerage")
        )
        account = uow.accounts.get_by_id(1)
        assert account is not None
        account.institution_id = chase_id
        uow.accounts.update(account)

    _patch_update_prompts(
        monkeypatch,
        prompt_values=[
            "2",
            "bank_1_checking",
            "bank_1 checking",
        ],
        int_values=[
            1,
            1,
            1,
            1,
        ],
        confirm_values=[True],
    )

    result: OperationResult[None] = configured_container.resolve(
        UpdateAccountInfo
    ).run()

    assert result.success

    refresh_uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with refresh_uow as uow:
        updated_account = uow.accounts.get_by_id(1)
    assert updated_account is not None
    assert updated_account.institution_id == fidelity_id

    captured_output: str = configured_container.resolve(Console).export_text()
    assert re.search(r"Institution: Fidelity", captured_output)


def test_account_updater_can_clear_institution(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)

    setup_uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with setup_uow as uow:
        chase_id = uow.institutions.insert(
            Institution(name="Chase", description="Primary bank")
        )
        account = uow.accounts.get_by_id(1)
        assert account is not None
        account.institution_id = chase_id
        uow.accounts.update(account)

    _patch_update_prompts(
        monkeypatch,
        prompt_values=[
            "0",
            "bank_1_checking",
            "bank_1 checking",
        ],
        int_values=[
            1,
            1,
            1,
            1,
        ],
        confirm_values=[True],
    )

    result: OperationResult[None] = configured_container.resolve(
        UpdateAccountInfo
    ).run()

    assert result.success

    refresh_uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with refresh_uow as uow:
        updated_account = uow.accounts.get_by_id(1)
    assert updated_account is not None
    assert updated_account.institution_id is None

    captured_output: str = configured_container.resolve(Console).export_text()
    assert re.search(r"Institution: None", captured_output)


def test_account_updater_can_add_tags(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Update should replace the account tag set from the tag selection step."""
    init_db_tables_w_entities(configured_container, sample_entities)

    setup_uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with setup_uow as uow:
        first_tag_id = uow.tags.insert(Tag(name="core", description="Core holding"))
        second_tag_id = uow.tags.insert(Tag(name="liquid", description="Quick access"))

    _patch_update_prompts(
        monkeypatch,
        prompt_values=[
            "1,2",
            "bank_1_checking",
            "bank_1 checking",
        ],
        int_values=[
            1,
            1,
            1,
            1,
        ],
        confirm_values=[True],
    )

    result: OperationResult[None] = configured_container.resolve(
        UpdateAccountInfo
    ).run()

    assert result.success

    refresh_uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with refresh_uow as uow:
        updated_account = uow.accounts.get_by_id(1)
    assert updated_account is not None
    assert [tag.id for tag in updated_account.tags] == [first_tag_id, second_tag_id]


def test_account_updater_can_clear_tags(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Update should clear all tags through the explicit no-tags path."""
    init_db_tables_w_entities(configured_container, sample_entities)

    setup_uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with setup_uow as uow:
        tag_id = uow.tags.insert(Tag(name="core", description="Core holding"))
        uow.tags.replace_for_account(1, [tag_id])

    _patch_update_prompts(
        monkeypatch,
        prompt_values=[
            "0",
            "bank_1_checking",
            "bank_1 checking",
        ],
        int_values=[
            1,
            1,
            1,
            1,
        ],
        confirm_values=[True],
    )

    result: OperationResult[None] = configured_container.resolve(
        UpdateAccountInfo
    ).run()

    assert result.success

    refresh_uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with refresh_uow as uow:
        updated_account = uow.accounts.get_by_id(1)
    assert updated_account is not None
    assert updated_account.tags == []


def test_account_updater_quits_when_institution_selector_receives_q(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        uow.institutions.insert(Institution(name="Chase", description="Primary bank"))

    _patch_update_prompts(
        monkeypatch,
        prompt_values=["q"],
        int_values=[1],
        confirm_values=[],
    )

    result: OperationResult[None] = configured_container.resolve(
        UpdateAccountInfo
    ).run()

    assert not result.success
    assert result.error_message == "Cancelled by user"


def test_account_updater_quits_when_tag_selector_receives_q(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Update should cancel cleanly when quitting from tag selection."""
    init_db_tables_w_entities(configured_container, sample_entities)

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        uow.tags.insert(Tag(name="core", description="Core holding"))

    _patch_update_prompts(
        monkeypatch,
        prompt_values=["q"],
        int_values=[1],
        confirm_values=[],
    )

    result: OperationResult[None] = configured_container.resolve(
        UpdateAccountInfo
    ).run()

    assert not result.success
    assert result.error_message == "Cancelled by user"
