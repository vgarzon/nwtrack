"""
Rich renderers for displaying entities in the terminal.
"""

from rich.console import Console
from rich.table import Table
from nwtrack.domain.models import Account, Category


def build_accounts_table(
    accounts: list[Account],
    categories_map: dict[int, Category | None],
    title_prefix: str = "",
) -> Table:
    """Build a Rich Table of active accounts.

    Args:
        accounts (list[Account]): List of Account objects
        categories_map (dict[int, Category]): Mapping of account IDs to Category objects
        title_prefix (str): Optional prefix for the table title.

    Returns:
        Table: Rich Table object
    """
    _title = f"{title_prefix} Accounts" if title_prefix else "Accounts"
    table = Table(title=_title)
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Category", style="green")
    table.add_column("Side", style="yellow")
    for account in accounts:
        category = categories_map.get(account.id)
        category_name = category.name if category else "Unknown"
        side = category.side.value if category else "Unknown"
        table.add_row(
            str(account.id),
            account.name,
            category_name,
            side,
        )
    return table


def render_account_data(console: Console, account: Account) -> None:
    console.print(
        f"[yellow]Account ID:[/yellow] {account.id}\n"
        f"[yellow]Account name:[/yellow] {account.name}\n"
        f"[yellow]Description:[/yellow] {account.description}\n"
        f"[yellow]Currency:[/yellow] {account.currency_code}\n"
        f"[yellow]Category:[/yellow] {account.category_name}\n"
        f"[yellow]Status:[/yellow] {account.status}"
    )
