"""Tag list screen and form modal for the nwtrack TUI."""

from collections.abc import Callable

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Footer, Header, Input, Label

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.infra.persistence.orm.models import Tag


class TagFormModal(ModalScreen[Tag | None]):
    """Overlay modal for creating or editing a tag.

    Pass tag=None for create mode; pass an existing tag for edit mode.
    Returns the Tag on confirm (not yet persisted), None on cancel.
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    TagFormModal {
        align: center middle;
    }
    #tag-form-container {
        width: 54;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #tag-form-title {
        text-align: center;
        margin-bottom: 1;
    }
    #tag-form-error {
        color: $error;
        margin-top: 1;
    }
    """

    def __init__(self, tag: Tag | None = None) -> None:
        super().__init__()
        self._tag = tag
        self._edit_mode = tag is not None

    def compose(self) -> ComposeResult:
        title = "Edit Tag" if self._edit_mode else "Create Tag"
        name_default = self._tag.name if self._tag else ""
        desc_default = self._tag.description or "" if self._tag else ""
        with Vertical(id="tag-form-container"):
            yield Label(title, id="tag-form-title")
            yield Label("Name")
            yield Input(value=name_default, placeholder="Tag name", id="input-name")
            yield Label("Description (optional)")
            yield Input(value=desc_default, placeholder="Description", id="input-desc")
            yield Label("", id="tag-form-error")
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
            self.query_one("#tag-form-error", Label).update("Name is required")
            self.query_one("#input-name", Input).focus()
            return
        if self._edit_mode and self._tag is not None:
            self._tag.name = name
            self._tag.description = desc
            self.dismiss(self._tag)
        else:
            self.dismiss(Tag(name=name, description=desc))

    def action_cancel(self) -> None:
        self.dismiss(None)


class TagsListScreen(Screen):
    """Scrollable DataTable of tags with create, edit, and delete."""

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
        self._tags: list[Tag] = []

    def on_mount(self) -> None:
        self.sub_title = "Tags"
        self._refresh_table()

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="tags-table", zebra_stripes=True, cursor_type="row")
        yield Footer()

    def _refresh_table(self) -> None:
        table = self.query_one("#tags-table", DataTable)
        table.clear(columns=True)
        table.add_columns("ID", "Name", "Description", "Linked Accounts")
        self._tags = self._fetcher.get_all_tags()
        for tag in self._tags:
            with self._uow() as uow:
                count = uow.tags.count_linked_accounts(tag.id)
            table.add_row(
                str(tag.id),
                tag.name,
                tag.description or "",
                str(count),
                key=str(tag.id),
            )

    @work
    async def action_create(self) -> None:
        result: Tag | None = await self.app.push_screen_wait(TagFormModal())
        if result is None:
            return
        try:
            with self._uow() as uow:
                uow.tags.insert(result)
        except Exception:
            self.notify(
                "Failed to create tag — name may already exist",
                severity="error",
            )
            return
        self._refresh_table()

    @work
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_idx = event.cursor_row
        if row_idx >= len(self._tags):
            return
        tag = self._tags[row_idx]
        result: Tag | None = await self.app.push_screen_wait(TagFormModal(tag))
        if result is None:
            return
        try:
            with self._uow() as uow:
                uow.tags.update(result)
        except Exception:
            self.notify(
                "Failed to update tag — name may already exist",
                severity="error",
            )
            return
        self._refresh_table()

    @work
    async def action_delete(self) -> None:
        table = self.query_one("#tags-table", DataTable)
        row_idx = table.cursor_row
        if row_idx >= len(self._tags):
            return
        tag = self._tags[row_idx]
        with self._uow() as uow:
            count = uow.tags.count_linked_accounts(tag.id)
        warning = (
            f"Delete tag '{tag.name}'?"
            + (f" {count} account association(s) will be removed." if count else "")
            + " This cannot be undone."
        )
        from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal
        confirmed: bool = await self.app.push_screen_wait(
            ConfirmModal(warning, confirm_label="Delete")
        )
        if not confirmed:
            return
        with self._uow() as uow:
            uow.tags.delete_by_id(tag.id)
        self._refresh_table()
