"""Presenter tests for account CLI views."""

from typing import cast

from rich.prompt import IntPrompt, Prompt

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
    RichAccountUpdatePresenter,
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

    def get_all_tags(self) -> list:
        return []


class FakeTaggedAccountCreationFetchService(FakeAccountCreationFetchService):
    """Fetch service stub with tags for create-workflow tests."""

    def get_all_tags(self) -> list[Tag]:
        first = Tag(name="core", description="Core holding")
        first.id = 1
        second = Tag(name="liquid", description="Quick access")
        second.id = 2
        return [first, second]


def test_account_list_presenter_renders_institution_and_tags_columns() -> None:
    """Account list presenter should show assigned and unassigned tags cleanly."""
    console = build_console(ConsoleSettings(record=True))
    presenter = RichAccountListPresenter(console)

    category = Category(name="checking", side=Side.ASSET)
    institution = Institution(name="Chase", description="Primary bank")
    institution.id = 1
    first_tag = Tag(name="core", description="Core holding")
    first_tag.id = 1
    second_tag = Tag(name="liquid", description="Quick access")
    second_tag.id = 2

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
    assigned_account.tags = [first_tag, second_tag]

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
    assert "Tags" in output
    assert "Chase" in output
    header_line = next(line for line in output.splitlines() if "Institution" in line)
    assert header_line.index("Institution") < header_line.index("Name")
    assert header_line.index("Tags") < header_line.index("Name")
    assert "core, liquid" in output
    assert "bank_2_savings" in output
    assert "None" not in output


def test_account_creation_presenter_exposes_tag_ids_field(monkeypatch) -> None:
    """Account creation data should now carry tag selections."""
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
    assert "tag_ids" in data.__dataclass_fields__
    assert data.tag_ids == []
    output = console.export_text()
    assert (
        "No institutions available. Continuing with no institution assigned."
        in output
    )
    assert "No tags available. Continuing with no tags assigned." in output


def test_account_creation_presenter_collects_selected_tag_ids(monkeypatch) -> None:
    """Account creation should collect selected tag IDs after institution."""
    import nwtrack.entrypoints.cli.adapters.account_presenters as account_presenters

    console = build_console(ConsoleSettings(record=True))
    presenter = RichAccountCreationPresenter(
        console,
        cast(FetchService, FakeTaggedAccountCreationFetchService()),
    )

    monkeypatch.setattr(
        account_presenters,
        "prompt_for_optional_tag_choices",
        lambda *args, **kwargs: [2, 1],
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
    assert data.tag_ids == [1, 2]
    output = console.export_text()
    assert "Tags" in output


def test_account_update_presenter_uses_current_tags_as_default(monkeypatch) -> None:
    """Account update should seed tag replacement with current selections."""
    import nwtrack.entrypoints.cli.adapters.account_presenters as account_presenters

    console = build_console(ConsoleSettings(record=True))
    presenter = RichAccountUpdatePresenter(
        console,
        cast(FetchService, FakeTaggedAccountCreationFetchService()),
    )

    current_account = Account(
        name="cash_account",
        description="Cash account",
        category_name="checking",
        currency_code="USD",
        institution_id=None,
        status=Status.ACTIVE,
    )
    current_account.id = 10
    current_account.tags = FakeTaggedAccountCreationFetchService().get_all_tags()

    captured_default: dict[str, str] = {}

    def capture_tags(*args, **kwargs) -> list[int]:
        captured_default["value"] = kwargs["default"]
        return [1, 2]

    prompt_values = iter(["cash_account", "Cash account"])
    int_values = iter([1, 1, 1])

    monkeypatch.setattr(
        account_presenters,
        "prompt_for_optional_tag_choices",
        capture_tags,
    )
    monkeypatch.setattr(Prompt, "ask", lambda *args, **kwargs: next(prompt_values))
    monkeypatch.setattr(IntPrompt, "ask", lambda *args, **kwargs: next(int_values))

    data = presenter.collect_updated_data(current_account)

    assert data is not None
    assert captured_default["value"] == "1,2"
    assert data.tag_ids == [1, 2]
