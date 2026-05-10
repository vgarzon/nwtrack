"""Tests for tag delete use case."""

import re

import pytest
from rich.console import Console
from tests.helpers import init_db_tables_w_entities

import nwtrack.entrypoints.cli.adapters.tag_presenters
from nwtrack.application.use_cases.delete_tag import DeleteTagInteractive
from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.adapters.tag_presenters import RichTagDeletePresenter
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
            RichTagDeletePresenter,
            lambda c: RichTagDeletePresenter(console=c.resolve(Console)),
        )
        .register(
            DeleteTagInteractive,
            lambda c: DeleteTagInteractive(
                uow=lambda: c.resolve(UnitOfWork),
                presenter=c.resolve(RichTagDeletePresenter),
            ),
        )
    )


def test_delete_tag_run(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Tag delete workflow should succeed when no accounts are linked."""
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.domain.models import Tag

    init_db_tables_w_entities(configured_container, sample_entities)
    uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow:
        uow.tags.insert(Tag(name="liquid", description="Quick access"))

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_id",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters.Confirm,
        "ask",
        lambda *args, **kwargs: True,
    )

    service: DeleteTagInteractive = configured_container.resolve(DeleteTagInteractive)
    result = service.run()

    assert result.success
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()
    assert re.search(r"Tag deleted successfully", captured_output)


def test_delete_tag_blocked_when_accounts_linked(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Delete should be blocked when a tag is still referenced."""
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.domain.models import Account, Status, Tag

    init_db_tables_w_entities(configured_container, sample_entities)
    uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow:
        account_id = uow.accounts.insert(
            Account(
                name="cash_bucket",
                description="Cash bucket",
                category_name="checking",
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )
        tag_id = uow.tags.insert(Tag(name="liquid", description="Quick access"))
        uow.tags.replace_for_account(account_id, [tag_id])

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_id",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters.Confirm,
        "ask",
        lambda *args, **kwargs: True,
    )

    service: DeleteTagInteractive = configured_container.resolve(DeleteTagInteractive)
    result = service.run()

    assert not result.success
    assert result.error_message == "Tag still has linked accounts"
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()
    assert re.search(r"Cannot delete tag 'liquid'", captured_output)
    assert re.search(r"1 account\(s\)", captured_output)


def test_delete_tag_no_tags(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Delete should exit cleanly when no tags exist."""
    init_db_tables_w_entities(configured_container, sample_entities)

    service: DeleteTagInteractive = configured_container.resolve(DeleteTagInteractive)
    result = service.run()

    assert not result.success
    assert result.error_message == "No tags found"


def test_delete_tag_cancellation(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Delete should stop cleanly when the user cancels selection."""
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.domain.models import Tag

    init_db_tables_w_entities(configured_container, sample_entities)
    uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow:
        uow.tags.insert(Tag(name="liquid", description="Quick access"))

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_id",
        lambda *args, **kwargs: None,
    )

    service: DeleteTagInteractive = configured_container.resolve(DeleteTagInteractive)
    result = service.run()

    assert not result.success
    assert result.error_message == "Cancelled by user"
