"""
CLI balance commands
"""

from nwtrack.entrypoints.cli.app import balances_app


@balances_app.command("roll")
def roll_balances_forward_interactive():
    """
    Roll balances forward interactively.
    """
    import nwtrack.application.use_cases.roll_balances_forward as roll_balances_forward

    roll_balances_forward.main()


@balances_app.command("update")
def update_balances_interactive():
    """
    Update balances interactively.
    """
    import nwtrack.application.use_cases.update_balances as update_balances

    update_balances.main()


@balances_app.command("delete")
def delete_balance_interactive():
    """
    Delete a balance entry interactively.
    """
    import nwtrack.application.use_cases.delete_balance as delete_balance

    delete_balance.main()
