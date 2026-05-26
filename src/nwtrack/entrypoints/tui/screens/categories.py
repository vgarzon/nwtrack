"""Category list screen and form modal for the nwtrack TUI."""

from collections.abc import Callable

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Footer, Header, Input, Label, Select

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.infra.persistence.orm.models import Category, Side

_SIDE_OPTIONS = [(side.value.capitalize(), side.value) for side in Side]


class CategoryFormModal(ModalScreen[Category | None]):
    """Overlay modal for creating a category.

    Returns the Category on confirm (not yet persisted), None on cancel.
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    CategoryFormModal {
        align: center middle;
    }
    #category-form-container {
        width: 54;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #category-form-title {
        text-align: center;
        margin-bottom: 1;
    }
    #category-form-error {
        color: $error;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="category-form-container"):
            yield Label("Create Category", id="category-form-title")
            yield Label("Name")
            yield Input(placeholder="Category name", id="input-name")
            yield Label("Side")
            yield Select(
                options=_SIDE_OPTIONS,
                prompt="Select side",
                id="select-side",
            )
            yield Label("", id="category-form-error")
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#input-name", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.query_one("#select-side", Select).focus()

    def _submit(self) -> None:
        name = self.query_one("#input-name", Input).value.strip()
        side_select = self.query_one("#select-side", Select)
        error = self.query_one("#category-form-error", Label)
        if not name:
            error.update("Name is required")
            self.query_one("#input-name", Input).focus()
            return
        if side_select.value is Select.NULL:
            error.update("Side is required")
            side_select.focus()
            return
        self.dismiss(Category(name=name, side=Side(str(side_select.value))))

    def on_select_changed(self, event: Select.Changed) -> None:
        pass

    def on_key(self, event) -> None:  # type: ignore[override]
        if event.key == "enter":
            focused = self.focused
            if focused and focused.id == "select-side":
                self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)


class CategoriesListScreen(Screen):
    """Scrollable DataTable of categories with create."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("c", "create", "Create"),
    ]

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow

    def on_mount(self) -> None:
        self.sub_title = "Categories"
        self._refresh_table()

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="categories-table", zebra_stripes=True, cursor_type="row")
        yield Footer()

    def _refresh_table(self) -> None:
        table = self.query_one("#categories-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Name", "Side")
        for category in self._fetcher.get_all_categories():
            table.add_row(category.name, category.side.value, key=category.name)

    @work
    async def action_create(self) -> None:
        result: Category | None = await self.app.push_screen_wait(CategoryFormModal())
        if result is None:
            return
        try:
            with self._uow() as uow:
                uow.categories.insert(result)
        except Exception:
            self.notify(
                "Failed to create category — name may already exist",
                severity="error",
            )
            return
        self._refresh_table()
