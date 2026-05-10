"""Presenter tests for tag CLI views."""

from nwtrack.application.dto import TagListItem
from nwtrack.domain.models import Tag
from nwtrack.entrypoints.cli.adapters.tag_presenters import (
    RichTagCreationPresenter,
    RichTagDeletePresenter,
    RichTagListPresenter,
    RichTagUpdatePresenter,
)
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


def test_create_presenter_renders_success_message() -> None:
    """Tag create presenter should confirm successful creation."""
    console = build_console(ConsoleSettings(record=True, width=120))
    presenter = RichTagCreationPresenter(console)

    tag = Tag(name="liquid", description="Quick access")
    tag.id = 2
    presenter.show_success(
        "liquid",
        [TagListItem(tag=tag, account_count=0)],
    )

    output = console.export_text()
    assert "created successfully" in output
    assert "liquid" in output


def test_update_presenter_shows_duplicate_error() -> None:
    """Update presenter should explain when a normalized duplicate exists."""
    console = build_console(ConsoleSettings(record=True, width=120))
    presenter = RichTagUpdatePresenter(console)

    presenter.show_duplicate_error("liquid")

    output = console.export_text()
    assert "Tag name 'liquid' already exists." in output


def test_delete_presenter_shows_blocked_message() -> None:
    """Delete presenter should explain when linked accounts block removal."""
    console = build_console(ConsoleSettings(record=True, width=120))
    presenter = RichTagDeletePresenter(console)

    tag = Tag(name="liquid", description="Quick access")
    tag.id = 3
    presenter.show_delete_blocked(tag, account_count=1)

    output = console.export_text()
    assert "Cannot delete tag 'liquid'." in output
    assert "1 account(s)" in output
