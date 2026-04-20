"""
Tests for balance transfer use case.
"""

import re

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import BalanceTransferPresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases.transfer_balance import BalanceTransfer
from nwtrack.bootstrap.container import Container
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.ui.console import Console


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services needed for BalanceTransfer in the container."""

    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.use_cases.transfer_balance import (
        BalanceTransfer,
        FetchService,
    )
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.entrypoints.cli.adapters.balance_presenters import (
        RichBalanceTransferPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings
    from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory
    from nwtrack.infra.config.settings import Settings
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

    console_default = ConsoleSettings(record=True)

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
            lambda _: ConsoleFactory(default_settings=console_default)(),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            BalanceTransferPresenter,
            lambda c: RichBalanceTransferPresenter(console=c.resolve(Console)),
        )
        .register(
            BalanceTransfer,
            lambda c: BalanceTransfer(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(BalanceTransferPresenter),
            ),
        )
    )


def _read_balance(container: Container, month: Month, account_id: int) -> int | None:
    """Helper to read a balance amount from the DB."""
    from nwtrack.domain.models import Balance as BalanceModel

    uow: UnitOfWork
    with container.resolve(UnitOfWork) as uow:
        try:
            balance: BalanceModel = uow.balances.get_by_account_id(month, account_id)
            return balance.amount
        except IndexError:
            return None


def test_transfer_asset_to_asset_success(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Transfer from checking (asset) to savings (asset).

    Sender balance decreases, receiver balance increases.
    """
    import nwtrack.application.use_cases.transfer_balance as transfer_balance
    import nwtrack.entrypoints.cli.adapters.balance_presenters as balance_presenters

    init_db_tables_w_entities(configured_container, sample_entities)

    # 2025-11: account 1 (checking, asset) = 200, account 2 (savings, asset) = 500
    monkeypatch.setattr(
        transfer_balance.BalanceTransfer,
        "_select_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_from_account",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_to_account",
        lambda *args, **kwargs: 2,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "prompt_for_transfer_amount",
        lambda *args, **kwargs: 100,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "prompt_to_confirm_transfer",
        lambda *args, **kwargs: True,
    )

    result: OperationResult = configured_container.resolve(BalanceTransfer).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    assert result.success
    assert re.search(r"Transfer completed successfully", captured_output)
    # from_delta = -100 (asset), to_delta = +100 (asset)
    assert _read_balance(configured_container, Month(2025, 11), 1) == 100
    assert _read_balance(configured_container, Month(2025, 11), 2) == 600


