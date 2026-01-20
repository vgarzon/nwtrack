"""
CLI category commands
"""

from nwtrack.entrypoints.cli.app import categories_app


# TODO: Enable listing categories once implemented
# @categories_app.command("list")
# def list_categories_interactive(active_only: bool = True):
#     """
#     List categories
#     """
#     import nwtrack.application.use_cases.list_categories as list_categories
#
#     list_categories.main(active_only=active_only)


@categories_app.command("create")
def create_category_interactive():
    """
    Create a new category interactively.
    """
    import nwtrack.application.use_cases.create_category as create_category

    create_category.main()
