"""Account list screen and form modal for the nwtrack TUI."""

from collections.abc import Callable
from dataclasses import dataclass

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    SelectionList,
)
from textual.widgets.selection_list import Selection

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.infra.persistence.orm.models import (
    Account,
    Category,
    Institution,
    Status,
    Tag,
)


@dataclass
class AccountFormData:
    """Collected field values returned by AccountFormModal."""

    name: str
    description: str
    category_name: str
    institution_id: int | None
    currency_code: str
    status: Status
    tag_ids: list[int]


class AccountFormModal(ModalScreen[AccountFormData | None]):
    """Overlay modal for creating or editing an account.

    Pass account=None for create mode. Pass an existing account + tags for edit mode.
    Returns AccountFormData on confirm, None on cancel.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit", "Save"),
    ]

    DEFAULT_CSS = """
    AccountFormModal {
        align: center middle;
    }
    #account-form-container {
        width: 64;
        height: auto;
        max-height: 90%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
        overflow-y: auto;
    }
    #account-form-title {
        text-align: center;
        margin-bottom: 1;
    }
    #account-form-error {
        color: $error;
        margin-top: 1;
    }
    #account-form-hint {
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        categories: list[Category],
        institutions: list[Institution],
        currencies: list[str],
        all_tags: list[Tag],
        account: Account | None = None,
        current_tag_ids: list[int] | None = None,
    ) -> None:
        super().__init__()
        self._categories = categories
        self._institutions = institutions
        self._currencies = currencies
        self._all_tags = all_tags
        self._account = account
        self._current_tag_ids = set(current_tag_ids or [])
        self._edit_mode = account is not None

    def compose(self) -> ComposeResult:
        title = "Edit Account" if self._edit_mode else "Create Account"
        acc = self._account

        category_options = [(c.name, c.name) for c in self._categories]
        institution_options: list[tuple[str, str]] = [("(none)", "")]
        institution_options += [(i.name, str(i.id)) for i in self._institutions]
        currency_options = [(code, code) for code in self._currencies]
        status_options = [(s.value.capitalize(), s.value) for s in Status]

        tag_selections = [
            Selection(t.name, t.id, initial_state=(t.id in self._current_tag_ids))
            for t in self._all_tags
        ]

        with Vertical(id="account-form-container"):
            yield Label(title, id="account-form-title")
            yield Label("Name")
            yield Input(
                value=acc.name if acc else "",
                placeholder="Account name",
                id="input-name",
            )
            yield Label("Description")
            yield Input(
                value=acc.description if acc else "",
                placeholder="Description",
                id="input-desc",
            )
            yield Label("Category")
            yield Select(
                options=category_options,
                value=acc.category_name if acc else Select.NULL,
                prompt="Select category",
                allow_blank=True,
                id="select-category",
            )
            yield Label("Institution (optional)")
            yield Select(
                options=institution_options,
                value=str(acc.institution_id) if acc and acc.institution_id else "",
                prompt="Select institution",
                id="select-institution",
            )
            yield Label("Currency")
            yield Select(
                options=currency_options,
                value=acc.currency_code if acc else "USD",
                prompt="Select currency",
                id="select-currency",
            )
            if self._edit_mode:
                yield Label("Status")
                yield Select(
                    options=status_options,
                    value=acc.status.value if acc else Status.ACTIVE.value,
                    prompt="Select status",
                    id="select-status",
                )
            if self._all_tags:
                yield Label("Tags")
                yield SelectionList[int](*tag_selections, id="select-tags")
            yield Label("", id="account-form-error")
            yield Label("Ctrl+S to save", id="account-form-hint")
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#input-name", Input).focus()

    def action_submit(self) -> None:
        self._submit()

    def _submit(self) -> None:
        name = self.query_one("#input-name", Input).value.strip()
        description = self.query_one("#input-desc", Input).value.strip()
        category_select = self.query_one("#select-category", Select)
        currency_select = self.query_one("#select-currency", Select)
        error = self.query_one("#account-form-error", Label)

        if not name:
            error.update("Name is required")
            self.query_one("#input-name", Input).focus()
            return
        if category_select.value is Select.NULL:
            error.update("Category is required")
            category_select.focus()
            return
        if currency_select.value is Select.NULL:
            error.update("Currency is required")
            currency_select.focus()
            return

        institution_select = self.query_one("#select-institution", Select)
        inst_raw = institution_select.value
        institution_id: int | None = (
            int(str(inst_raw)) if inst_raw and inst_raw is not Select.NULL else None
        )

        status = Status.ACTIVE
        if self._edit_mode:
            status_select = self.query_one("#select-status", Select)
            if status_select.value is not Select.NULL:
                status = Status(str(status_select.value))
            else:
                status = Status.ACTIVE

        tag_ids: list[int] = []
        if self._all_tags:
            tag_ids = list(self.query_one("#select-tags", SelectionList).selected)

        self.dismiss(
            AccountFormData(
                name=name,
                description=description,
                category_name=str(category_select.value),
                institution_id=institution_id,
                currency_code=str(currency_select.value),
                status=status,
                tag_ids=tag_ids,
            )
        )

    def action_cancel(self) -> None:
        self.dismiss(None)


