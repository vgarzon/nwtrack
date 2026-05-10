"""Shared helpers for tag administration workflows."""

from nwtrack.application.dto import TagListItem
from nwtrack.application.ports.uow import UnitOfWork


def list_tag_items(uow: UnitOfWork) -> list[TagListItem]:
    """Build tag list rows with linked-account counts."""
    tags = sorted(
        uow.tags.get_all(),
        key=lambda tag: tag.id,
    )
    return [
        TagListItem(
            tag=tag,
            account_count=uow.tags.count_linked_accounts(tag.id),
        )
        for tag in tags
    ]
