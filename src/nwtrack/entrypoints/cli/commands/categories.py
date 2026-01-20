"""
CLI category commands
"""

from nwtrack.entrypoints.cli.app import categories_app


@categories_app.command("list")
def list_categories_interactive():
    """
    List categories
    """
    import nwtrack.application.use_cases.list_categories as list_categories

    list_categories.main()


@categories_app.command("create")
def create_category_interactive():
    """
    Create a new category interactively.
    """
    import nwtrack.application.use_cases.create_category as create_category

    create_category.main()
