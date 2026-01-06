"""
Define configuration settings dataclass.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_file_path: str
    db_ddl_path: str
