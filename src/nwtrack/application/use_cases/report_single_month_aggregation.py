"""Shared single-month aggregation use case."""

from collections.abc import Callable

from nwtrack.application.dto import (
    AggregationDimension,
    OperationResult,
    SingleMonthAggregationRequest,
    SingleMonthAggregationResult,
)
from nwtrack.application.ports.uow import UnitOfWork


class ReportSingleMonthAggregation:
    """Run one shared grouped-balance query for a single month."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow

    def run(
        self, request: SingleMonthAggregationRequest
    ) -> OperationResult[SingleMonthAggregationResult]:
        """Validate the request and return grouped totals."""
        with self._uow() as uow:
            if (
                request.dimension != AggregationDimension.CURRENCY
                and request.currency_code is None
            ):
                currencies = uow.reporting.get_month_currencies(
                    request.month,
                    request.status_scope,
                )
                if len(currencies) > 1:
                    return OperationResult(
                        success=False,
                        error_message=(
                            "Aggregation requires one currency. "
                            "Provide currency_code for mixed-currency months."
                        ),
                    )

            result = uow.reporting.aggregate_single_month(request)

        return OperationResult(success=True, data=result)
