"""Tests for the ShowConfig use case."""

from pathlib import Path

from nwtrack.application.dto import (
    ConfigFieldInfo,
    ConfigPathInfo,
    ConfigShowResult,
    ConfigValueSource,
)
from nwtrack.application.use_cases.show_config import ShowConfig


class MockShowConfigPresenter:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.shown_paths: list[ConfigPathInfo] | None = None
        self.shown_fields: list[ConfigFieldInfo] | None = None

    def display_search_paths(self, paths: list[ConfigPathInfo]) -> None:
        self.calls.append("display_search_paths")
        self.shown_paths = paths

    def display_settings(self, fields: list[ConfigFieldInfo]) -> None:
        self.calls.append("display_settings")
        self.shown_fields = fields


def test_run_displays_search_paths_and_settings(monkeypatch) -> None:
    fake_result = ConfigShowResult(
        search_paths=[
            ConfigPathInfo(path=Path("/a/config.toml"), exists=True, is_active=True),
            ConfigPathInfo(path=Path("/b/config.toml"), exists=False, is_active=False),
        ],
        fields=[
            ConfigFieldInfo(
                name="db_file_path",
                value="/a/nwtrack.db",
                source=ConfigValueSource.FILE,
            ),
        ],
    )
    monkeypatch.setattr(
        "nwtrack.application.use_cases.show_config.describe_settings",
        lambda: fake_result,
    )
    presenter = MockShowConfigPresenter()

    result = ShowConfig(presenter).run()

    assert result.success
    assert presenter.calls == ["display_search_paths", "display_settings"]
    assert presenter.shown_paths == fake_result.search_paths
    assert presenter.shown_fields == fake_result.fields
