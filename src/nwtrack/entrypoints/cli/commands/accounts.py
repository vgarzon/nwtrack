"""
CLI account commands
"""

from nwtrack.entrypoints.cli.app import accounts_app


@accounts_app.command("list")
def list_accounts_interactive(active_only: bool = True):
    """
    List accounts
    """
    import sys

    import nwtrack.application.use_cases.list_accounts as list_accounts

    sys.exit(list_accounts.main(active_only=active_only))


@accounts_app.command("create")
def create_account_interactive():
    """
    Create a new account interactively.
    """
    import nwtrack.application.use_cases.create_account as create_account

    create_account.main()


@accounts_app.command("update")
def update_account_info_interactive():
    """
    Update account information interactively.
    """
    import nwtrack.application.use_cases.update_account_info as update_account_info

    update_account_info.main()
