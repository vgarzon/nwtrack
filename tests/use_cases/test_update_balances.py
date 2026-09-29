"""
Test suite for the balance updater use case
"""

import re

import pytest
from rich.console import Console
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.update_balances import BalanceUpdater
from nwtrack.bootstrap.container import Container
from nwtrack.domain.models import Balance
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.adapters.balance_presenters import (
    RichBalanceUpdatePresenter,
)
from nwtrack.entrypoints.cli.ui.console import ConsoleSettings, build_console


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Configure container."""
    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.data_loader import InitDataService
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
            InitDataService,
            lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
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
            RichBalanceUpdatePresenter,
            lambda c: RichBalanceUpdatePresenter(console=c.resolve(Console)),
        )
        .register(
            BalanceUpdater,
            lambda c: BalanceUpdater(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(RichBalanceUpdatePresenter),
            ),
        )
    )


def test_update_balances_run(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Test initializing database and loading sample data."""
    # TODO: Use common fixture to init DB with entities
    input_prompt = iter(
        [
            "1",  # Select default month
            "1",  # Select account ID 1
            "3",  # Update account ID 3
            "q",  # Quit
        ]
    )
    input_int_prompt = iter(
        [
            300,  # New balance for account 1
            500,  # New balance for account 3
        ]
    )

    def mock_prompt(*args, **kwargs):
        return next(input_prompt)

    def mock_int_prompt(*args, **kwargs):
        return next(input_int_prompt)

    init_db_tables_w_entities(configured_container, sample_entities)

    # Patch the prompt classes
    from rich.prompt import Confirm, IntPrompt, Prompt

    monkeypatch.setattr(
        Prompt,
        "ask",
        mock_prompt,
    )
    monkeypatch.setattr(
        IntPrompt,
        "ask",
        mock_int_prompt,
    )
    # Both updates below are large percent changes from their prior balances,
    # so always confirm past the new threshold-warning prompt.
    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: True)

    from nwtrack.application.dto import OperationResult

    result: OperationResult[None] = configured_container.resolve(BalanceUpdater).run()

    assert result.success

    # Check console output
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()

    assert re.search(r"Balances 2025-11", captured_output)
    assert re.search(r"Account bank_1_checking.+2025-11.+200", captured_output)
    assert re.search(r"800.+500.+300", captured_output)

    # TODO: Test other interactions


class FakeBalanceUpdatePresenter:
    """Minimal BalanceUpdatePresenter fake for threshold-warning tests."""

    def __init__(
        self,
        account_ids: list[int | None],
        amounts: list[int],
        confirm_responses: list[bool] | None = None,
    ) -> None:
        self._account_ids = iter(account_ids)
        self._amounts = iter(amounts)
        self._confirm_responses = iter(confirm_responses or [])
        self.confirm_calls: list[tuple[str, int, int, float, bool]] = []

    def show_header(self) -> None:
        pass

    def display_active_accounts(self, accounts) -> None:
        pass

    def select_month(self, balance_counts):
        return balance_counts[0][0]

    def show_invalid_month_error(self) -> None:
        pass

    def show_no_balances_warning(self, month) -> None:
        pass

    def show_no_month_selected(self) -> None:
        pass

    def display_balances(self, balances, month) -> None:
        pass

    def prompt_for_account_id(self) -> int | None:
        return next(self._account_ids)

    def show_invalid_account_id(self) -> None:
        pass

    def show_current_balance_and_prompt(
        self, account_name, account_id, month, current_balance
    ) -> int:
        return next(self._amounts)

    def display_final_summary(self, balances, networth, month) -> None:
        pass

    def display_networth(self, nw, month) -> None:
        pass

    def confirm_large_change(
        self, account_name, current_balance, new_amount, pct_change, increased
    ) -> bool:
        self.confirm_calls.append(
            (account_name, current_balance, new_amount, pct_change, increased)
        )
        return next(self._confirm_responses)


