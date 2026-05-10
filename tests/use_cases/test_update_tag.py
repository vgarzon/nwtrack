"""Tests for tag updater use case."""

import re

import pytest
from rich.console import Console
from tests.helpers import init_db_tables_w_entities

import nwtrack.entrypoints.cli.adapters.tag_presenters
from nwtrack.application.use_cases.update_tag import UpdateTagInteractive
from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.adapters.tag_presenters import RichTagUpdatePresenter
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
            RichTagUpdatePresenter,
            lambda c: RichTagUpdatePresenter(console=c.resolve(Console)),
        )
        .register(
            UpdateTagInteractive,
            lambda c: UpdateTagInteractive(
                uow=lambda: c.resolve(UnitOfWork),
                presenter=c.resolve(RichTagUpdatePresenter),
            ),
        )
    )


def test_update_tag_run(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Tag update workflow should succeed for a valid ID."""
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
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_name",
        lambda *args, **kwargs: "  Long   Term  ",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_description",
        lambda *args, **kwargs: "Updated description",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters.Confirm,
        "ask",
        lambda *args, **kwargs: True,
    )

    service: UpdateTagInteractive = configured_container.resolve(UpdateTagInteractive)
    result = service.run()

    assert result.success
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()
    assert re.search(r"Tag updated successfully", captured_output)
    assert re.search(r"long term", captured_output)


def test_update_tag_rejects_duplicate_name_after_normalization(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Update should reject duplicate tag names after normalization."""
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.domain.models import Tag

    init_db_tables_w_entities(configured_container, sample_entities)
    uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow:
        uow.tags.insert(Tag(name="liquid", description="Quick access"))
        uow.tags.insert(Tag(name="core holding", description="Core"))

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_id",
        lambda *args, **kwargs: 2,
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_name",
        lambda *args, **kwargs: "LIQUID",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_description",
        lambda *args, **kwargs: "Duplicate description",
    )

    service: UpdateTagInteractive = configured_container.resolve(UpdateTagInteractive)
    result = service.run()

    assert not result.success
    assert result.error_message == "Duplicate tag name"
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()
    assert re.search(r"Tag name 'liquid' already exists", captured_output)


def test_update_tag_reprompts_invalid_id(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Update should re-prompt when the selected tag ID is invalid."""
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.domain.models import Tag

    init_db_tables_w_entities(configured_container, sample_entities)
    uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow:
        uow.tags.insert(Tag(name="liquid", description="Quick access"))

    id_answers = iter([99, 1])

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_id",
        lambda *args, **kwargs: next(id_answers),
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_name",
        lambda *args, **kwargs: "long term",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_description",
        lambda *args, **kwargs: "Updated description",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters.Confirm,
        "ask",
        lambda *args, **kwargs: True,
    )

    service: UpdateTagInteractive = configured_container.resolve(UpdateTagInteractive)
    result = service.run()

    assert result.success
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()
    assert re.search(r"Tag ID 99 not found", captured_output)


def test_update_tag_no_tags(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Update should exit cleanly when no tags exist."""
    init_db_tables_w_entities(configured_container, sample_entities)

    service: UpdateTagInteractive = configured_container.resolve(UpdateTagInteractive)
    result = service.run()

    assert not result.success
    assert result.error_message == "No tags found"


def test_update_tag_cancellation(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Update should stop cleanly when the user cancels selection."""
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

    service: UpdateTagInteractive = configured_container.resolve(UpdateTagInteractive)
    result = service.run()

    assert not result.success
    assert result.error_message == "Cancelled by user"
