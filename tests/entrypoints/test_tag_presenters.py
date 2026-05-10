"""Presenter tests for tag CLI views."""

from nwtrack.application.dto import TagListItem
from nwtrack.domain.models import Tag
from nwtrack.entrypoints.cli.adapters.tag_presenters import RichTagListPresenter
from nwtrack.entrypoints.cli.ui.console import ConsoleSettings, build_console


def test_list_presenter_displays_empty_state() -> None:
    """Tag list presenter should render a readable empty state."""
    console = build_console(ConsoleSettings(record=True, width=120))
    presenter = RichTagListPresenter(console)

    presenter.display_tags([])

    output = console.export_text()
    assert "No tags found." in output


def test_list_presenter_displays_usage_counts() -> None:
    """Tag list presenter should render the Accounts column."""
    console = build_console(ConsoleSettings(record=True, width=120))
    presenter = RichTagListPresenter(console)

    tag = Tag(name="liquid", description="Quick access")
    tag.id = 1
    presenter.display_tags([TagListItem(tag=tag, account_count=2)])

    output = console.export_text()
    assert "Tags" in output
    assert "liquid" in output
    assert "Accounts" in output
    assert "2" in output