def test_transfer_asset_to_liability_success(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Transfer from checking (asset) to credit card (liability) — paying off debt.

    Both balances decrease: asset loses cash, liability is paid down (positive storage).
    """
    import nwtrack.application.use_cases.transfer_balance as transfer_balance
    import nwtrack.entrypoints.cli.adapters.balance_presenters as balance_presenters

    init_db_tables_w_entities(configured_container, sample_entities)

    # 2025-11: account 1 (asset) = 200, account 3 (liability) = 600
    monkeypatch.setattr(
        transfer_balance.BalanceTransfer,
        "_select_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_from_account",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_to_account",
        lambda *args, **kwargs: 3,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "prompt_for_transfer_amount",
        lambda *args, **kwargs: 50,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "prompt_to_confirm_transfer",
        lambda *args, **kwargs: True,
    )

    result: OperationResult = configured_container.resolve(BalanceTransfer).run()

    assert result.success
    # from_delta = -50 (asset loses), to_delta = -50 (liability paid down)
    assert _read_balance(configured_container, Month(2025, 11), 1) == 150
    assert _read_balance(configured_container, Month(2025, 11), 3) == 550


def test_transfer_liability_to_asset_success(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Transfer from credit card (liability) to checking (asset) — drawing on credit.

    Both balances increase: liability takes on more debt, asset receives cash.
    """
    import nwtrack.application.use_cases.transfer_balance as transfer_balance
    import nwtrack.entrypoints.cli.adapters.balance_presenters as balance_presenters

    init_db_tables_w_entities(configured_container, sample_entities)

    # 2025-11: account 3 (liability) = 600, account 1 (asset) = 200
    monkeypatch.setattr(
        transfer_balance.BalanceTransfer,
        "_select_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_from_account",
        lambda *args, **kwargs: 3,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_to_account",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "prompt_for_transfer_amount",
        lambda *args, **kwargs: 100,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "prompt_to_confirm_transfer",
        lambda *args, **kwargs: True,
    )

    result: OperationResult = configured_container.resolve(BalanceTransfer).run()

    assert result.success
    # from_delta = +100 (liability: more debt), to_delta = +100 (asset gains cash)
    assert _read_balance(configured_container, Month(2025, 11), 3) == 700
    assert _read_balance(configured_container, Month(2025, 11), 1) == 300


def test_transfer_missing_balance_creates_entry(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Transfer to account with no balance for month creates a new balance entry.

    2025-06 has balances for accounts 1, 2, 3 — but NOT account 4 (mortgage).
    Transferring from account 1 to account 4 should create a new entry for account 4.
    """
    import nwtrack.application.use_cases.transfer_balance as transfer_balance
    import nwtrack.entrypoints.cli.adapters.balance_presenters as balance_presenters

    init_db_tables_w_entities(configured_container, sample_entities)

    # Verify account 4 has no balance in 2025-06 before the transfer
    assert _read_balance(configured_container, Month(2025, 6), 4) is None

    monkeypatch.setattr(
        transfer_balance.BalanceTransfer,
        "_select_month",
        lambda *args, **kwargs: Month(2025, 6),
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_from_account",
        lambda *args, **kwargs: 1,  # checking (asset), bal=200
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_to_account",
        lambda *args, **kwargs: 4,  # mortgage (liability), no balance in 2025-06
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "prompt_for_transfer_amount",
        lambda *args, **kwargs: 50,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "prompt_to_confirm_transfer",
        lambda *args, **kwargs: True,
    )

    result: OperationResult = configured_container.resolve(BalanceTransfer).run()

    assert result.success
    # Account 1 (asset, 200) → Account 4 (liability, missing=0)
    # from_delta = -50, to_delta = -50 (Asset → Liability)
    assert _read_balance(configured_container, Month(2025, 6), 1) == 150
    assert _read_balance(configured_container, Month(2025, 6), 4) == -50  # new entry


def test_transfer_cancelled_at_month_selection(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """User quits at month selection — operation is cancelled."""
    import nwtrack.application.use_cases.transfer_balance as transfer_balance

    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        transfer_balance.BalanceTransfer,
        "_select_month",
        lambda *args, **kwargs: None,
    )

    result: OperationResult = configured_container.resolve(BalanceTransfer).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    assert not result.success
    assert re.search(r"Operation canceled by user", captured_output)


def test_transfer_cancelled_at_from_account(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """User quits at source account selection — operation is cancelled."""
    import nwtrack.application.use_cases.transfer_balance as transfer_balance
    import nwtrack.entrypoints.cli.adapters.balance_presenters as balance_presenters

    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        transfer_balance.BalanceTransfer,
        "_select_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_from_account",
        lambda *args, **kwargs: None,
    )

    result: OperationResult = configured_container.resolve(BalanceTransfer).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    assert not result.success
    assert re.search(r"Operation canceled by user", captured_output)


def test_transfer_cancelled_at_to_account(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """User quits at destination account selection — operation is cancelled."""
    import nwtrack.application.use_cases.transfer_balance as transfer_balance
    import nwtrack.entrypoints.cli.adapters.balance_presenters as balance_presenters

    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        transfer_balance.BalanceTransfer,
        "_select_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_from_account",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_to_account",
        lambda *args, **kwargs: None,
    )

    result: OperationResult = configured_container.resolve(BalanceTransfer).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    assert not result.success
    assert re.search(r"Operation canceled by user", captured_output)


def test_transfer_same_account_rejected(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Selecting the same account for source and destination is rejected."""
    import nwtrack.application.use_cases.transfer_balance as transfer_balance
    import nwtrack.entrypoints.cli.adapters.balance_presenters as balance_presenters

    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        transfer_balance.BalanceTransfer,
        "_select_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_from_account",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_to_account",
        lambda *args, **kwargs: 1,  # same as from
    )

    result: OperationResult = configured_container.resolve(BalanceTransfer).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    assert not result.success
    assert re.search(r"must differ", captured_output)


def test_transfer_cancelled_at_confirmation(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """User declines the transfer at confirmation — operation is cancelled."""
    import nwtrack.application.use_cases.transfer_balance as transfer_balance
    import nwtrack.entrypoints.cli.adapters.balance_presenters as balance_presenters

    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        transfer_balance.BalanceTransfer,
        "_select_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_from_account",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_to_account",
        lambda *args, **kwargs: 2,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "prompt_for_transfer_amount",
        lambda *args, **kwargs: 100,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "prompt_to_confirm_transfer",
        lambda *args, **kwargs: False,
    )

    result: OperationResult = configured_container.resolve(BalanceTransfer).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    assert not result.success
    assert re.search(r"Operation canceled by user", captured_output)
    # Verify no balances were changed
    assert _read_balance(configured_container, Month(2025, 11), 1) == 200
    assert _read_balance(configured_container, Month(2025, 11), 2) == 500


def test_transfer_no_balances_for_month(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Selecting a month with no balances stops the operation with a warning."""
    import nwtrack.application.use_cases.transfer_balance as transfer_balance

    init_db_tables_w_entities(configured_container, sample_entities)

    # 2030-01 has no balance entries
    monkeypatch.setattr(
        transfer_balance.BalanceTransfer,
        "_select_month",
        lambda *args, **kwargs: Month(2030, 1),
    )

    result: OperationResult = configured_container.resolve(BalanceTransfer).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    assert not result.success
    assert re.search(r"No balance entries found in 2030-01", captured_output)


def test_transfer_account_not_found(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Selecting a nonexistent account ID shows an error."""
    import nwtrack.application.use_cases.transfer_balance as transfer_balance
    import nwtrack.entrypoints.cli.adapters.balance_presenters as balance_presenters

    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        transfer_balance.BalanceTransfer,
        "_select_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_from_account",
        lambda *args, **kwargs: 999,  # nonexistent
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "select_to_account",
        lambda *args, **kwargs: 2,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "prompt_for_transfer_amount",
        lambda *args, **kwargs: 100,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceTransferPresenter,
        "prompt_to_confirm_transfer",
        lambda *args, **kwargs: True,
    )

    result: OperationResult = configured_container.resolve(BalanceTransfer).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    assert not result.success
    assert re.search(r"Account 999 not found", captured_output)
