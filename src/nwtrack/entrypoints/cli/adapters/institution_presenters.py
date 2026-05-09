"""Rich-based presenters for institution-related use cases."""

from rich.console import Console
from rich.prompt import Confirm

from nwtrack.application.dto import InstitutionListItem
from nwtrack.domain.models import Institution
from nwtrack.entrypoints.cli.ui.prompts import (
    prompt_for_institution_description,
    prompt_for_institution_id,
    prompt_for_institution_name,
    prompt_to_confirm_action,
)
from nwtrack.entrypoints.cli.ui.renderers import (
    build_institutions_table,
    render_institution_data,
)


class RichInstitutionListPresenter:
    """Rich-based implementation of InstitutionListPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def display_institutions(self, institutions: list[InstitutionListItem]) -> None:
        """Display institutions table using Rich."""
        if not institutions:
            self._console.print("[info]No institutions found.[/info]")
            return
        self._console.print(build_institutions_table(institutions))


class RichInstitutionCreationPresenter:
    """Rich-based implementation of InstitutionCreationPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def show_header(self) -> None:
        self._console.rule("[header]Create Institution[/header]")

    def display_institutions(self, institutions: list[InstitutionListItem]) -> None:
        RichInstitutionListPresenter(self._console).display_institutions(institutions)

    def collect_institution_data(self) -> Institution | None:
        try:
            name = self._collect_name()
            description = self._collect_description()
            return Institution(name=name, description=description or None)
        except KeyboardInterrupt:
            return None

    def _collect_name(self, default: str = "") -> str:
        while True:
            name = prompt_for_institution_name(self._console, default=default)
            if name.lower() == "q":
                raise KeyboardInterrupt("Quit while collecting institution name.")
            if name:
                return name
            self._console.print(
                "[validation]Institution name cannot be empty.[/validation]"
                " Please try again."
            )

    def _collect_description(self, default: str = "") -> str:
        description = prompt_for_institution_description(
            self._console, default=default
        )
        if description.lower() == "q":
            raise KeyboardInterrupt("Quit while collecting institution description.")
        return description

    def show_duplicate_error(self, institution_name: str) -> None:
        self._console.print(
            f"[error]Error:[/error] Institution name "
            f"[bold]'{institution_name}'[/bold] already exists."
        )

    def show_preview_and_confirm(self, institution: Institution) -> bool:
        self._console.print("\n[bold]Institution to be created:[/bold]")
        render_institution_data(self._console, institution)
        return prompt_to_confirm_action(self._console, "Create institution?")

    def show_cancellation(self) -> None:
        self._console.print("[cancel]Institution creation cancelled.[/cancel]")

    def show_error(self, message: str) -> None:
        self._console.print(f"[error]{message}[/error]")

    def show_success(
        self,
        institution_name: str,
        institutions: list[InstitutionListItem],
    ) -> None:
        self._console.print(
            f"[success]Institution '{institution_name}' created successfully.[/success]"
        )
        self.display_institutions(institutions)


class RichInstitutionUpdatePresenter:
    """Rich-based implementation of InstitutionUpdatePresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console
        self._confirm = Confirm(console=console)

    def show_header(self) -> None:
        self._console.rule("[header]Update Institution[/header]")

    def display_institutions(self, institutions: list[InstitutionListItem]) -> None:
        RichInstitutionListPresenter(self._console).display_institutions(institutions)

    def show_no_institutions(self) -> None:
        self._console.print("[info]No institutions available to update.[/info]")

    def select_institution(self) -> int | None:
        return prompt_for_institution_id(self._console)

    def show_institution_not_found(self, institution_id: int) -> None:
        self._console.print(
            f"[validation]Institution ID {institution_id} not found.[/validation]"
            " Please try again."
        )

    def collect_updated_data(
        self, current_institution: Institution
    ) -> Institution | None:
        self._console.print(
            f"Updating institution [bold]{current_institution.name}[/bold] "
            f"(ID: {current_institution.id})"
        )
        try:
            name = self._collect_name(default=current_institution.name)
            description = self._collect_description(
                default=current_institution.description or ""
            )
            institution = Institution(name=name, description=description or None)
            institution.id = current_institution.id
            return institution
        except KeyboardInterrupt:
            return None

    def _collect_name(self, default: str = "") -> str:
        while True:
            name = prompt_for_institution_name(self._console, default=default)
            if name.lower() == "q":
                raise KeyboardInterrupt("Quit while collecting institution name.")
            if name:
                return name
            self._console.print(
                "[validation]Institution name cannot be empty.[/validation]"
                " Please try again."
            )

    def _collect_description(self, default: str = "") -> str:
        description = prompt_for_institution_description(
            self._console, default=default
        )
        if description.lower() == "q":
            raise KeyboardInterrupt("Quit while collecting institution description.")
        return description

    def show_duplicate_error(self, institution_name: str) -> None:
        self._console.print(
            f"[error]Error:[/error] Institution name "
            f"[bold]'{institution_name}'[/bold] already exists."
        )

    def show_preview_and_confirm(self, institution: Institution) -> bool:
        self._console.print("[bold]Updated institution data[/bold]")
        render_institution_data(self._console, institution)
        return self._confirm.ask("Proceed with update", default=False)

    def show_cancellation(self, message: str = "") -> None:
        msg = "[cancel]Institution update cancelled.[/cancel]"
        if message:
            msg += f" {message}"
        self._console.print(msg)

    def show_error(self, message: str) -> None:
        self._console.print(f"[error]{message}[/error]")

    def show_success(self, institutions: list[InstitutionListItem]) -> None:
        self._console.print("\n[success]Institution updated successfully.[/success]")
        self.display_institutions(institutions)


class RichInstitutionDeletePresenter:
    """Rich-based implementation of InstitutionDeletePresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console
        self._confirm = Confirm(console=console)

    def show_header(self) -> None:
        self._console.rule("[header]Delete Institution[/header]")

    def display_institutions(self, institutions: list[InstitutionListItem]) -> None:
        RichInstitutionListPresenter(self._console).display_institutions(institutions)

    def show_no_institutions(self) -> None:
        self._console.print("[info]No institutions available to delete.[/info]")

    def select_institution(self) -> int | None:
        return prompt_for_institution_id(self._console)

    def show_institution_not_found(self, institution_id: int) -> None:
        self._console.print(
            f"[validation]Institution ID {institution_id} not found.[/validation]"
            " Please try again."
        )

    def show_preview_and_confirm(
        self, institution: Institution, account_count: int
    ) -> bool:
        self._console.print("[bold]Institution to be deleted:[/bold]")
        render_institution_data(self._console, institution, account_count=account_count)
        return self._confirm.ask("Proceed with delete", default=False)

    def show_delete_blocked(self, institution: Institution, account_count: int) -> None:
        self._console.print(
            f"[validation]Cannot delete institution '{institution.name}'.[/validation] "
            f"It is still linked to {account_count} account(s)."
        )

    def show_cancellation(self, message: str = "") -> None:
        msg = "[cancel]Institution delete cancelled.[/cancel]"
        if message:
            msg += f" {message}"
        self._console.print(msg)

    def show_error(self, message: str) -> None:
        self._console.print(f"[error]{message}[/error]")

    def show_success(self, institutions: list[InstitutionListItem]) -> None:
        self._console.print("\n[success]Institution deleted successfully.[/success]")
        self.display_institutions(institutions)
