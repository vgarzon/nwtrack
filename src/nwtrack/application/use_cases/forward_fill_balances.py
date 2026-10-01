"""
Forward-fill balances for months missing between the latest balance month and today.
"""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.value_objects import Month

logger = logging.getLogger(__name__)


class ForwardFillBalances:
    """Detect and fill the trailing gap of months without balances.

    Each missing month is copied from the month before it, so values chain
    forward. Only accounts active in the target month are carried over.
    """

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        fetcher: FetchService,
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher

    def find_gap(self, today: Month) -> list[Month]:
        """Return months after the latest balance month through ``today``.

        Returns an empty list when there are no balances at all or the latest
        balance month is not before ``today``.
        """
        recent = self._fetcher.get_recent_months(n_months=1)
        if not recent:
            return []
        return recent[0].months_through(today)

    def run(self, months: list[Month]) -> OperationResult[int]:
        """Fill ``months`` (ascending, contiguous) in a single transaction.

        The first month is copied from the month before it; each later month
        from its predecessor. Any failure rolls back every month.

        Returns:
            OperationResult whose data is the total number of balances created.
        """
        if not months:
            return OperationResult(success=True, data=0)

        total = 0
        try:
            with self._uow() as uow:
                source = self._previous_month(months[0])
                for target in months:
                    count = uow.balances.copy_active_by_month(source, target)
                    if count == 0:
                        logger.warning(
                            "No balances copied from %s to %s. Rolling back.",
                            source,
                            target,
                        )
                        uow.rollback()
                        return OperationResult(
                            success=False,
                            error_message=f"No balances to carry into {target}.",
                        )
                    total += count
                    source = target
        except Exception:
            logger.exception("Forward fill failed.")
            return OperationResult(
                success=False, error_message="Failed to forward-fill balances."
            )
        logger.info("Forward-filled %d months (%d balances).", len(months), total)
        return OperationResult(success=True, data=total)

    @staticmethod
    def _previous_month(month: Month) -> Month:
        if month.month == 1:
            return Month(month.year - 1, 12)
        return Month(month.year, month.month - 1)
