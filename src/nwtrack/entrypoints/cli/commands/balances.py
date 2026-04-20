"""
CLI balance commands
"""

import sys

from nwtrack.entrypoints.cli.app import balances_app


@balances_app.command("roll")
def roll_balances_forward_interactive():
    """
    Roll balances forward interactively.
    """
    import nwtrack.application.use_cases.roll_balances_forward as roll_balances_forward

    sys.exit(roll_balances_forward.main())


@balances_app.command("update")
def update_balances_interactive():
    """
    Update balances interactively.
    """
    import nwtrack.application.use_cases.update_balances as update_balances

    sys.exit(update_balances.main())


@balances_app.command("delete")
def delete_balance_interactive():
    """
    Delete a balance entry interactively.
    """
    import nwtrack.application.use_cases.delete_balance as delete_balance

    sys.exit(delete_balance.main())


@balances_app.command("transfer")
def transfer_balance_interactive():
    """
    Transfer funds between accounts for a selected month.
    """
    import nwtrack.application.use_cases.transfer_balance as transfer_balance

    sys.exit(transfer_balance.main())
