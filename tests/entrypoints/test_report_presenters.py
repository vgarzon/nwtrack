"""Tests for report presenter behavior."""

from typing import cast

from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.adapters.report_presenters import (
    RichSingleMonthAggregationReportPresenter,
)
from nwtrack.entrypoints.cli.ui.console import ConsoleSettings, build_console


class FakeFetchService:
    """Minimal fetcher stub for presenter tests."""

    def check_month_in_balances(self, month: Month) -> bool:
        return True


def test_aggregated_report_month_prompt_defaults_to_most_complete_recent_month(
    monkeypatch,
) -> None:
    """Enter should select the recent month with the highest balance count."""
    presenter = RichSingleMonthAggregationReportPresenter(
        fetcher=cast("FetchService", FakeFetchService()),
        console=build_console(ConsoleSettings(record=True)),
    )
    observed_default: str | None = None

    def fake_ask(*args, **kwargs):
        nonlocal observed_default
        observed_default = kwargs["default"]
        return kwargs["default"]

    monkeypatch.setattr(presenter._prompt, "ask", fake_ask)

    selected_month = presenter.prompt_for_month_choice(
        [
            (Month(2026, 5), 1),
            (Month(2026, 4), 1),
            (Month(2025, 12), 9),
        ]
    )

    assert observed_default == "3"
    assert selected_month == Month(2025, 12)
