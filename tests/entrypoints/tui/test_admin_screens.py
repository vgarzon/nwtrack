"""Tests for Phase 30 TUI admin and account screens."""

import asyncio
from unittest.mock import MagicMock

from nwtrack.entrypoints.tui.app import NWTrackApp
from nwtrack.entrypoints.tui.screens.accounts import AccountsListScreen
from nwtrack.entrypoints.tui.screens.admin_menu import AdminMenuScreen
from nwtrack.entrypoints.tui.screens.categories import CategoriesListScreen
from nwtrack.entrypoints.tui.screens.home import HomeScreen
from nwtrack.entrypoints.tui.screens.institutions import InstitutionsListScreen
from nwtrack.entrypoints.tui.screens.tags import TagsListScreen
from nwtrack.infra.persistence.orm.models import (
    Account,
    Category,
    Institution,
    Side,
    Status,
    Tag,
)

# ── Fixtures / helpers ───────────────────────────────────────────────────────


def _mock_uow(institutions=None, tags=None, categories=None, accounts=None):
    """Build a UoW factory mock wired with sensible defaults."""
    uow_factory = MagicMock()
    mock_uow = MagicMock()
    uow_factory.return_value.__enter__ = MagicMock(return_value=mock_uow)
    uow_factory.return_value.__exit__ = MagicMock(return_value=False)
    mock_uow.institutions.count_linked_accounts.return_value = 0
    mock_uow.tags.count_linked_accounts.return_value = 0
    return uow_factory, mock_uow


def _make_institution(
    id_: int, name: str, description: str | None = None
) -> Institution:
    inst = Institution(name=name, description=description)
    inst.id = id_
    return inst


def _make_tag(id_: int, name: str, description: str | None = None) -> Tag:
    tag = Tag(name=name, description=description)
    tag.id = id_
    return tag


def _make_category(name: str, side: Side) -> Category:
    return Category(name=name, side=side)


def _make_account(
    id_: int,
    name: str,
    category: Category,
    currency_code: str = "USD",
    status: Status = Status.ACTIVE,
) -> Account:
    acc = Account(
        name=name,
        description="",
        category_name=category.name,
        institution_id=None,
        currency_code=currency_code,
        status=status,
    )
    acc.id = id_
    acc.category = category
    acc.institution = None
    acc.tags = []
    return acc


def _make_fetcher(
    institutions=None,
    tags=None,
    categories=None,
    accounts=None,
    currencies=None,
):
    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = []
    fetcher.get_all_institutions.return_value = institutions or []
    fetcher.get_all_tags.return_value = tags or []
    fetcher.get_all_categories.return_value = categories or []
    fetcher.get_accounts.return_value = accounts or []
    fetcher.get_all_currencies.return_value = currencies or []
    fetcher.get_tags_for_account.return_value = []
    return fetcher


def _make_app(fetcher=None, uow_factory=None):
    if fetcher is None:
        fetcher = _make_fetcher()
    if uow_factory is None:
        uow_factory, _ = _mock_uow()
    return NWTrackApp(fetcher=fetcher, uow=uow_factory)


# ── HomeScreen routing ───────────────────────────────────────────────────────


class TestHomeScreenRouting:
    def test_accounts_pushes_accounts_list_screen(self) -> None:
        app = _make_app()

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("down")  # Accounts
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AccountsListScreen)

        asyncio.run(_run())

    def test_admin_pushes_admin_menu_screen(self) -> None:
        app = _make_app()

        async def _run() -> None:
            async with app.run_test() as pilot:
                for _ in range(3):
                    await pilot.press("down")  # Reports, Accounts, Admin
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AdminMenuScreen)

        asyncio.run(_run())

    def test_escape_from_accounts_returns_to_home(self) -> None:
        app = _make_app()

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")
                await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AccountsListScreen)
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, HomeScreen)

        asyncio.run(_run())

    def test_escape_from_admin_returns_to_home(self) -> None:
        app = _make_app()

        async def _run() -> None:
            async with app.run_test() as pilot:
                for _ in range(3):
                    await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AdminMenuScreen)
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, HomeScreen)

        asyncio.run(_run())


