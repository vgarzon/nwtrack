""" """

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt

from nwtrack.domain.value_objects import Month


def prompt_for_month(console: Console) -> Month:
    """Prompt for year and month with defaults to current month.

    Returns:
        Month: Month object
    """
    from datetime import date

    today = date.today()
    int_prompt = IntPrompt(console=console)
    while True:
        _year = int_prompt.ask("Enter [bold]year[/bold] as 'YYYY'", default=today.year)
        _month = int_prompt.ask(
            "Enter [bold]month[/bold] as 'MM'",
            default=today.month,
            choices=[str(k) for k in range(1, 13)],
        )
        try:
            month = Month(year=_year, month=_month)
        except ValueError:
            console.print("[error]Invalid month format. Please use YYYY-MM.[/error]")
            continue
        break
    return month


def prompt_for_month_choice(
    console: Console, balance_counts: list[tuple[Month, int]]
) -> str:
    """Prompt user to choose month input method.

    Args:
        console (Console): Rich Console object
        balance_counts (list): List of balance counts per month

    Returns:
        str: User choice
    """
    from nwtrack.entrypoints.cli.ui.renderers import build_balance_counts_table

    prompt = Prompt(console=console)
    n_months = len(balance_counts)
    table = build_balance_counts_table(balance_counts)
    console.print(table)
    console.print(
        "Options:\n  [bold]A.[/bold] Enter year and month\n  [bold]Q.[/bold] Quit"
    )
    choice = prompt.ask(
        "[bold]Enter choice[/bold]",
        choices=[str(i + 1) for i in range(n_months)] + ["A", "Q"],
        default="1",
        case_sensitive=False,
    )
    return choice.lower().strip()


def prompt_for_account_name(console: Console) -> str:
    """Prompt user for account name.

    Args:
        console (Console): Rich Console object

    Returns:
        str: Account name
    """
    prompt = Prompt(console=console)
    name = prompt.ask("Enter [bold]account name[/bold] or 'q' to quit")
    return name.strip()


def prompt_for_account_description(console: Console) -> str:
    """Prompt user for account description.

    Args:
        console (Console): Rich Console object

    Returns:
        str: Account description
    """
    prompt = Prompt(console=console)
    name = prompt.ask("Enter optional [bold]description[/bold] or 'q' to quit")
    return name.strip()


def prompt_for_account_id(console: Console) -> int | None:
    """Prompt user for account ID.

    Args:
        console (Console): Rich Console object

    Returns:
        int | None: Account ID or None if user quits
    """
    prompt = Prompt(console=console)
    while True:
        response = prompt.ask("Enter [bold]account ID[/bold] or 'q' to quit")
        if response.lower().strip() == "q":
            return None
        try:
            account_id = int(response)
            return account_id
        except ValueError:
            console.print(
                "[error]Invalid input. Please enter a valid account ID.[/error]"
            )


def prompt_for_category_choice(console: Console, n_categories: int = 0) -> int:
    """Prompt user to choose category input method.

    Args:
        console (Console): Rich Console object
        n_categories (int): Length of categories list

    Returns:
        int: User choice
    """
    int_prompt = IntPrompt(console=console)
    choice = int_prompt.ask(
        "Enter [bold]category index[/bold] or '0' to quit",
        default=0,  # 0 to quit
        choices=[str(i) for i in range(n_categories + 1)],
    )
    return choice


def prompt_for_currency_choice(console: Console, n_currencies: int = 0) -> int:
    """Prompt user to choose currency input method.

    Args:
        console (Console): Rich Console object
        n_currencies (int): Length of currencies list

    Returns:
        int: User choice
    """
    int_prompt = IntPrompt(console=console)
    choice = int_prompt.ask(
        "Enter [bold]currency index[/bold] or '0' to quit",
        default=1,  # assumes USD is choise 1
        choices=[str(i) for i in range(n_currencies + 1)],
    )
    return choice


def prompt_to_confirm_action(console: Console, action: str = "") -> bool:
    """Prompt user to confirm action."""
    confirm = Confirm(console=console)
    answer = confirm.ask(f"[bold]{action}[/bold]")
    return answer


def prompt_for_balance_amount(console: Console) -> int:
    """Prompt user for initial balance amount.

    Args:
        console (Console): Rich Console object
    Returns:
        int: Balance amount
    from rich.prompt import FloatPrompt
    """
    int_prompt = IntPrompt(console=console)
    amount = int_prompt.ask(
        "Enter initial [bold]balance amount[/bold] (integer)",
        default=0,
    )
    return amount


def prompt_for_status_choice(console: Console, n_options) -> int:
    """Prompt user to choose account status.

    Args:
        console (Console): Rich Console object
        n_options (int): Number of status options

    Returns:
        int: User choice
    """
    int_prompt = IntPrompt(console=console)
    choice = int_prompt.ask(
        "Select [bold]account status[/bold] by index or '0' to quit",
        default=1,  # assumes 'active' is choice 1 (index 0)
        choices=[str(i) for i in range(n_options + 1)],
    )
    return choice


def prompt_for_category_name(console: Console) -> str:
    """Prompt user for category name.

    Args:
        console (Console): Rich Console object
    Returns:
        str: Category name
    """
    prompt = Prompt(console=console)
    name = prompt.ask("Enter [bold]category name[/bold] or 'q' to quit")
    return name.strip()


def prompt_for_category_side(console: Console) -> str:
    """Prompt user for category side.

    Args:
        console (Console): Rich Console object
    Returns:
        Side: Category side
    """
    from nwtrack.domain.models import Side

    prompt = Prompt(console=console)
    choice = prompt.ask(
        "Enter [bold]side[/bold] or 'q' to quit",
        choices=[side.value for side in Side] + ["q"],
        default=Side.ASSET.value,
    )
    return choice
