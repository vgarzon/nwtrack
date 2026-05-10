"""CLI tag commands."""

from nwtrack.entrypoints.cli.app import tags_app


@tags_app.command("list")
def list_tags_interactive():
    """List tags."""
    import nwtrack.application.use_cases.list_tags as list_tags

    list_tags.main()


@tags_app.command("create")
def create_tag_interactive():
    """Create a new tag interactively."""
    import nwtrack.application.use_cases.create_tag as create_tag

    create_tag.main()


@tags_app.command("update")
def update_tag_interactive():
    """Update a tag interactively."""
    import nwtrack.application.use_cases.update_tag as update_tag

    update_tag.main()


@tags_app.command("delete")
def delete_tag_interactive():
    """Delete a tag interactively."""
    import nwtrack.application.use_cases.delete_tag as delete_tag

    delete_tag.main()
