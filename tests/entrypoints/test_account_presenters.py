"""Presenter tests for account CLI views."""

from nwtrack.domain.models import Account, Category, Institution, Side, Status
from nwtrack.entrypoints.cli.adapters.account_presenters import RichAccountListPresenter
from nwtrack.entrypoints.cli.ui.console import ConsoleSettings, build_console


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
