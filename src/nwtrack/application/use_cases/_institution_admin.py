"""Shared helpers for institution administration workflows."""

from nwtrack.application.dto import InstitutionListItem
from nwtrack.application.ports.uow import UnitOfWork


def list_institution_items(uow: UnitOfWork) -> list[InstitutionListItem]:
    """Build institution list rows with linked-account counts."""
    institutions = sorted(
        uow.institutions.get_all(),
        key=lambda institution: institution.id,
    )
    return [
        InstitutionListItem(
            institution=institution,
            account_count=uow.institutions.count_linked_accounts(institution.id),
        )
        for institution in institutions
    ]
