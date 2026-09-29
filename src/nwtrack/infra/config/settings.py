"""
Define configuration settings dataclass.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_file_path: str
    log_file: str
    log_file_level: str
    log_rotation_mb: int
    log_backup_count: int
    change_warning_threshold_pct: float = 20.0
