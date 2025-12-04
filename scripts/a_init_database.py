"""
`nwtracK`: Net worth tracker app.
Prototype initializing SQLite database from DDL script.
"""

import sqlite3

from nwtrack.config import settings


def init_db_from_ddl_script(ddl_script_path: str) -> None:
    conn = sqlite3.connect(settings.db_file_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    with open(ddl_script_path, "r") as f:
        ddl_script = f.read()

    cursor.executescript(ddl_script)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("Database file path:", settings.db_file_path)
    init_db_from_ddl_script("sql/nwtrack_ddl.sql")
