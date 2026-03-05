"""
Rich renderers for displaying entities in the terminal.
"""

from rich.console import Console
from rich.table import Table

from nwtrack.application.dto import MonthlyCategoryBalance
from nwtrack.domain.models import Account, Balance, Category, Currency, NetWorth, Status
from nwtrack.domain.value_objects import Month


def build_accounts_table(
    accounts: list[Account],
    title_prefix: str = "",
) -> Table:
    """Build a Rich Table of active accounts.

    Args:
        accounts (list[Account]): List of Account objects
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
        category = account.category
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


def build_indexed_categories_table(categories: list[Category]) -> Table:
    """Build a Rich Table of categories with index.

    Args:
        categories (list[Category]): List of Category objects

    Returns:
        Table: Rich Table object
    """
    table = Table(title="Categories")
    table.add_column("Index", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Side", style="green")
    for k, category in enumerate(categories):
        table.add_row(
            str(k + 1),
            category.name,
            category.side.value,
        )
    return table


def build_balance_counts_table(balance_counts: list[tuple[Month, int]]) -> Table:
    """Build a Rich Table of balances per month.

    Args:
        balance_counts: List of tuples (Month, count of balances)

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
    title_suffix: str = "",
) -> Table:
    """Build a Rich Table of balances.

    Args:
        balances (list[Balance]): List of Balance objects
        account_map (dict[int, Account]): Map of account IDs to Account objects
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
        account = account_map[account_id]
        category = account.category
        category_name = category.name if category else "Unknown"
        side = category.side.value if category else "Unknown"
        table.add_row(
            str(account_id),
            account.name,
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


def build_currencies_table(currencies: list[Currency]) -> Table:
    """Build a Rich Table of currencies.

    Args:
        currencies (list[Currency]): List of Currency objects

    Returns:
        Table: Rich Table object
    """
    table = Table(title="Currencies")
    table.add_column("Index", justify="right", style="cyan", no_wrap=True)
    table.add_column("Code", style="magenta")
    table.add_column("Description", style="green")
    for k, currency in enumerate(currencies):
        table.add_row(
            str(k + 1),
            currency.code,
            currency.description,
        )
    return table


def build_status_table(status_options: list[Status]) -> Table:
    """Build a Rich Table of status options.

    Args:
        status_options (list[Status]): List of Status enum options

    Returns:
        Table: Rich Table object
    """
    table = Table(title="Status Options")
    table.add_column("Index", justify="right", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    for k, status in enumerate(status_options):
        table.add_row(
            str(k + 1),
            status.value,
        )
    return table


def render_new_account_info(
    console: Console, account: Account, balance: Balance
) -> None:
    """Render information about a newly created account.

    Args:
        console: Rich Console object
        account: Account object
        balance: Balance object
    """
    console.print(
        f"[yellow]Account name:[/yellow] {account.name}\n"
        f"[yellow]Account ID:[/yellow] {account.id}\n"
        f"[yellow]Description:[/yellow] {account.description}\n"
        f"[yellow]Currency:[/yellow] {account.currency_code}\n"
        f"[yellow]Category:[/yellow] {account.category_name}\n"
        f"[yellow]Status:[/yellow] {account.status.value}\n"
        f"[yellow]Initial month:[/yellow] {balance.month}\n"
        f"[yellow]Initial balance:[/yellow] {balance.amount}\n"
    )


def render_category_data(console: Console, category: Category) -> None:
    console.print(
        f"[yellow]Category name:[/yellow] {category.name}\n"
        f"[yellow]Category side:[/yellow] {category.side.value}\n"
    )


def build_file_paths_table(file_paths: dict[str, str], title_prefix: str = "") -> Table:
    """Build a table of file paths for display.

    Args:
        file_paths (list[str]): List of file paths
        title_prefix (str): Optional title prefix

    Returns:
        Table: Rich Table object with file paths
    """
    title = f"{title_prefix} File Paths" if title_prefix else "File Paths"
    table = Table(title=title)
    table.add_column("Repo", style="cyan", no_wrap=True)
    table.add_column("Path", style="magenta")
    for key, path in file_paths.items():
        table.add_row(key, path)
    return table


def build_networth_history_table(nws: list[NetWorth]) -> Table:
    """Build a Rich Table of net worth summary.

    Args:
        console: Rich Console object
        nws: List of Net Worth records

    Returns:
        Table: Rich Table object
    """
    _first_month = nws[0].month if nws else ""
    _last_month = nws[-1].month if nws else ""
    _title = f"Net Worth History {_first_month} to {_last_month}"
    table = Table(title=f"[green]{_title}[/green]")
    table.add_column("Month", justify="right")
    table.add_column("Assets", justify="right", style="green")
    table.add_column("Liabilities", justify="right", style="yellow")
    table.add_column("Net Worth", justify="right", style="red")
    table.add_column("Change", justify="right")
    for k, nw in enumerate(nws):
        if k > 0:
            change = nw.net_worth - nws[k - 1].net_worth
            color_str = "red" if change < 0 else "green"
            change_str = f"[{color_str}]{change:7,}[/{color_str}]"
        else:
            change_str = ""
        table.add_row(
            f"{nw.month}",
            f"{nw.assets:9,}",
            f"{nw.liabilities:9,}",
            f"{nw.net_worth:9,}",
            f"{change_str}",
        )
    return table


def build_month_balances_table(balance_counts: list[tuple[Month, int]]) -> Table:
    """Build Rich table of balances per month.

    Args:
        balance_counts: List of tuples (Month, count of balances)

    Returns:
        Table: Rich Table object
    """
    table = Table(title="Balance Entries per Month")
    table.add_column("Index", justify="right", style="green")
    table.add_column("Month", style="cyan")
    table.add_column("Balances", justify="right", style="magenta")
    for idx, (month, count) in enumerate(balance_counts):
        table.add_row(str(idx + 1), str(month), str(count))
    return table


def build_networth_history_total_change_table(changes: dict) -> Table:
    """Build Rich table of total net worth changes.

    Args:
        changes: Dictionary with total change data

    Returns:
        Table: Rich Table object
    """
    table = Table(title="Total Change")
    table.add_column("Assets", justify="right", style="green")
    table.add_column("Liabilities", justify="right", style="orange3")
    table.add_column("Net Worth", justify="right", style="bold")

    changes_abs = (f"{changes[k][0]:,}" for k in ["assets", "liabilities", "net_worth"])
    changes_pct = (
        f"({changes[k][1]:.0%})" for k in ["assets", "liabilities", "net_worth"]
    )
    table.add_row(*changes_abs)
    table.add_row(*changes_pct)
    return table
