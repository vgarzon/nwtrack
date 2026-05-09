"""Presenter tests for institution CLI views."""

from nwtrack.application.dto import InstitutionListItem
from nwtrack.domain.models import Institution
from nwtrack.entrypoints.cli.adapters.institution_presenters import (
    RichInstitutionCreationPresenter,
    RichInstitutionDeletePresenter,
    RichInstitutionListPresenter,
)
from nwtrack.entrypoints.cli.ui.console import ConsoleSettings, build_console


def test_list_presenter_displays_usage_counts() -> None:
    """Institution list presenter should render the Accounts column."""
    console = build_console(ConsoleSettings(record=True, width=120))
    presenter = RichInstitutionListPresenter(console)

    institution = Institution(name="Chase", description="Primary bank")
    institution.id = 1
    presenter.display_institutions(
        [InstitutionListItem(institution=institution, account_count=2)]
    )

    output = console.export_text()
    assert "Institutions" in output
    assert "Chase" in output
    assert "Accounts" in output
    assert "2" in output


def test_create_presenter_renders_success_message() -> None:
    """Institution create presenter should confirm successful creation."""
    console = build_console(ConsoleSettings(record=True, width=120))
    presenter = RichInstitutionCreationPresenter(console)

    institution = Institution(name="Fidelity", description="Brokerage")
    institution.id = 2
    presenter.show_success(
        "Fidelity",
        [InstitutionListItem(institution=institution, account_count=0)],
    )

    output = console.export_text()
    assert "created successfully" in output
    assert "Fidelity" in output


def test_delete_presenter_shows_blocked_message() -> None:
    """Delete presenter should explain when linked accounts block removal."""
    console = build_console(ConsoleSettings(record=True, width=120))
    presenter = RichInstitutionDeletePresenter(console)

    institution = Institution(name="Vanguard", description="Brokerage")
    institution.id = 3
    presenter.show_delete_blocked(institution, account_count=1)

    output = console.export_text()
    assert "Cannot delete institution 'Vanguard'." in output
    assert "1 account(s)" in output
