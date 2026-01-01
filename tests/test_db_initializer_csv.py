"""
Test DBInitializerCSV class methods.
"""

import pytest

from nwtrack.services import ReportService
from nwtrack.use_cases import DBInitializerCSV


def test_db_initializer_csv_yes(
    test_container, test_file_paths, monkeypatch, capsys
) -> None:
    db_initializer = DBInitializerCSV(test_container)
    inputs = iter(["YES"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    db_initializer.run(test_file_paths)
    captured = capsys.readouterr()
    assert "Database initialization complete." in captured.out
    report_svc = test_container.resolve(ReportService)
    balances = report_svc.get_balances_by_account_id(1)
    assert len(balances) == 12
    assert balances[11].amount == 200


def test_db_initializer_csv_quit(
    test_container, test_file_paths, monkeypatch, capsys
) -> None:
    db_initializer = DBInitializerCSV(test_container)
    inputs = iter(["no"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    db_initializer.run(test_file_paths)
    captured = capsys.readouterr()
    assert "Quitting." in captured.out


def test_db_initializer_csv_missing_key(test_container, test_file_paths) -> None:
    db_initializer = DBInitializerCSV(test_container)
    incomplete_file_paths = test_file_paths.copy()
    del incomplete_file_paths["accounts"]

    with pytest.raises(KeyError) as exc_info:
        db_initializer.run(incomplete_file_paths)
    assert "Missing required file paths for keys" in str(exc_info.value)
    assert "accounts" in str(exc_info.value)


def test_db_initializer_csv_invalid_path(test_container, test_file_paths) -> None:
    db_initializer = DBInitializerCSV(test_container)
    invalid_file_paths = test_file_paths.copy()
    invalid_file_paths["accounts"] = "invalid/path/accounts.csv"

    with pytest.raises(FileNotFoundError) as exc_info:
        db_initializer.run(invalid_file_paths)
    assert "Path for 'accounts' is not a file" in str(exc_info.value)
    assert "invalid/path/accounts.csv" in str(exc_info.value)
