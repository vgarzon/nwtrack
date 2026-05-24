"""Rich-based presenters for admin use cases."""

from rich.console import Console
from rich.prompt import Confirm, IntPrompt
from rich.table import Table

from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account, Institution
from nwtrack.entrypoints.cli.ui.renderers import build_indexed_institutions_table


def _build_unassigned_accounts_table(accounts: list[Account]) -> Table:
    table = Table(title="Accounts Without Institution")
    table.add_column("ID", justify="right", style="col.id", no_wrap=True)
    table.add_column("Name", style="col.name")
    table.add_column("Category", style="col.category")
    table.add_column("Currency", style="col.code")
    table.add_column("Status", style="col.status")
    for account in accounts:
        category = account.category
        table.add_row(
            str(account.id),
            account.name,
            category.name if category else "",
            account.currency_code,
            account.status.value,
        )
    return table


class RichAdminListUnassignedPresenter:
    """Rich implementation of AdminListUnassignedPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def display_unassigned(self, accounts: list[Account]) -> None:
        self._console.print(_build_unassigned_accounts_table(accounts))
        self._console.print(
            f"[info]{len(accounts)} account(s) have no institution assigned.[/info]"
        )

    def show_empty_state(self) -> None:
        self._console.print(
            "[success]All accounts have an institution assigned.[/success]"
        )


class RichAdminAssignInstitutionsPresenter:
    """Rich implementation of AdminAssignInstitutionsPresenter."""

    def __init__(self, console: Console, fetcher: FetchService) -> None:
        self._console = console
        self._fetcher = fetcher
        self._int_prompt = IntPrompt(console=console)
        self._confirm = Confirm(console=console)

    def show_header(self) -> None:
        self._console.rule("[header]Assign Institutions to Accounts[/header]")

    def display_unassigned(self, accounts: list[Account]) -> None:
        self._console.print(_build_unassigned_accounts_table(accounts))

    def show_empty_state(self) -> None:
        self._console.print(
            "[success]All accounts have an institution assigned.[/success]"
        )

    def select_account(self, accounts: list[Account]) -> int | None:
        account_ids = {a.id for a in accounts}
        while True:
            account_id = self._int_prompt.ask(
                "Enter [bold]account ID[/bold] to assign an institution, "
                "or '0' to finish",
                default=0,
            )
            if account_id == 0:
                return None
            if account_id in account_ids:
                return account_id
            self._console.print(
                f"[validation]Account ID {account_id} is not in the unassigned list."
                "[/validation] Please try again."
            )

    def select_institution(self, institutions: list[Institution]) -> int | None:
        self._console.print(build_indexed_institutions_table(institutions))
        while True:
            choice = self._int_prompt.ask(
                "Enter [bold]institution index[/bold] or '0' to cancel",
                default=0,
                choices=[str(i) for i in range(len(institutions) + 1)],
            )
            if choice == 0:
                return None
            index = choice - 1
            if 0 <= index < len(institutions):
                return institutions[index].id
            self._console.print(
                "[validation]Invalid choice.[/validation] Please try again."
            )

    def show_no_institutions_error(self) -> None:
        self._console.print(
            "[error]No institutions found.[/error] "
            "Create institutions first with [bold]nwtrack institutions create[/bold]."
        )

    def confirm_assignment(self, account: Account, institution: Institution) -> bool:
        self._console.print(
            f"Assign [bold]{institution.name}[/bold] to account "
            f"[bold]{account.name}[/bold] (ID: {account.id})?"
        )
        return self._confirm.ask("Confirm", default=False)

    def show_assignment_success(
        self, account: Account, institution: Institution
    ) -> None:
        self._console.print(
            f"[success]Assigned [bold]{institution.name}[/bold] to "
            f"[bold]{account.name}[/bold].[/success]"
        )

    def show_session_summary(self, assigned_count: int) -> None:
        if assigned_count == 0:
            self._console.print(
                "[info]No institutions were assigned this session.[/info]"
            )
        else:
            self._console.print(
                f"[success]{assigned_count} institution(s) assigned "
                "this session.[/success]"
            )
