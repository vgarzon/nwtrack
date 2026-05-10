"""Schema tests for tag persistence foundations."""

from sqlalchemy import inspect

from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager


def test_schema_includes_tags_table(base_container) -> None:
    """Ensure metadata-driven schema creation includes the tags table."""
    engine = base_container.resolve(SQLiteSessionManager).engine
    inspector = inspect(engine)

    table_names = inspector.get_table_names()
    tag_columns = {column["name"] for column in inspector.get_columns("tags")}

    assert "tags" in table_names
    assert tag_columns == {"id", "name", "description"}
