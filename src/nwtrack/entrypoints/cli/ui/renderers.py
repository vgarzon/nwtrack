"""
Rich renderers for displaying entities in the terminal.
"""

from rich.console import Console
from rich.table import Table

from nwtrack.application.dto import InstitutionListItem, MonthlyCategoryBalance
from nwtrack.domain.models import (
    Account,
    Balance,
    Category,
    Currency,
    Institution,
    NetWorth,
    Status,
)
from nwtrack.domain.value_objects import Month

UNASSIGNED_INSTITUTION_LABEL = "None"
UNASSIGNED_INSTITUTION_TABLE_LABEL = ""


def format_institution_name(
    account: Account,
    unassigned_label: str = UNASSIGNED_INSTITUTION_LABEL,
) -> str:
    """Return the display label for an account institution."""
    institution = account.institution
    if institution is not None:
        return institution.name
    return unassigned_label


def build_indexed_institutions_table(institutions: list[Institution]) -> Table:
    """Build an indexed institution-selection table with a None option."""
    table = Table(title="Institutions")
    table.add_column("Index", justify="right", style="col.id", no_wrap=True)
    table.add_column("Name", style="col.name")
    table.add_column("Description", style="col.desc")
    table.add_row("0", UNASSIGNED_INSTITUTION_LABEL, "")
    for index, institution in enumerate(institutions, start=1):
        table.add_row(
            str(index),
            institution.name,
            institution.description or "",
        )
    return table


