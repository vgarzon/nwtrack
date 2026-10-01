"""
Write a default config.toml to the explicit override path if one is set, else to
the standard per-OS config location.

Prompts before overwriting a file already at the target, and separately prompts
before writing a new file at the standard location if a higher-priority
config.toml is currently in effect (the new file would be ignored).
"""

import logging
from pathlib import Path

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import InitConfigPresenter
from nwtrack.infra.config.paths import (
    default_config_dir,
    default_db_file_path,
    default_log_file_path,
    get_config_file_override,
    resolve_config_file,
)

logger = logging.getLogger(__name__)

_CONFIG_FILE_NAME = "config.toml"

_TEMPLATE = """\
[database]
# db_file_path is optional. Left unset (or ""), it defaults to:
# {db_file_path}
# db_file_path = ""

[logging]
# log_file is optional. Left unset (or ""), it defaults to:
# {log_file}
# log_file = ""
log_file_level = "INFO"
log_rotation_mb = 10
log_backup_count = 7

[balances]
# Percent change (in either direction) from an account's prior balance that
# triggers a confirmation prompt before saving a balance update. Set to 0 to
# disable the check.
change_warning_threshold_pct = 20.0
"""


class InitConfig:
    """Write a default config.toml, prompting before overwriting an existing file."""

    def __init__(self, presenter: InitConfigPresenter) -> None:
        self._presenter = presenter

    def run(self) -> OperationResult[Path]:
        logger.info("Starting InitConfig use case")
        override = get_config_file_override()
        target_path = (
            override.path
            if override is not None
            else default_config_dir() / _CONFIG_FILE_NAME
        )
        self._presenter.show_target_path(target_path)

        if target_path.exists():
            if not self._presenter.confirm_overwrite(target_path):
                self._presenter.show_cancelled()
                logger.info("InitConfig cancelled: user declined overwrite")
                return OperationResult(success=False)
        elif override is None:
            active_path = resolve_config_file()
            if active_path is not None and active_path != target_path:
                if not self._presenter.confirm_shadow(target_path, active_path):
                    self._presenter.show_cancelled()
                    logger.info(
                        "InitConfig cancelled: user declined to shadow %s",
                        active_path,
                    )
                    return OperationResult(success=False)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            _TEMPLATE.format(
                db_file_path=default_db_file_path(),
                log_file=default_log_file_path(),
            ),
            encoding="utf-8",
        )

        self._presenter.show_success(target_path)
        logger.info("Finished InitConfig: wrote %s", target_path)
        return OperationResult(success=True, data=target_path)


def main() -> int:
    from rich.console import Console

    from nwtrack.bootstrap.container import Container, Lifetime
    from nwtrack.entrypoints.cli.adapters.config_presenters import (
        RichInitConfigPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    container = Container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        RichInitConfigPresenter,
        lambda c: RichInitConfigPresenter(console=c.resolve(Console)),
    ).register(
        InitConfig,
        lambda c: InitConfig(presenter=c.resolve(RichInitConfigPresenter)),
    )

    op: OperationResult[Path] = container.resolve(InitConfig).run()
    return 0 if op.success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