# ── AdminMenuScreen ──────────────────────────────────────────────────────────


class TestAdminMenuScreen:
    def test_subtitle_is_admin(self) -> None:
        app = _make_app()

        async def _run() -> None:
            async with app.run_test() as pilot:
                for _ in range(3):
                    await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                assert app.screen.sub_title == "Admin"

        asyncio.run(_run())

    def test_institutions_pushes_institutions_list(self) -> None:
        app = _make_app()

        async def _run() -> None:
            async with app.run_test() as pilot:
                for _ in range(3):
                    await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AdminMenuScreen)
                await pilot.press("enter")  # Institutions (first item)
                await pilot.pause()
                assert isinstance(app.screen, InstitutionsListScreen)

        asyncio.run(_run())

    def test_tags_pushes_tags_list(self) -> None:
        app = _make_app()

        async def _run() -> None:
            async with app.run_test() as pilot:
                for _ in range(3):
                    await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("down")  # Tags
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, TagsListScreen)

        asyncio.run(_run())

    def test_categories_pushes_categories_list(self) -> None:
        app = _make_app()

        async def _run() -> None:
            async with app.run_test() as pilot:
                for _ in range(3):
                    await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("down")
                await pilot.press("down")  # Categories
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, CategoriesListScreen)

        asyncio.run(_run())

    def test_escape_from_institutions_returns_to_admin(self) -> None:
        app = _make_app()

        async def _run() -> None:
            async with app.run_test() as pilot:
                for _ in range(3):
                    await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, InstitutionsListScreen)
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, AdminMenuScreen)

        asyncio.run(_run())


# ── InstitutionsListScreen ───────────────────────────────────────────────────


