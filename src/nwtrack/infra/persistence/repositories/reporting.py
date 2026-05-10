"""SQLAlchemy implementation of reporting queries."""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    MonthlyCategoryBalance,
    SingleMonthAggregationGroup,
    SingleMonthAggregationRequest,
    SingleMonthAggregationResult,
)
from nwtrack.domain.value_objects import Month
from nwtrack.infra.persistence.orm.models import (
    Account,
    Balance,
    Category,
    Institution,
    Side,
    Status,
    Tag,
    account_tags_table,
)
from nwtrack.infra.persistence.orm.models import Category as CategoryModel

logger = logging.getLogger(__name__)


class ReportingQueries:
    """SQLAlchemy-based implementation of reporting queries."""

    def __init__(self, session: Session):
        """Initialize reporting queries with SQLAlchemy session."""
        self._session = session

    def get_month_currencies(
        self, month: Month, status_scope: AccountStatusScope
    ) -> list[str]:
        """List distinct currencies present for one month and status filter."""
        stmt = (
            select(Account.currency_code)
            .select_from(Balance)
            .join(Account, Balance.account_id == Account.id)
            .where(Balance.month == month)
        )
        stmt = self._apply_status_scope(stmt, status_scope).distinct().order_by(
            Account.currency_code
        )
        results = self._session.execute(stmt).scalars().all()
        return list(results)

    def aggregate_single_month(
        self, request: SingleMonthAggregationRequest
    ) -> SingleMonthAggregationResult:
        """Group balances for one month by a supported account attribute."""
        if request.dimension == AggregationDimension.CATEGORY:
            groups = self._aggregate_by_category(request)
        elif request.dimension == AggregationDimension.SIDE:
            groups = self._aggregate_by_side(request)
        elif request.dimension == AggregationDimension.INSTITUTION:
            groups = self._aggregate_by_institution(request)
        elif request.dimension == AggregationDimension.CURRENCY:
            groups = self._aggregate_by_currency(request)
        elif request.dimension == AggregationDimension.TAG:
            groups = self._aggregate_by_tag(request)
        else:
            raise ValueError(f"Unsupported aggregation dimension: {request.dimension}")

        return SingleMonthAggregationResult(
            month=request.month,
            dimension=request.dimension,
            currency_code=self._resolve_result_currency_code(request, groups),
            status_scope=request.status_scope,
            groups=groups,
        )

    def monthly_balance_total_by_category(
        self, month: Month
    ) -> list[MonthlyCategoryBalance]:
        """Get total balance amount by category name for a given month."""
        stmt = (
            select(
                Category.name,
                Category.side,
                func.sum(Balance.amount).label("total_amount"),
            )
            .join(Account, Balance.account_id == Account.id)
            .join(Category, Account.category_name == Category.name)
            .where(Balance.month == month)
            .group_by(Category.name, Category.side)
            .order_by(Category.side, Category.name)
        )

        results = self._session.execute(stmt).all()

        return [
            MonthlyCategoryBalance(
                month=month,
                category=CategoryModel(name=row.name, side=Side(row.side)),
                amount=row.total_amount if row.total_amount is not None else 0,
            )
            for row in results
        ]

    def _aggregate_by_category(
        self, request: SingleMonthAggregationRequest
    ) -> list[SingleMonthAggregationGroup]:
        stmt = (
            select(
                Category.name.label("name"),
                Account.currency_code.label("currency_code"),
                func.sum(Balance.amount).label("total_amount"),
            )
            .join(Account, Balance.account_id == Account.id)
            .join(Category, Account.category_name == Category.name)
            .where(Balance.month == request.month)
        )
        stmt = self._apply_request_filters(stmt, request).group_by(
            Category.name,
            Account.currency_code,
        )
        rows = self._session.execute(stmt).all()

        groups = [
            SingleMonthAggregationGroup(
                group_key=row.name,
                label=row.name,
                amount=row.total_amount or 0,
                currency_code=row.currency_code,
            )
            for row in rows
        ]
        return self._sort_groups(groups)

    def _aggregate_by_side(
        self, request: SingleMonthAggregationRequest
    ) -> list[SingleMonthAggregationGroup]:
        stmt = (
            select(
                Category.side.label("side"),
                Account.currency_code.label("currency_code"),
                func.sum(Balance.amount).label("total_amount"),
            )
            .join(Account, Balance.account_id == Account.id)
            .join(Category, Account.category_name == Category.name)
            .where(Balance.month == request.month)
        )
        stmt = self._apply_request_filters(stmt, request).group_by(
            Category.side,
            Account.currency_code,
        )
        rows = self._session.execute(stmt).all()

        groups = [
            SingleMonthAggregationGroup(
                group_key=row.side.value,
                label=row.side.value,
                amount=row.total_amount or 0,
                currency_code=row.currency_code,
            )
            for row in rows
        ]
        return self._sort_groups(groups)

    def _aggregate_by_institution(
        self, request: SingleMonthAggregationRequest
    ) -> list[SingleMonthAggregationGroup]:
        stmt = (
            select(
                Institution.id.label("institution_id"),
                Institution.name.label("institution_name"),
                Account.currency_code.label("currency_code"),
                func.sum(Balance.amount).label("total_amount"),
            )
            .join(Account, Balance.account_id == Account.id)
            .outerjoin(Institution, Account.institution_id == Institution.id)
            .where(Balance.month == request.month)
        )
        stmt = self._apply_request_filters(stmt, request).group_by(
            Institution.id,
            Institution.name,
            Account.currency_code,
        )
        rows = self._session.execute(stmt).all()

        groups = [
            SingleMonthAggregationGroup(
                group_key=(
                    f"institution:{row.institution_id}"
                    if row.institution_id is not None
                    else "unassigned"
                ),
                label=(
                    row.institution_name
                    if row.institution_id is not None
                    else "Unassigned"
                ),
                amount=row.total_amount or 0,
                currency_code=row.currency_code,
            )
            for row in rows
        ]
        return self._sort_groups(groups)

    def _aggregate_by_currency(
        self, request: SingleMonthAggregationRequest
    ) -> list[SingleMonthAggregationGroup]:
        stmt = (
            select(
                Account.currency_code.label("currency_code"),
                func.sum(Balance.amount).label("total_amount"),
            )
            .join(Account, Balance.account_id == Account.id)
            .where(Balance.month == request.month)
        )
        stmt = self._apply_request_filters(
            stmt,
            request,
        ).group_by(Account.currency_code)
        rows = self._session.execute(stmt).all()

        groups = [
            SingleMonthAggregationGroup(
                group_key=row.currency_code,
                label=row.currency_code,
                amount=row.total_amount or 0,
                currency_code=row.currency_code,
            )
            for row in rows
        ]
        return self._sort_groups(groups)

    def _aggregate_by_tag(
        self, request: SingleMonthAggregationRequest
    ) -> list[SingleMonthAggregationGroup]:
        stmt = (
            select(
                Tag.id.label("tag_id"),
                Tag.name.label("tag_name"),
                Account.currency_code.label("currency_code"),
                func.sum(Balance.amount).label("total_amount"),
            )
            .join(Account, Balance.account_id == Account.id)
            .outerjoin(
                account_tags_table,
                account_tags_table.c.account_id == Account.id,
            )
            .outerjoin(Tag, Tag.id == account_tags_table.c.tag_id)
            .where(Balance.month == request.month)
        )
        stmt = self._apply_request_filters(stmt, request).group_by(
            Tag.id,
            Tag.name,
            Account.currency_code,
        )
        rows = self._session.execute(stmt).all()

        groups = [
            SingleMonthAggregationGroup(
                group_key=f"tag:{row.tag_id}" if row.tag_id is not None else "untagged",
                label=row.tag_name if row.tag_id is not None else "Untagged",
                amount=row.total_amount or 0,
                currency_code=row.currency_code,
            )
            for row in rows
        ]
        return self._sort_groups(groups)

    def _apply_request_filters(self, stmt, request: SingleMonthAggregationRequest):
        """Apply status scope and optional currency filter to a statement."""
        stmt = self._apply_status_scope(stmt, request.status_scope)
        if request.currency_code is not None:
            stmt = stmt.where(Account.currency_code == request.currency_code)
        return stmt

    def _apply_status_scope(self, stmt, status_scope: AccountStatusScope):
        """Apply account status filtering when requested."""
        if status_scope == AccountStatusScope.ACTIVE:
            stmt = stmt.where(Account.status == Status.ACTIVE)
        return stmt

    def _resolve_result_currency_code(
        self,
        request: SingleMonthAggregationRequest,
        groups: list[SingleMonthAggregationGroup],
    ) -> str | None:
        """Resolve the result-level currency code from request and grouped rows."""
        if request.currency_code is not None:
            return request.currency_code

        currencies = sorted({group.currency_code for group in groups})
        if len(currencies) == 1:
            return currencies[0]

        return None

    def _sort_groups(
        self,
        groups: list[SingleMonthAggregationGroup],
    ) -> list[SingleMonthAggregationGroup]:
        """Return deterministic ordering across aggregation dimensions."""
        side_order = {
            Side.ASSET.value: 0,
            Side.LIABILITY.value: 1,
        }
        special_last = {"Unassigned", "Untagged"}

        return sorted(
            groups,
            key=lambda group: (
                0 if group.label in side_order else 1,
                side_order.get(group.label, 0),
                1 if group.label in special_last else 0,
                group.label,
            ),
        )
