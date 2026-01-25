"""
Rich renderers for displaying entities in the terminal.
"""

from rich.console import Console
from rich.table import Table

from nwtrack.application.dto import MonthlyCategoryBalance
from nwtrack.domain.models import Account, Balance, Category, NetWorth
from nwtrack.domain.value_objects import Month


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


def build_categories_table(categories: list[Category]) -> Table:
    """Build a Rich Table of active accounts.

    Args:
        categories (list[Category]): List of Category objects

    Returns:
        Table: Rich Table object
    """
    table = Table(title="Categories")
    table.add_column("Name", style="magenta")
    table.add_column("Side", style="yellow")
    for category in categories:
        category_name = category.name if category else "Unknown"
        side_value = category.side.value if category else "Unknown"
        table.add_row(category_name, side_value)
    return table


def build_balance_counts_table(balance_counts: list[tuple[Month, int]]) -> Table:
    """Build a Rich Table of balances per month.

    Args:
        balance_counts (list[tuple[Month, int]]): List of tuples Month and count of balances
    Returns:
        Table: Rich Table object
            idx (starts at 1) | month | count
    """
    table = Table(title="Balance Entries per Month")
    table.add_column("Index", justify="right", style="green")
    table.add_column("Month", style="cyan")
    table.add_column("Balances", justify="right", style="magenta")
    for idx, (month, count) in enumerate(balance_counts):
        table.add_row(str(idx + 1), str(month), str(count))
    return table


def build_category_summary_table(
    monthly_balances: list[MonthlyCategoryBalance], title_suffix: str = ""
) -> Table:
    """Build a Rich Table of summary by category.

    Args:
        monthly_balances: List of MonthlyCategoryBalance objects
        title_suffix (str): Suffix for table title

    Returns:
        Table: Rich Table object
    """
    _title = "Summary by Category" + (f" {title_suffix}" if title_suffix else "")
    table = Table(title=_title)
    table.add_column("Category", style="magenta")
    table.add_column("Side", style="green")
    table.add_column("Total", justify="right", style="red")
    for mb in monthly_balances:
        category_name = mb.category.name
        category_side = mb.category.side.value
        amount = mb.amount
        table.add_row(
            category_name,
            category_side,
            f"{amount:8,}",
        )
    return table


def build_balances_table(
    balances: list[Balance],
    account_map: dict[int, Account],
    category_map: dict[int, Category | None],
    title_suffix: str = "",
) -> Table:
    """Build a Rich Table of balances.

    Args:
        balances (list[Balance]): List of Balance objects
        account_map (dict[int, Account]): Map of account IDs to Account objects
        category_map (dict[int, Category]): Map of account IDs to Category objects
        title_suffix (str): Suffix for table title

    Returns:
        Table: Rich Table object
    """
    _title = "Balances" + (f" {title_suffix}" if title_suffix else "")
    table = Table(title=_title)
    table.add_column("Acct_ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Account Name", style="magenta")
    table.add_column("Category", style="green")
    table.add_column("Side", style="yellow")
    table.add_column("Amount", justify="right", style="red")
    for balance in balances:
        account_id = balance.account_id
        account_name = account_map[account_id].name
        category: Category | None = category_map.get(account_id, None)
        assert category is not None, f"Category not found for account ID {account_id}"
        category_name = category.name if category else "Unknown"
        side = category.side.value if category else "Unknown"
        table.add_row(
            str(account_id),
            account_name,
            category_name,
            side,
            f"{balance.amount:8,}",
        )
    return table


def build_networth_table(nw: NetWorth, title_suffix: str = "", form="wide") -> Table:
    """Build a Rich Table of net worth summary.

    Args:
        nw (NetWorth): NetWorth object
        title_suffix (str): Suffix for table title
        form (str): Table format, "wide" or "long"

    Returns:
        Table: Rich Table object
    """
    _title = "Net Worth Summary" + (f" {title_suffix}" if title_suffix else "")
    table = Table(title=_title)
    if form == "long":
        table.add_column("Side", style="magenta")
        table.add_column("Total", justify="right", style="red")
        table.add_row("Assets", f"{nw.assets:9,}")
        table.add_row("Liabilities", f"{nw.liabilities:9,}")
        table.add_row("Net Worth", f"{nw.net_worth:9,}")
    elif form == "wide":
        table.add_column("Assets", justify="right", style="green")
        table.add_column("Liabilities", justify="right", style="yellow")
        table.add_column("Net Worth", justify="right", style="red")
        table.add_row(
            f"{nw.assets:9,}",
            f"{nw.liabilities:9,}",
            f"{nw.net_worth:9,}",
        )
    else:
        raise ValueError(f"Invalid table form: {form}")
        table = Table()
    return table