def build_accounts_table(
    accounts: list[Account],
    title_prefix: str = "",
    show_institution: bool = False,
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
    table.add_column("ID", justify="right", style="col.id", no_wrap=True)
    if show_institution:
        table.add_column("Institution", style="col.name")
    table.add_column("Name", style="col.name")
    table.add_column("Category", style="col.category")
    table.add_column("Side", style="col.side")
    for account in accounts:
        category = account.category
        category_name = category.name if category else "Unknown"
        side = category.side.value if category else "Unknown"
        row = [
            str(account.id),
        ]
        if show_institution:
            row.append(
                format_institution_name(
                    account,
                    unassigned_label=UNASSIGNED_INSTITUTION_TABLE_LABEL,
                )
            )
        row.extend(
            [
                account.name,
                category_name,
                side,
            ]
        )
        table.add_row(*row)
    return table


def render_account_data(
    console: Console,
    account: Account,
    institution_name: str | None = None,
) -> None:
    console.print(
        f"[label]Account ID:[/label] {account.id}\n"
        f"[label]Account name:[/label] {account.name}\n"
        f"[label]Description:[/label] {account.description}\n"
        f"[label]Currency:[/label] {account.currency_code}\n"
        f"[label]Category:[/label] {account.category_name}\n"
        f"[label]Institution:[/label] "
        f"{institution_name or format_institution_name(account)}\n"
        f"[label]Status:[/label] {account.status}"
    )


def build_categories_table(categories: list[Category]) -> Table:
    """Build a Rich Table of active accounts.

    Args:
        categories (list[Category]): List of Category objects

    Returns:
        Table: Rich Table object
    """
    table = Table(title="Categories")
    table.add_column("Name", style="col.name")
    table.add_column("Side", style="col.side")
    for category in categories:
        category_name = category.name if category else "Unknown"
        side_value = category.side.value if category else "Unknown"
        table.add_row(category_name, side_value)
    return table


def build_institutions_table(institutions: list[InstitutionListItem]) -> Table:
    """Build a Rich table of institutions with usage counts."""
    table = Table(title="Institutions")
    table.add_column("ID", justify="right", style="col.id", no_wrap=True)
    table.add_column("Name", style="col.name")
    table.add_column("Description", style="col.desc")
    table.add_column("Accounts", justify="right", style="col.count")
    for item in institutions:
        institution = item.institution
        table.add_row(
            str(institution.id),
            institution.name,
            institution.description or "",
            str(item.account_count),
        )
    return table


def build_indexed_categories_table(categories: list[Category]) -> Table:
    """Build a Rich Table of categories with index.

    Args:
        categories (list[Category]): List of Category objects

    Returns:
        Table: Rich Table object
    """
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


def render_institution_data(
    console: Console, institution: Institution, account_count: int | None = None
) -> None:
    """Render institution details and optional linked-account count."""
    text = (
        f"[label]Institution ID:[/label] {institution.id}\n"
        f"[label]Institution name:[/label] {institution.name}\n"
        f"[label]Description:[/label] {institution.description or ''}"
    )
    if account_count is not None:
        text += f"\n[label]Linked accounts:[/label] {account_count}"
    console.print(text)


def build_balance_counts_table(balance_counts: list[tuple[Month, int]]) -> Table:
    """Build a Rich Table of balances per month.

    Args:
        balance_counts: List of tuples (Month, count of balances)

    Returns:
        Table: Rich Table object
            idx (starts at 1) | month | count
    """
    table = Table(title="Balance Entries per Month")
    table.add_column("Index", justify="right", style="col.id")
    table.add_column("Month", style="col.month")
    table.add_column("Balances", justify="right", style="col.count")
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
    table.add_column("Category", style="col.category")
    table.add_column("Side", style="col.side")
    table.add_column("Total", justify="right", style="col.total")
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
    title_suffix: str = "",
) -> Table:
    """Build a Rich Table of balances.

    Args:
        balances (list[Balance]): List of Balance objects
        title_suffix (str): Suffix for table title

    Returns:
        Table: Rich Table object
    """
    _title = "Balances" + (f" {title_suffix}" if title_suffix else "")
    table = Table(title=_title)
    table.add_column("Acct_ID", justify="right", style="col.id", no_wrap=True)
    table.add_column("Account Name", style="col.name")
    table.add_column("Category", style="col.category")
    table.add_column("Side", style="col.side")
    table.add_column("Amount", justify="right", style="col.amount")
    for balance in balances:
        account = balance.account
        category = account.category if account else None
        account_name = account.name if account else "Unknown"
        category_name = category.name if category else "Unknown"
        side = category.side.value if category else "Unknown"
        table.add_row(
            str(balance.account_id),
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
        table.add_column("Side", style="col.name")
        table.add_column("Total", justify="right", style="col.total")
        table.add_row("Assets", f"{nw.assets:9,}")
        table.add_row("Liabilities", f"{nw.liabilities:9,}")
        table.add_row("Net Worth", f"{nw.net_worth:9,}")
    elif form == "wide":
        table.add_column("Assets", justify="right", style="col.asset")
        table.add_column("Liabilities", justify="right", style="col.liability")
        table.add_column("Net Worth", justify="right", style="col.networth")
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


def build_status_table(status_options: list[Status]) -> Table:
    """Build a Rich Table of status options.

    Args:
        status_options (list[Status]): List of Status enum options

    Returns:
        Table: Rich Table object
    """
    table = Table(title="Status Options")
    table.add_column("Index", justify="right", style="col.id", no_wrap=True)
    table.add_column("Status", style="col.status")
    for k, status in enumerate(status_options):
        table.add_row(
            str(k + 1),
            status.value,
        )
    return table


def render_new_account_info(
    console: Console,
    account: Account,
    balance: Balance,
    institution_name: str | None = None,
) -> None:
    """Render information about a newly created account.

    Args:
        console: Rich Console object
        account: Account object
        balance: Balance object
    """
    console.print(
        f"[label]Account name:[/label] {account.name}\n"
        f"[label]Account ID:[/label] {account.id}\n"
        f"[label]Description:[/label] {account.description}\n"
        f"[label]Currency:[/label] {account.currency_code}\n"
        f"[label]Category:[/label] {account.category_name}\n"
        f"[label]Institution:[/label] "
        f"{institution_name or format_institution_name(account)}\n"
        f"[label]Status:[/label] {account.status.value}\n"
        f"[label]Initial month:[/label] {balance.month}\n"
        f"[label]Initial balance:[/label] {balance.amount}\n"
    )


def render_category_data(console: Console, category: Category) -> None:
    console.print(
        f"[label]Category name:[/label] {category.name}\n"
        f"[label]Category side:[/label] {category.side.value}\n"
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
    table.add_column("Repo", style="col.code", no_wrap=True)
    table.add_column("Path", style="col.name")
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
    table = Table(title=f"[header]{_title}[/header]")
    table.add_column("Month", justify="right")
    table.add_column("Assets", justify="right", style="col.asset")
    table.add_column("Liabilities", justify="right", style="col.liability")
    table.add_column("Net Worth", justify="right", style="col.networth")
    table.add_column("Change", justify="right")
    for k, nw in enumerate(nws):
        if k > 0:
            change = nw.net_worth - nws[k - 1].net_worth
            color_str = "delta.negative" if change < 0 else "delta.positive"
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
    table.add_column("Index", justify="right", style="col.id")
    table.add_column("Month", style="col.month")
    table.add_column("Balances", justify="right", style="col.count")
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
    table.add_column("Assets", justify="right", style="col.asset")
    table.add_column("Liabilities", justify="right", style="col.liability")
    table.add_column("Net Worth", justify="right", style="col.networth")

    changes_abs = (f"{changes[k][0]:,}" for k in ["assets", "liabilities", "net_worth"])
    changes_pct = (
        f"({changes[k][1]:.0%})" for k in ["assets", "liabilities", "net_worth"]
    )
    table.add_row(*changes_abs)
    table.add_row(*changes_pct)
    return table
