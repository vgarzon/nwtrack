"""Presenter tests for account CLI views."""

from typing import cast

from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import (
    Account,
    Category,
    Currency,
    Institution,
    Side,
    Status,
)
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.adapters.account_presenters import (
    RichAccountCreationPresenter,
    RichAccountListPresenter,
)
from nwtrack.entrypoints.cli.ui.console import ConsoleSettings, build_console


class FakeAccountCreationFetchService:
    """Minimal fetch service stub for account presenter tests."""

    def get_all_categories(self) -> list[Category]:
        return [Category(name="checking", side=Side.ASSET)]

    def get_all_currencies(self) -> list[Currency]:
        return [Currency(code="USD", description="United States Dollar")]

    def get_all_institutions(self) -> list[Institution]:
        return []


def test_account_list_presenter_renders_institution_column_for_mixed_accounts() -> None:
    """Account list presenter should show assigned and unassigned institutions."""
    console = build_console(ConsoleSettings(record=True))
    presenter = RichAccountListPresenter(console)

    category = Category(name="checking", side=Side.ASSET)
    institution = Institution(name="Chase", description="Primary bank")
    institution.id = 1

    assigned_account = Account(
        name="bank_1_checking",
        description="Checking",
        category_name="checking",
        currency_code="USD",
        institution_id=1,
        status=Status.ACTIVE,
    )
    assigned_account.id = 1
    assigned_account.category = category
    assigned_account.institution = institution

    unassigned_account = Account(
        name="bank_2_savings",
        description="Savings",
        category_name="checking",
        currency_code="USD",
        institution_id=None,
        status=Status.ACTIVE,
    )
    unassigned_account.id = 2
    unassigned_account.category = category

    presenter.display_accounts(
        [assigned_account, unassigned_account],
        active_only=False,
    )

    output = console.export_text()

    assert "Institution" in output
    assert "Chase" in output
    header_line = next(line for line in output.splitlines() if "Institution" in line)
    assert header_line.index("Institution") < header_line.index("Name")
    assert "bank_2_savings" in output
    assert "None" not in output


def test_account_creation_presenter_keeps_phase14_no_tag_input(monkeypatch) -> None:
    """Phase 14 should not add tag input to account creation workflows."""
    import nwtrack.entrypoints.cli.adapters.account_presenters as account_presenters

    console = build_console(ConsoleSettings(record=True))
    presenter = RichAccountCreationPresenter(
        console,
        cast(FetchService, FakeAccountCreationFetchService()),
    )

    monkeypatch.setattr(
        account_presenters,
        "prompt_for_account_name",
        lambda *args, **kwargs: "cash_account",
    )
    monkeypatch.setattr(
        account_presenters,
        "prompt_for_account_description",
        lambda *args, **kwargs: "Cash account",
    )
    monkeypatch.setattr(
        account_presenters,
        "prompt_for_category_choice",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        account_presenters,
        "prompt_for_currency_choice",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        account_presenters,
        "prompt_for_status_choice",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        account_presenters,
        "prompt_for_month",
        lambda *args, **kwargs: Month(2025, 10),
    )
    monkeypatch.setattr(
        account_presenters,
        "prompt_for_balance_amount",
        lambda *args, **kwargs: 100,
    )

    data = presenter.collect_account_data()

    assert data is not None
    assert "institution_id" in data.__dataclass_fields__
    assert "tag_ids" not in data.__dataclass_fields__
    assert "tags" not in data.__dataclass_fields__
    output = console.export_text()
    assert (
        "No institutions available. Continuing with no institution assigned."
        in output
    )
    assert "Tag" not in output