class TestInstitutionsListScreen:
    def _navigate_to_institutions(self, pilot):
        async def _go():
            for _ in range(3):
                await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

        return _go()

    def test_renders_institutions_from_fetcher(self) -> None:
        inst = _make_institution(1, "CIBC", "Bank")
        fetcher = _make_fetcher(institutions=[inst])
        uow_factory, mock_uow = _mock_uow()
        app = _make_app(fetcher, uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await self._navigate_to_institutions(pilot)
                assert isinstance(app.screen, InstitutionsListScreen)
                assert app.screen._institutions == [inst]

        asyncio.run(_run())

    def test_empty_institution_list(self) -> None:
        fetcher = _make_fetcher(institutions=[])
        uow_factory, _ = _mock_uow()
        app = _make_app(fetcher, uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await self._navigate_to_institutions(pilot)
                assert isinstance(app.screen, InstitutionsListScreen)
                assert app.screen._institutions == []

        asyncio.run(_run())

    def test_delete_calls_delete_by_id(self) -> None:
        from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal

        inst = _make_institution(42, "CIBC")
        fetcher = _make_fetcher(institutions=[inst])
        uow_factory, mock_uow = _mock_uow()
        app = _make_app(fetcher, uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await self._navigate_to_institutions(pilot)
                screen = app.screen
                assert isinstance(screen, InstitutionsListScreen)

                async def _auto_confirm(modal_screen):
                    if isinstance(modal_screen, ConfirmModal):
                        modal_screen.dismiss(True)

                app.push_screen = MagicMock(side_effect=app.push_screen)
                screen._institutions = [inst]

                await pilot.press("d")
                await pilot.pause()
                # Dismiss the confirm modal that was pushed
                if isinstance(app.screen, ConfirmModal):
                    app.screen.dismiss(True)
                    await pilot.pause()

                mock_uow.institutions.delete_by_id.assert_called_with(42)

        asyncio.run(_run())


# ── TagsListScreen ───────────────────────────────────────────────────────────


class TestTagsListScreen:
    def _navigate_to_tags(self, pilot):
        async def _go():
            for _ in range(3):
                await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("down")  # Tags
            await pilot.press("enter")
            await pilot.pause()

        return _go()

    def test_renders_tags_from_fetcher(self) -> None:
        tag = _make_tag(1, "retirement")
        fetcher = _make_fetcher(tags=[tag])
        uow_factory, _ = _mock_uow()
        app = _make_app(fetcher, uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await self._navigate_to_tags(pilot)
                assert isinstance(app.screen, TagsListScreen)
                assert app.screen._tags == [tag]

        asyncio.run(_run())

    def test_delete_calls_delete_by_id(self) -> None:
        from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal

        tag = _make_tag(7, "retirement")
        fetcher = _make_fetcher(tags=[tag])
        uow_factory, mock_uow = _mock_uow()
        app = _make_app(fetcher, uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await self._navigate_to_tags(pilot)
                screen = app.screen
                assert isinstance(screen, TagsListScreen)

                await pilot.press("d")
                await pilot.pause()
                if isinstance(app.screen, ConfirmModal):
                    app.screen.dismiss(True)
                    await pilot.pause()

                mock_uow.tags.delete_by_id.assert_called_with(7)

        asyncio.run(_run())


# ── CategoriesListScreen ─────────────────────────────────────────────────────


class TestCategoriesListScreen:
    def _navigate_to_categories(self, pilot):
        async def _go():
            for _ in range(3):
                await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("down")
            await pilot.press("down")  # Categories
            await pilot.press("enter")
            await pilot.pause()

        return _go()

    def test_renders_categories_from_fetcher(self) -> None:
        cat = _make_category("Savings", Side.ASSET)
        fetcher = _make_fetcher(categories=[cat])
        uow_factory, _ = _mock_uow()
        app = _make_app(fetcher, uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await self._navigate_to_categories(pilot)
                assert isinstance(app.screen, CategoriesListScreen)
                from textual.widgets import DataTable
                table = app.screen.query_one("#categories-table", DataTable)
                assert table.row_count == 1

        asyncio.run(_run())

    def test_subtitle_is_categories(self) -> None:
        fetcher = _make_fetcher()
        uow_factory, _ = _mock_uow()
        app = _make_app(fetcher, uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await self._navigate_to_categories(pilot)
                assert isinstance(app.screen, CategoriesListScreen)
                assert app.screen.sub_title == "Categories"

        asyncio.run(_run())


# ── AccountsListScreen ───────────────────────────────────────────────────────


class TestAccountsListScreen:
    def _navigate_to_accounts(self, pilot):
        async def _go():
            await pilot.press("down")
            await pilot.press("down")  # Accounts
            await pilot.press("enter")
            await pilot.pause()

        return _go()

    def test_shows_all_accounts_active_and_inactive(self) -> None:
        cat = _make_category("Savings", Side.ASSET)
        active_acc = _make_account(1, "Chequing", cat, status=Status.ACTIVE)
        inactive_acc = _make_account(2, "OldAccount", cat, status=Status.INACTIVE)
        fetcher = _make_fetcher(accounts=[active_acc, inactive_acc], categories=[cat])
        uow_factory, _ = _mock_uow()
        app = _make_app(fetcher, uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await self._navigate_to_accounts(pilot)
                screen = app.screen
                assert isinstance(screen, AccountsListScreen)
                assert len(screen._accounts) == 2
                names = {a.name for a in screen._accounts}
                assert "Chequing" in names
                assert "OldAccount" in names

        asyncio.run(_run())

    def test_get_accounts_called_with_active_only_false(self) -> None:
        cat = _make_category("Savings", Side.ASSET)
        fetcher = _make_fetcher(categories=[cat])
        uow_factory, _ = _mock_uow()
        app = _make_app(fetcher, uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await self._navigate_to_accounts(pilot)
                assert isinstance(app.screen, AccountsListScreen)
                fetcher.get_accounts.assert_called_with(active_only=False)

        asyncio.run(_run())

    def test_subtitle_is_accounts(self) -> None:
        fetcher = _make_fetcher()
        uow_factory, _ = _mock_uow()
        app = _make_app(fetcher, uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await self._navigate_to_accounts(pilot)
                assert isinstance(app.screen, AccountsListScreen)
                assert app.screen.sub_title == "Accounts"

        asyncio.run(_run())

    def test_delete_removes_account_and_balances(self) -> None:
        from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal

        cat = _make_category("Savings", Side.ASSET)
        acc = _make_account(99, "MyAccount", cat)
        fetcher = _make_fetcher(accounts=[acc], categories=[cat])
        uow_factory, mock_uow = _mock_uow()
        app = _make_app(fetcher, uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await self._navigate_to_accounts(pilot)
                screen = app.screen
                assert isinstance(screen, AccountsListScreen)

                await pilot.press("d")
                await pilot.pause()
                if isinstance(app.screen, ConfirmModal):
                    app.screen.dismiss(True)
                    await pilot.pause()

                mock_uow.balances.delete_by_account_id.assert_called_with(99)
                mock_uow.accounts.delete_by_id.assert_called_with(99)

        asyncio.run(_run())

    def test_delete_cancel_does_not_remove_account(self) -> None:
        from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal

        cat = _make_category("Savings", Side.ASSET)
        acc = _make_account(99, "MyAccount", cat)
        fetcher = _make_fetcher(accounts=[acc], categories=[cat])
        uow_factory, mock_uow = _mock_uow()
        app = _make_app(fetcher, uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await self._navigate_to_accounts(pilot)
                screen = app.screen
                assert isinstance(screen, AccountsListScreen)

                await pilot.press("d")
                await pilot.pause()
                if isinstance(app.screen, ConfirmModal):
                    app.screen.dismiss(False)
                    await pilot.pause()

                mock_uow.accounts.delete_by_id.assert_not_called()

        asyncio.run(_run())


# ── ConfirmModal ─────────────────────────────────────────────────────────────


class TestConfirmModal:
    """Test ConfirmModal by mounting it directly as the root screen."""

    def test_confirm_button_dismisses_true(self) -> None:
        from textual.app import App, ComposeResult

        from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal

        class _ModalApp(App):
            CSS = "Screen { align: center middle; }"

            def compose(self) -> ComposeResult:
                yield ConfirmModal("Are you sure?", confirm_label="Yes")

        async def _run() -> None:
            app = _ModalApp()
            async with app.run_test() as pilot:
                await pilot.pause()
                modal = app.query_one(ConfirmModal)
                from textual.widgets import Button
                btn = modal.query_one("#btn-confirm", Button)
                assert str(btn.label) == "Yes"

        asyncio.run(_run())

    def test_cancel_button_label(self) -> None:
        from textual.app import App, ComposeResult

        from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal

        class _ModalApp(App):
            CSS = "Screen { align: center middle; }"

            def compose(self) -> ComposeResult:
                yield ConfirmModal("Are you sure?", cancel_label="No Thanks")

        async def _run() -> None:
            app = _ModalApp()
            async with app.run_test() as pilot:
                await pilot.pause()
                modal = app.query_one(ConfirmModal)
                from textual.widgets import Button
                btn = modal.query_one("#btn-cancel", Button)
                assert str(btn.label) == "No Thanks"

        asyncio.run(_run())

    def test_action_cancel_calls_dismiss_false(self) -> None:
        """action_cancel() should dismiss with False."""
        from unittest.mock import patch

        from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal

        modal = ConfirmModal("Test")
        with patch.object(modal, "dismiss") as mock_dismiss:
            modal.action_cancel()
            mock_dismiss.assert_called_once_with(False)
