"""
Rich-based presenters for account-related use cases.
"""

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from nwtrack.application.dto import AccountUpdateData, NewAccountData
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account, Balance, Category, Currency, Status
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.ui.prompts import (
    prompt_for_account_description,
    prompt_for_account_name,
    prompt_for_balance_amount,
    prompt_for_category_choice,
    prompt_for_currency_choice,
    prompt_for_month,
    prompt_for_optional_institution_choice,
    prompt_for_optional_tag_choices,
    prompt_for_status_choice,
    prompt_to_confirm_action,
)
from nwtrack.entrypoints.cli.ui.renderers import (
    build_accounts_table,
    build_currencies_table,
    build_indexed_categories_table,
    build_indexed_institutions_table,
    build_indexed_tags_table,
    build_status_table,
    render_account_data,
    render_new_account_info,
)


class RichAccountListPresenter:
    """Rich-based implementation of AccountListPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def display_accounts(
        self,
        accounts: list[Account],
        active_only: bool = True,
    ) -> None:
        """Display accounts table using Rich.

        Args:
            accounts: List of accounts to display
            active_only: Whether only active accounts are shown
        """
        title_prefix = "Active" if active_only else "All"
        table = build_accounts_table(accounts, title_prefix, show_institution=True)
        self._console.print(table)


class RichAccountCreationPresenter:
    """Rich-based implementation of AccountCreationPresenter."""

    def __init__(self, console: Console, fetcher: FetchService) -> None:
        self._console = console
        self._fetcher = fetcher
        self._selected_institution_name = "None"
        self._selected_tag_names = "None"

    def show_header(self) -> None:
        """Display workflow header using Rich."""
        self._console.rule("[header]Account Creation[/header]")

    def display_accounts(
        self,
        accounts: list[Account],
        active_only: bool = True,
    ) -> None:
        """Display existing accounts table.

        Args:
            accounts: List of accounts to display
            active_only: Whether only active accounts are shown
        """
        title_prefix = "Active" if active_only else "All"
        table = build_accounts_table(accounts, title_prefix, show_institution=True)
        self._console.print(table)

    def collect_account_data(self) -> NewAccountData | None:
        """Interactively collect all account data from user.

        Returns:
            NewAccountData or None if cancelled by user
        """
        try:
            return NewAccountData(
                institution_id=self._collect_institution_id(),
                tag_ids=self._collect_tag_ids(),
                account_name=self._collect_account_name(),
                description=self._collect_description(),
                category_name=self._collect_category_name(),
                currency_code=self._collect_currency_code(),
                status=self._collect_status(),
                initial_month=self._collect_initial_month(),
                initial_amount=self._collect_initial_balance(),
            )
        except KeyboardInterrupt:
            return None

    def _collect_account_name(self) -> str:
        """Collect account name from user."""
        while True:
            name = prompt_for_account_name(self._console)
            if name.lower() == "q":
                raise KeyboardInterrupt("Quit while collecting account name.")
            if name:
                return name
            self._console.print(
                "[validation]Account name cannot be empty.[/validation]"
                " Please try again."
            )

    def _collect_description(self) -> str:
        """Collect account description from user."""
        description = prompt_for_account_description(self._console)
        if description.lower() == "q":
            raise KeyboardInterrupt("Quit while collecting description.")
        return description

    def _collect_category_name(self) -> str:
        """Collect category selection from user."""
        categories = self._fetcher.get_all_categories()
        table = build_indexed_categories_table(categories)
        self._console.print(table)
        n_categories = len(categories)
        choice = prompt_for_category_choice(self._console, n_categories)
        if choice == 0:
            raise KeyboardInterrupt("Quit while collecting category name.")
        return categories[choice - 1].name

    def _collect_currency_code(self) -> str:
        """Collect currency selection from user."""
        currencies = self._fetcher.get_all_currencies()
        table = build_currencies_table(currencies)
        self._console.print(table)
        n_currencies = len(currencies)
        choice = prompt_for_currency_choice(self._console, n_currencies)
        if choice == 0:
            raise KeyboardInterrupt("Quit while collecting currency code.")
        return currencies[choice - 1].code

    def _collect_status(self) -> Status:
        """Collect status selection from user."""
        status_options = [Status.ACTIVE, Status.INACTIVE]
        table = build_status_table(status_options)
        self._console.print(table)
        choice = prompt_for_status_choice(self._console, len(status_options))
        if choice == 0:
            raise KeyboardInterrupt("Quit while collecting account status.")
        return status_options[choice - 1]

    def _collect_institution_id(self) -> int | None:
        """Collect optional institution selection from user."""
        institutions = self._fetcher.get_all_institutions()
        if not institutions:
            self._selected_institution_name = "None"
            self._console.print(
                "[info]No institutions available. Continuing with no institution "
                "assigned.[/info]"
            )
            return None

        self._console.print(build_indexed_institutions_table(institutions))
        choice = prompt_for_optional_institution_choice(
            self._console,
            len(institutions),
            default=0,
        )
        if choice is None:
            raise KeyboardInterrupt("Quit while collecting institution.")
        if choice == 0:
            self._selected_institution_name = "None"
            return None

        institution = institutions[choice - 1]
        self._selected_institution_name = institution.name
        return institution.id

    def _collect_tag_ids(self) -> list[int]:
        """Collect optional tag selections from user."""
        tags = self._fetcher.get_all_tags()
        if not tags:
            self._selected_tag_names = "None"
            self._console.print(
                "[info]No tags available. Continuing with no tags assigned.[/info]"
            )
            return []

        self._console.print(build_indexed_tags_table(tags))
        choices = prompt_for_optional_tag_choices(
            self._console,
            len(tags),
            default="0",
        )
        if choices is None:
            raise KeyboardInterrupt("Quit while collecting tags.")
        if not choices:
            self._selected_tag_names = "None"
            return []

        normalized_choices = sorted(set(choices))
        selected_tags = [tags[choice - 1] for choice in normalized_choices]
        self._selected_tag_names = ", ".join(tag.name for tag in selected_tags)
        return [tag.id for tag in selected_tags]

    def _collect_initial_month(self) -> Month:
        """Collect initial month from user."""
        return prompt_for_month(self._console)

    def _collect_initial_balance(self) -> int:
        """Collect initial balance amount from user."""
        return prompt_for_balance_amount(self._console)

    def show_preview_and_confirm(self, account: Account, balance: Balance) -> bool:
        """Show preview and get confirmation.

        Args:
            account: Account data to preview
            balance: Balance data to preview

        Returns:
            True if user confirms, False otherwise
        """
        self._console.print("\n[bold]New account data:[/bold]")
        render_new_account_info(
            self._console,
            account,
            balance,
            institution_name=self._selected_institution_name,
            tag_names=self._selected_tag_names,
        )
        return prompt_to_confirm_action(self._console, "Create account?")

    def show_cancellation(self, message: str = "") -> None:
        """Display cancellation message.

        Args:
            message: Optional additional context
        """
        msg = "[cancel]Account creation cancelled.[/cancel]"
        if message:
            msg += f" {message}"
        self._console.print(msg)

    def show_error(self, message: str) -> None:
        """Display error message.

        Args:
            message: Error message to display
        """
        self._console.print(f"[error]{message}[/error]")

    def show_success(
        self,
        accounts: list[Account],
    ) -> None:
        """Display success message and updated accounts list.

        Args:
            accounts: Updated list of all accounts
        """
        self._console.print("[success]Account created successfully.[/success]")
        self.display_accounts(accounts, active_only=False)


class RichAccountUpdatePresenter:
    """Rich-based implementation of AccountUpdatePresenter."""

    def __init__(self, console: Console, fetcher: FetchService) -> None:
        self._console = console
        self._fetcher = fetcher
        self._prompt = Prompt(console=console)
        self._int_prompt = IntPrompt(console=console)
        self._confirm = Confirm(console=console)
        self._selected_institution_name = "None"
        self._selected_tag_names = "None"

    def show_header(self) -> None:
        """Display workflow header using Rich."""
        self._console.rule("[header]Update Account Info[/header]")

    def display_accounts(
        self,
        accounts: list[Account],
        active_only: bool = False,
    ) -> None:
        """Display accounts table.

        Args:
            accounts: List of accounts to display
            active_only: Whether only active accounts are shown
        """
        title_prefix = "Active" if active_only else "All"
        table = build_accounts_table(accounts, title_prefix, show_institution=True)
        self._console.print(table)

    def select_account(self) -> int | None:
        """Prompt user to select an account to update by ID.

        Returns:
            Account ID or None if cancelled
        """
        while True:
            account_id = self._int_prompt.ask(
                "Enter [bold]account ID[/bold] to update or '0' to quit",
                default=0,
            )
            if account_id == 0:
                return None
            # Validate account exists
            account = self._fetcher.get_account_by_id(account_id)
            if account:
                return account_id
            else:
                self.show_account_not_found(account_id)

    def show_account_not_found(self, account_id: int) -> None:
        """Display error when account ID is not found.

        Args:
            account_id: The account ID that was not found
        """
        self._console.print(
            f"[validation]Account ID {account_id} not found.[/validation]"
            " Please try again."
        )

    def collect_updated_data(
        self, current_account: Account
    ) -> AccountUpdateData | None:
        """Interactively collect updated account data with current values as defaults.

        Args:
            current_account: Current account data to use as defaults

        Returns:
            Updated Account or None if cancelled by user
        """
        self._console.print(
            f"Updating account [bold]{current_account.name}[/bold] "
            f"(ID: {current_account.id})"
        )

        try:
            new_institution_id = self._collect_institution_id(
                default=current_account.institution_id
            )
            new_tag_ids = self._collect_tag_ids(current_account)
            new_name = self._collect_account_name(default=current_account.name)
            new_description = self._collect_description(
                default=current_account.description
            )
            new_category_name = self._collect_category_name(
                default=current_account.category_name
            )
            new_currency_code = self._collect_currency_code(
                default=current_account.currency_code
            )
            new_status = self._collect_status(default=current_account.status)

            return AccountUpdateData(
                account_id=current_account.id,
                account_name=new_name,
                description=new_description,
                category_name=new_category_name,
                currency_code=new_currency_code,
                institution_id=new_institution_id,
                status=new_status,
                tag_ids=new_tag_ids,
            )
        except KeyboardInterrupt:
            return None

    def _collect_account_name(self, default: str = "") -> str:
        """Collect account name from user."""
        while True:
            name = self._prompt.ask(
                "Enter [bold]account name[/bold] or 'q' to quit",
                default=default,
            ).strip()
            if name.lower() == "q":
                raise KeyboardInterrupt("Quit while collecting account name.")
            if name:
                return name
            self._console.print(
                "[validation]Account name cannot be empty.[/validation]"
                " Please try again."
            )

    def _collect_description(self, default: str = "") -> str:
        """Collect account description from user."""
        description = self._prompt.ask(
            "Enter optional [bold]description[/bold] or 'q' to quit",
            default=default,
        ).strip()
        if description.lower() == "q":
            raise KeyboardInterrupt("Quit while collecting description.")
        return description

    def _collect_category_name(self, default: str = "") -> str:
        """Collect category selection from user."""
        categories = self._fetcher.get_all_categories()

        # Find default index
        default_index = 0
        if default:
            default_index = next(
                (i + 1 for i, cat in enumerate(categories) if cat.name == default), 0
            )

        table = self._build_categories_table(categories)
        self._console.print(table)

        while True:
            choice = self._int_prompt.ask(
                "Enter [bold]category index[/bold] or '0' to quit",
                default=default_index,
                choices=[str(i) for i in range(len(categories) + 1)],
            )
            if choice == 0:
                raise KeyboardInterrupt("Quit while collecting category name.")
            index = choice - 1
            if 0 <= index < len(categories):
                return categories[index].name
            else:
                self._console.print(
                    "[validation]Invalid choice.[/validation] Please try again."
                )

    def _build_categories_table(self, categories: list[Category]) -> Table:
        """Build categories selection table."""
        table = Table(title="Categories")
        table.add_column("Index", justify="right", style="col.id", no_wrap=True)
        table.add_column("Name", style="col.name")
        table.add_column("Side", style="col.side")
        for k, category in enumerate(categories):
            table.add_row(
                str(k + 1),
                category.name,
                category.side.value,
            )
        return table

    def _collect_currency_code(self, default: str = "") -> str:
        """Collect currency selection from user."""
        currencies = self._fetcher.get_all_currencies()

        # Find default index
        default_index = 1
        if default:
            default_index = next(
                (i + 1 for i, cur in enumerate(currencies) if cur.code == default), 1
            )

        table = self._build_currencies_table(currencies)
        self._console.print(table)

        while True:
            choice = self._int_prompt.ask(
                "Enter [bold]currency index[/bold] or '0' to quit",
                default=default_index,
                choices=[str(i) for i in range(len(currencies) + 1)],
            )
            if choice == 0:
                raise KeyboardInterrupt("Quit while collecting currency code.")
            index = choice - 1
            if 0 <= index < len(currencies):
                return currencies[index].code
            else:
                self._console.print(
                    "[validation]Invalid choice.[/validation] Please try again."
                )

    def _build_currencies_table(self, currencies: list[Currency]) -> Table:
        """Build currencies selection table."""
        table = Table(title="Currencies")
        table.add_column("Index", justify="right", style="col.id", no_wrap=True)
        table.add_column("Code", style="col.code")
        table.add_column("Description", style="col.desc")
        for k, currency in enumerate(currencies):
            table.add_row(
                str(k + 1),
                currency.code,
                currency.description,
            )
        return table

    def _collect_status(self, default: Status = Status.ACTIVE) -> Status:
        """Collect status selection from user."""
        status_options = [Status.ACTIVE, Status.INACTIVE]
        default_index = status_options.index(default) + 1

        table = self._build_status_table(status_options)
        self._console.print(table)

        choice = self._int_prompt.ask(
            "Select [bold]account status[/bold] by index or '0' to quit",
            default=default_index,
            choices=["0", "1", "2"],
        )
        if choice == 0:
            raise KeyboardInterrupt("Quit while collecting account status.")
        index = choice - 1
        return status_options[index]

    def _collect_institution_id(self, default: int | None = None) -> int | None:
        """Collect optional institution selection from user."""
        institutions = self._fetcher.get_all_institutions()
        if not institutions:
            self._selected_institution_name = "None"
            self._console.print(
                "[info]No institutions available. Continuing with no institution "
                "assigned.[/info]"
            )
            return None

        default_index = 0
        if default is not None:
            default_index = next(
                (
                    index
                    for index, institution in enumerate(institutions, start=1)
                    if institution.id == default
                ),
                0,
            )
        self._console.print(build_indexed_institutions_table(institutions))
        choice = prompt_for_optional_institution_choice(
            self._console,
            len(institutions),
            default=default_index,
        )
        if choice is None:
            raise KeyboardInterrupt("Quit while collecting institution.")
        if choice == 0:
            self._selected_institution_name = "None"
            return None

        institution = institutions[choice - 1]
        self._selected_institution_name = institution.name
        return institution.id

    def _collect_tag_ids(self, current_account: Account) -> list[int]:
        """Collect optional replacement tag selections from user."""
        tags = self._fetcher.get_all_tags()
        if not tags:
            self._selected_tag_names = "None"
            self._console.print(
                "[info]No tags available. Continuing with no tags assigned.[/info]"
            )
            return []

        selected_tag_ids = {tag.id for tag in current_account.tags}
        default_choices = [
            str(index)
            for index, tag in enumerate(tags, start=1)
            if tag.id in selected_tag_ids
        ]
        default_value = ",".join(default_choices) if default_choices else "0"

        self._console.print(build_indexed_tags_table(tags))
        choices = prompt_for_optional_tag_choices(
            self._console,
            len(tags),
            default=default_value,
        )
        if choices is None:
            raise KeyboardInterrupt("Quit while collecting tags.")
        if not choices:
            self._selected_tag_names = "None"
            return []

        normalized_choices = sorted(set(choices))
        selected_tags = [tags[choice - 1] for choice in normalized_choices]
        self._selected_tag_names = ", ".join(tag.name for tag in selected_tags)
        return [tag.id for tag in selected_tags]

    def _build_status_table(self, status_options: list[Status]) -> Table:
        """Build status selection table."""
        table = Table(title="Status Options")
        table.add_column("Index", justify="right", style="col.id", no_wrap=True)
        table.add_column("Status", style="col.status")
        for k, status in enumerate(status_options):
            table.add_row(
                str(k + 1),
                status.value,
            )
        return table

    def show_preview_and_confirm(self, updated_account: AccountUpdateData) -> bool:
        """Show preview and get confirmation.

        Args:
            updated_account: Updated account data to preview

        Returns:
            True if user confirms, False otherwise
        """
        self._console.print("[bold]Updated account data[/bold]")
        preview_account = Account(
            name=updated_account.account_name,
            description=updated_account.description,
            category_name=updated_account.category_name,
            currency_code=updated_account.currency_code,
            institution_id=updated_account.institution_id,
            status=updated_account.status,
        )
        preview_account.id = updated_account.account_id
        render_account_data(
            self._console,
            preview_account,
            institution_name=self._selected_institution_name,
        )
        return self._confirm.ask("Proceed with update", default=False)

    def show_cancellation(self, message: str = "") -> None:
        """Display cancellation message.

        Args:
            message: Optional additional context
        """
        msg = "[cancel]Account update cancelled.[/cancel]"
        if message:
            msg += f" {message}"
        self._console.print(msg)

    def show_error(self, message: str) -> None:
        """Display error message.

        Args:
            message: Error message to display
        """
        self._console.print(f"[error]{message}[/error]")

    def show_success(self) -> None:
        """Display success message."""
        self._console.print("\n[success]Account updated successfully.[/success]")
