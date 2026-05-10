"""Shared helpers for tag administration workflows."""

import re

from nwtrack.application.dto import TagListItem
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.domain.models import Tag

_REPEATED_WHITESPACE = re.compile(r"\s+")


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


def normalize_tag_name(name: str) -> str:
    """Normalize tag names for duplicate checks and persistence."""
    normalized = _REPEATED_WHITESPACE.sub(" ", name.strip())
    return normalized.lower()


def normalized_tag(tag: Tag) -> Tag:
    """Return a tag copy with the canonical normalized name."""
    normalized = Tag(
        name=normalize_tag_name(tag.name),
        description=tag.description,
    )
    if getattr(tag, "id", None):
        normalized.id = tag.id
    return normalized
