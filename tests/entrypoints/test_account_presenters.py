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
    Tag,
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

    def get_all_tags(self) -> list[Tag]:
        return []


class FakeTaggedAccountCreationFetchService(FakeAccountCreationFetchService):
    """Fetch-service stub with tags for presenter tests."""

    def get_all_tags(self) -> list[Tag]:
        liquid = Tag(name="liquid", description="Quick access")
        liquid.id = 1
        emergency = Tag(name="emergency", description="Rainy day")
        emergency.id = 2
        return [liquid, emergency]


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


def test_account_creation_presenter_handles_no_tags(monkeypatch) -> None:
    """Account creation should continue cleanly when no tags exist."""
    import nwtrack.entrypoints.cli.adapters.account_presenters as account_presenters

    console = build_console(ConsoleSettings(record=True))
    presenter = RichAccountCreationPresenter(
        console,
        cast(FetchService, FakeAccountCreationFetchService()),
    )

    monkeypatch.setattr(
        account_presenters,
        "prompt_for_optional_tag_choices",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Tag selector should not run when no tags exist.")
        ),
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
    assert data.tag_ids == []
    output = console.export_text()
    assert (
        "No institutions available. Continuing with no institution assigned."
        in output
    )
    assert "No tags available. Continuing with no tags assigned." in output


def test_account_creation_presenter_collects_tag_ids_from_indexes(monkeypatch) -> None:
    """Account creation should map selected tag indexes to tag IDs."""
    import nwtrack.entrypoints.cli.adapters.account_presenters as account_presenters

    console = build_console(ConsoleSettings(record=True))
    presenter = RichAccountCreationPresenter(
        console,
        cast(FetchService, FakeTaggedAccountCreationFetchService()),
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
    monkeypatch.setattr(
        account_presenters,
        "prompt_for_optional_tag_choices",
        lambda *args, **kwargs: [2, 1, 2],
    )

    data = presenter.collect_account_data()

    assert data is not None
    assert data.tag_ids == [2, 1]
