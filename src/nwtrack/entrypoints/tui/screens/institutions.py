"""Institution list screen and form modal for the nwtrack TUI."""

from collections.abc import Callable

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Footer, Header, Input, Label

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.infra.persistence.orm.models import Institution


class InstitutionFormModal(ModalScreen[Institution | None]):
    """Overlay modal for creating or editing an institution.

    Pass institution=None for create mode; pass an existing institution for edit mode.
    Returns the Institution on confirm (not yet persisted), None on cancel.
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    InstitutionFormModal {
        align: center middle;
    }
    #institution-form-container {
        width: 54;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #institution-form-title {
        text-align: center;
        margin-bottom: 1;
    }
    #institution-form-error {
        color: $error;
        margin-top: 1;
    }
    """

    def __init__(self, institution: Institution | None = None) -> None:
        super().__init__()
        self._institution = institution
        self._edit_mode = institution is not None

    def compose(self) -> ComposeResult:
        title = "Edit Institution" if self._edit_mode else "Create Institution"
        name_default = self._institution.name if self._institution else ""
        desc_default = self._institution.description or "" if self._institution else ""
        with Vertical(id="institution-form-container"):
            yield Label(title, id="institution-form-title")
            yield Label("Name")
            yield Input(
                value=name_default,
                placeholder="Institution name",
                id="input-name",
            )
            yield Label("Description (optional)")
            yield Input(value=desc_default, placeholder="Description", id="input-desc")
            yield Label("", id="institution-form-error")
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#input-name", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "input-name":
            self.query_one("#input-desc", Input).focus()
        elif event.input.id == "input-desc":
            self._submit()

    def _submit(self) -> None:
        name = self.query_one("#input-name", Input).value.strip()
        desc_raw = self.query_one("#input-desc", Input).value.strip()
        desc: str | None = desc_raw if desc_raw else None
        if not name:
            self.query_one("#institution-form-error", Label).update("Name is required")
            self.query_one("#input-name", Input).focus()
            return
        if self._edit_mode and self._institution is not None:
            self._institution.name = name
            self._institution.description = desc
            self.dismiss(self._institution)
        else:
            self.dismiss(Institution(name=name, description=desc))

    def action_cancel(self) -> None:
        self.dismiss(None)


class InstitutionsListScreen(Screen):
    """Scrollable DataTable of institutions with create, edit, and delete."""

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
        self._institutions: list[Institution] = []

    def on_mount(self) -> None:
        self.sub_title = "Institutions"
        self._refresh_table()

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="institutions-table", zebra_stripes=True, cursor_type="row")
        yield Footer()

    def _refresh_table(self) -> None:
        table = self.query_one("#institutions-table", DataTable)
        table.clear(columns=True)
        table.add_columns("ID", "Name", "Description", "Linked Accounts")
        self._institutions = self._fetcher.get_all_institutions()
        for inst in self._institutions:
            with self._uow() as uow:
                count = uow.institutions.count_linked_accounts(inst.id)
            table.add_row(
                str(inst.id),
                inst.name,
                inst.description or "",
                str(count),
                key=str(inst.id),
            )

    @work
    async def action_create(self) -> None:
        result: Institution | None = await self.app.push_screen_wait(
            InstitutionFormModal()
        )
        if result is None:
            return
        try:
            with self._uow() as uow:
                uow.institutions.insert(result)
        except Exception:
            self.notify(
                "Failed to create institution — name may already exist",
                severity="error",
            )
            return
        self._refresh_table()

    @work
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_idx = event.cursor_row
        if row_idx >= len(self._institutions):
            return
        inst = self._institutions[row_idx]
        result: Institution | None = await self.app.push_screen_wait(
            InstitutionFormModal(inst)
        )
        if result is None:
            return
        try:
            with self._uow() as uow:
                uow.institutions.update(result)
        except Exception:
            self.notify(
                "Failed to update institution — name may already exist",
                severity="error",
            )
            return
        self._refresh_table()

    @work
    async def action_delete(self) -> None:
        table = self.query_one("#institutions-table", DataTable)
        row_idx = table.cursor_row
        if row_idx >= len(self._institutions):
            return
        inst = self._institutions[row_idx]
        with self._uow() as uow:
            count = uow.institutions.count_linked_accounts(inst.id)
        warning = (
            f"Delete institution '{inst.name}'?"
            + (
                f" {count} account(s) will lose their institution assignment."
                if count
                else ""
            )
            + " This cannot be undone."
        )
        from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal
        confirmed: bool = await self.app.push_screen_wait(
            ConfirmModal(warning, confirm_label="Delete")
        )
        if not confirmed:
            return
        with self._uow() as uow:
            uow.institutions.delete_by_id(inst.id)
        self._refresh_table()
