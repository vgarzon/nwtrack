"""Rich-based presenters for tag-related use cases."""

from rich.console import Console
from rich.prompt import Confirm

from nwtrack.application.dto import TagListItem
from nwtrack.domain.models import Tag
from nwtrack.entrypoints.cli.ui.prompts import (
    prompt_for_tag_description,
    prompt_for_tag_id,
    prompt_for_tag_name,
    prompt_to_confirm_action,
)
from nwtrack.entrypoints.cli.ui.renderers import build_tags_table, render_tag_data


class RichTagListPresenter:
    """Rich-based implementation of TagListPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def display_tags(self, tags: list[TagListItem]) -> None:
        """Display tags table using Rich."""
        if not tags:
            self._console.print("[info]No tags found.[/info]")
            return
        self._console.print(build_tags_table(tags))


class RichTagCreationPresenter:
    """Rich-based implementation of TagCreationPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def show_header(self) -> None:
        self._console.rule("[header]Create Tag[/header]")

    def display_tags(self, tags: list[TagListItem]) -> None:
        RichTagListPresenter(self._console).display_tags(tags)

    def collect_tag_data(self) -> Tag | None:
        try:
            name = self._collect_name()
            description = self._collect_description()
            return Tag(name=name, description=description or None)
        except KeyboardInterrupt:
            return None

    def _collect_name(self, default: str = "") -> str:
        name = prompt_for_tag_name(self._console, default=default)
        if name.lower() == "q":
            raise KeyboardInterrupt("Quit while collecting tag name.")
        return name

    def _collect_description(self, default: str = "") -> str:
        description = prompt_for_tag_description(self._console, default=default)
        if description.lower() == "q":
            raise KeyboardInterrupt("Quit while collecting tag description.")
        return description

    def show_duplicate_error(self, tag_name: str) -> None:
        self._console.print(
            f"[error]Error:[/error] Tag name [bold]'{tag_name}'[/bold] already exists."
        )

    def show_empty_name_error(self) -> None:
        self._console.print(
            "[validation]Tag name cannot be empty after normalization.[/validation]"
        )

    def show_preview_and_confirm(self, tag: Tag) -> bool:
        self._console.print("\n[bold]Tag to be created:[/bold]")
        render_tag_data(self._console, tag)
        return prompt_to_confirm_action(self._console, "Create tag?")

    def show_cancellation(self) -> None:
        self._console.print("[cancel]Tag creation cancelled.[/cancel]")

    def show_error(self, message: str) -> None:
        self._console.print(f"[error]{message}[/error]")

    def show_success(self, tag_name: str, tags: list[TagListItem]) -> None:
        self._console.print(
            f"[success]Tag '{tag_name}' created successfully.[/success]"
        )
        self.display_tags(tags)


class RichTagUpdatePresenter:
    """Rich-based implementation of TagUpdatePresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console
        self._confirm = Confirm(console=console)

    def show_header(self) -> None:
        self._console.rule("[header]Update Tag[/header]")

    def display_tags(self, tags: list[TagListItem]) -> None:
        RichTagListPresenter(self._console).display_tags(tags)

    def show_no_tags(self) -> None:
        self._console.print("[info]No tags available to update.[/info]")

    def select_tag(self) -> int | None:
        return prompt_for_tag_id(self._console)

    def show_tag_not_found(self, tag_id: int) -> None:
        self._console.print(
            f"[validation]Tag ID {tag_id} not found.[/validation] Please try again."
        )

    def collect_updated_data(self, current_tag: Tag) -> Tag | None:
        self._console.print(
            f"Updating tag [bold]{current_tag.name}[/bold] (ID: {current_tag.id})"
        )
        try:
            name = self._collect_name(default=current_tag.name)
            description = self._collect_description(default=current_tag.description or "")
            tag = Tag(name=name, description=description or None)
            tag.id = current_tag.id
            return tag
        except KeyboardInterrupt:
            return None

    def _collect_name(self, default: str = "") -> str:
        name = prompt_for_tag_name(self._console, default=default)
        if name.lower() == "q":
            raise KeyboardInterrupt("Quit while collecting tag name.")
        return name

    def _collect_description(self, default: str = "") -> str:
        description = prompt_for_tag_description(self._console, default=default)
        if description.lower() == "q":
            raise KeyboardInterrupt("Quit while collecting tag description.")
        return description

    def show_duplicate_error(self, tag_name: str) -> None:
        self._console.print(
            f"[error]Error:[/error] Tag name [bold]'{tag_name}'[/bold] already exists."
        )

    def show_empty_name_error(self) -> None:
        self._console.print(
            "[validation]Tag name cannot be empty after normalization.[/validation]"
        )

    def show_preview_and_confirm(self, tag: Tag) -> bool:
        self._console.print("[bold]Updated tag data[/bold]")
        render_tag_data(self._console, tag)
        return self._confirm.ask("Proceed with update", default=False)

    def show_cancellation(self, message: str = "") -> None:
        full_message = "[cancel]Tag update cancelled.[/cancel]"
        if message:
            full_message += f" {message}"
        self._console.print(full_message)

    def show_error(self, message: str) -> None:
        self._console.print(f"[error]{message}[/error]")

    def show_success(self, tags: list[TagListItem]) -> None:
        self._console.print("\n[success]Tag updated successfully.[/success]")
        self.display_tags(tags)