class AccountsListScreen(Screen):
    """Scrollable DataTable of all accounts with create, edit, and delete."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("c", "create", "Create"),
        Binding("d", "delete", "Delete"),
    ]

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow
        self._accounts: list[Account] = []

    def on_mount(self) -> None:
        self.sub_title = "Accounts"
        self._refresh_table()

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="accounts-table", zebra_stripes=True, cursor_type="row")
        yield Footer()

    def _refresh_table(self) -> None:
        table = self.query_one("#accounts-table", DataTable)
        table.clear(columns=True)
        table.add_columns(
            "ID", "Name", "Status", "Category",
            "Side", "Institution", "Currency", "Tags",
        )
        self._accounts = self._fetcher.get_accounts(active_only=False)
        for acc in self._accounts:
            institution_name = acc.institution.name if acc.institution else ""
            tag_names = ", ".join(t.name for t in acc.tags) if acc.tags else ""
            table.add_row(
                str(acc.id),
                acc.name,
                acc.status.value,
                acc.category_name,
                acc.category.side.value if acc.category else "",
                institution_name,
                acc.currency_code,
                tag_names,
                key=str(acc.id),
            )
        table.refresh(layout=True)

    def _load_form_deps(
        self,
    ) -> tuple[list[Category], list[Institution], list[str], list[Tag]]:
        categories = self._fetcher.get_all_categories()
        institutions = self._fetcher.get_all_institutions()
        currencies = [c.code for c in self._fetcher.get_all_currencies()]
        tags = self._fetcher.get_all_tags()
        return categories, institutions, currencies, tags

    @work
    async def action_create(self) -> None:
        categories, institutions, currencies, tags = self._load_form_deps()
        result: AccountFormData | None = await self.app.push_screen_wait(
            AccountFormModal(
                categories=categories,
                institutions=institutions,
                currencies=currencies,
                all_tags=tags,
            )
        )
        if result is None:
            return
        account = Account(
            name=result.name,
            description=result.description,
            category_name=result.category_name,
            institution_id=result.institution_id,
            currency_code=result.currency_code,
            status=result.status,
        )
        try:
            with self._uow() as uow:
                account_id = uow.accounts.insert(account)
                uow.tags.replace_for_account(account_id, result.tag_ids)
        except Exception:
            self.notify(
                "Failed to create account — name may already exist",
                severity="error",
            )
            return
        self.call_after_refresh(self._refresh_table)

    @work
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_idx = event.cursor_row
        if row_idx >= len(self._accounts):
            return
        acc = self._accounts[row_idx]
        categories, institutions, currencies, tags = self._load_form_deps()
        current_tag_ids = [t.id for t in self._fetcher.get_tags_for_account(acc.id)]
        result: AccountFormData | None = await self.app.push_screen_wait(
            AccountFormModal(
                categories=categories,
                institutions=institutions,
                currencies=currencies,
                all_tags=tags,
                account=acc,
                current_tag_ids=current_tag_ids,
            )
        )
        if result is None:
            return
        try:
            acc.name = result.name
            acc.description = result.description
            acc.category_name = result.category_name
            acc.currency_code = result.currency_code
            acc.status = result.status
            acc.institution_id = result.institution_id
            with self._uow() as uow:
                uow.accounts.update(acc)
                uow.tags.replace_for_account(acc.id, result.tag_ids)
        except Exception:
            self.notify(
                "Failed to update account — name may already exist",
                severity="error",
            )
            return
        def _refresh_and_restore() -> None:
            self._refresh_table()
            table = self.query_one("#accounts-table", DataTable)
            if row_idx < len(self._accounts):
                table.move_cursor(row=row_idx)
        self.call_after_refresh(_refresh_and_restore)

    @work
    async def action_delete(self) -> None:
        table = self.query_one("#accounts-table", DataTable)
        row_idx = table.cursor_row
        if row_idx >= len(self._accounts):
            return
        acc = self._accounts[row_idx]
        from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal
        warning = (
            f"Delete account '{acc.name}'? All balance records for this account"
            " will also be deleted. This cannot be undone."
        )
        confirmed: bool = await self.app.push_screen_wait(
            ConfirmModal(warning, confirm_label="Delete")
        )
        if not confirmed:
            return
        with self._uow() as uow:
            uow.balances.delete_by_account_id(acc.id)
            uow.accounts.delete_by_id(acc.id)
        self.call_after_refresh(self._refresh_table)
