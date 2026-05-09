"""Schema tests for institution persistence foundations."""

from sqlalchemy import inspect

from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager


def test_schema_includes_institutions_table(base_container) -> None:
    """Ensure metadata-driven schema creation includes the institutions table."""
    engine = base_container.resolve(SQLiteSessionManager).engine
    inspector = inspect(engine)

    table_names = inspector.get_table_names()
    institution_columns = {
        column["name"] for column in inspector.get_columns("institutions")
    }

    assert "institutions" in table_names
    assert institution_columns == {"id", "name", "description"}
