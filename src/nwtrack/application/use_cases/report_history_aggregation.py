"""Shared history aggregation use case."""

from collections.abc import Callable

from nwtrack.application.dto import (
    AggregationDimension,
    HistoryAggregationRequest,
    HistoryAggregationResult,
    OperationResult,
)
from nwtrack.application.ports.uow import UnitOfWork


class ReportHistoryAggregation:
    """Run one shared grouped-balance query for an inclusive month range."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow

    def run(
        self,
        request: HistoryAggregationRequest,
    ) -> OperationResult[HistoryAggregationResult]:
        """Validate the request and return grouped totals across the range."""
        if request.end_month < request.start_month:
            return OperationResult(
                success=False,
                error_message=(
                    "Start month must be earlier than or equal to end month."
                ),
            )

        with self._uow() as uow:
            if (
                request.dimension != AggregationDimension.CURRENCY
                and request.currency_code is None
            ):
                currencies = uow.reporting.get_range_currencies(
                    request.start_month,
                    request.end_month,
                    request.status_scope,
                )
                if len(currencies) > 1:
                    return OperationResult(
                        success=False,
                        error_message=(
                            "Aggregation requires one currency. "
                            "Provide currency_code for mixed-currency ranges."
                        ),
                    )

            result = uow.reporting.aggregate_history(request)

        return OperationResult(success=True, data=result)
