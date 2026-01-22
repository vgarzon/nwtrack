"""
Tests for account creator use case
"""

import re

import pytest

import nwtrack.application.use_cases.create_category
from nwtrack.application.use_cases.create_category import CreateCategoryInteractive
from nwtrack.bootstrap.container import Container
from tests.helpers import init_db_tables_w_entities


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.use_cases.create_category import (
        Console,
        FetchService,
    )
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.infra.config.settings import Settings

    return (
        base_container.register(
            DBAdminService,
            lambda c: DBAdminService(
                c.resolve(Settings), c.resolve(DBConnectionManager)
            ),
        )
        .register(
            Console,
            lambda c: Console(),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            CreateCategoryInteractive,
            lambda c: CreateCategoryInteractive(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=FetchService(uow=lambda: c.resolve(UnitOfWork)),
                console=Console(),
            ),
        )
    )


def test_create_category_run(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
    capsys,
) -> None:
    # TODO: Use common fixture to init DB with entities
    input_prompt = iter(
        [
            "new_category_5",  # category name
            "asset",  # category side
        ]
    )

    def mock_prompt(*args, **kwargs):
        return next(input_prompt)

    init_db_tables_w_entities(configured_container, sample_entities)
    monkeypatch.setattr(
        nwtrack.application.use_cases.create_category.Prompt,
        "ask",
        mock_prompt,
    )
    configured_container.resolve(CreateCategoryInteractive).run()
    captured = capsys.readouterr()
    # TODO: Enable assertions through direct database queries instead of output matching
    assert len(captured.out.splitlines()) == 23
    assert re.search(r"Category 'new_category_5' created successfully", captured.out)
    assert re.search(r"Category name: new_category_5", captured.out)
    assert re.search(r"Category side: asset", captured.out)
