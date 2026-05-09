"""CLI institution commands."""

from nwtrack.entrypoints.cli.app import institutions_app


@institutions_app.command("list")
def list_institutions_interactive():
    """List institutions."""
    import nwtrack.application.use_cases.list_institutions as list_institutions

    list_institutions.main()


@institutions_app.command("create")
def create_institution_interactive():
    """Create a new institution interactively."""
    import nwtrack.application.use_cases.create_institution as create_institution

    create_institution.main()


@institutions_app.command("update")
def update_institution_interactive():
    """Update an institution interactively."""
    import nwtrack.application.use_cases.update_institution as update_institution

    update_institution.main()


@institutions_app.command("delete")
def delete_institution_interactive():
    """Delete an institution interactively."""
    import nwtrack.application.use_cases.delete_institution as delete_institution

    delete_institution.main()
