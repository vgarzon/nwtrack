""" """

from rich.console import Console
from rich.prompt import IntPrompt, Prompt
from nwtrack.domain.models import Month


def prompt_for_month(console: Console) -> Month:
    """Input a specific month from user.

    Returns:
        Month: Month object
    """
    from datetime import date

    today = date.today()
    int_prompt = IntPrompt(console=console)
    while True:
        _year = int_prompt.ask("Enter year as 'YYYY'", default=today.year)
        _month = int_prompt.ask("Enter month as 'MM'", default=today.month)
        try:
            month = Month(year=_year, month=_month)
        except ValueError:
            console.print("[red]Invalid month format. Please use YYYY-MM.[/red]")
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