def _get_account_1_balance(container: Container) -> Balance | None:
    return container.resolve(FetchService).get_balance_for_account_id(
        Month(2025, 11), 1
    )


def test_below_threshold_change_never_prompts_confirmation(
    configured_container: Container, sample_entities: dict[str, list]
) -> None:
    """Account 1's 2025-11 balance is 200; 210 is a ~5% change (below 20%)."""
    init_db_tables_w_entities(configured_container, sample_entities)

    presenter = FakeBalanceUpdatePresenter(account_ids=[1, None], amounts=[210])
    updater = BalanceUpdater(
        uow=lambda: configured_container.resolve(UnitOfWork),
        fetcher=configured_container.resolve(FetchService),
        presenter=presenter,
    )

    result = updater.run()

    assert result.success
    assert presenter.confirm_calls == []

    balance = _get_account_1_balance(configured_container)
    assert balance is not None
    assert balance.amount == 210


def test_above_threshold_change_confirmed_writes_new_amount(
    configured_container: Container, sample_entities: dict[str, list]
) -> None:
    """Account 1's 2025-11 balance is 200; 300 is a 50% change (above 20%)."""
    init_db_tables_w_entities(configured_container, sample_entities)

    presenter = FakeBalanceUpdatePresenter(
        account_ids=[1, None], amounts=[300], confirm_responses=[True]
    )
    updater = BalanceUpdater(
        uow=lambda: configured_container.resolve(UnitOfWork),
        fetcher=configured_container.resolve(FetchService),
        presenter=presenter,
    )

    result = updater.run()

    assert result.success
    assert len(presenter.confirm_calls) == 1
    account_name, current_balance, new_amount, pct_change, increased = (
        presenter.confirm_calls[0]
    )
    assert current_balance == 200
    assert new_amount == 300
    assert pct_change == pytest.approx(50.0)
    assert increased is True

    balance = _get_account_1_balance(configured_container)
    assert balance is not None
    assert balance.amount == 300


def test_above_threshold_change_declined_reprompts_and_does_not_write(
    configured_container: Container, sample_entities: dict[str, list]
) -> None:
    """Declining the first (large) amount re-prompts; the second amount is small
    enough to proceed without a further confirmation."""
    init_db_tables_w_entities(configured_container, sample_entities)

    presenter = FakeBalanceUpdatePresenter(
        account_ids=[1, None],
        amounts=[300, 205],
        confirm_responses=[False],
    )
    updater = BalanceUpdater(
        uow=lambda: configured_container.resolve(UnitOfWork),
        fetcher=configured_container.resolve(FetchService),
        presenter=presenter,
    )

    result = updater.run()

    assert result.success
    assert len(presenter.confirm_calls) == 1

    balance = _get_account_1_balance(configured_container)
    assert balance is not None
    assert balance.amount == 205


def test_disabled_threshold_never_prompts_even_for_large_change(
    configured_container: Container, sample_entities: dict[str, list]
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)

    presenter = FakeBalanceUpdatePresenter(account_ids=[1, None], amounts=[10_000])
    updater = BalanceUpdater(
        uow=lambda: configured_container.resolve(UnitOfWork),
        fetcher=configured_container.resolve(FetchService),
        presenter=presenter,
        change_warning_threshold_pct=0,
    )

    result = updater.run()

    assert result.success
    assert presenter.confirm_calls == []

    balance = _get_account_1_balance(configured_container)
    assert balance is not None
    assert balance.amount == 10_000


def test_balance_account_relationship_loads(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Verify Balance.account and Balance.account.category load outside session."""
    init_db_tables_w_entities(configured_container, sample_entities)

    fetcher: FetchService = configured_container.resolve(FetchService)
    balances = fetcher.get_month_balances(Month(2025, 11))

    assert len(balances) > 0
    assert balances[0].account is not None
    assert balances[0].account.category is not None
