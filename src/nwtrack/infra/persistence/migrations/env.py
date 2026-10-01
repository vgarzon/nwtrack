"""Alembic runtime environment.

Unlike a typical Alembic project, this environment is never driven by a
filesystem-discovered ``alembic.ini`` or by the ``alembic`` CLI pointed at a
URL. ``nwtrack`` resolves its database location through ``Settings`` at
runtime, so the only supported entry point is ``SchemaManager`` passing an
already-open SQLAlchemy connection via ``config.attributes["connection"]``
(see ``nwtrack.infra.persistence.alembic_runtime``).
"""

from __future__ import annotations

from alembic import context

from nwtrack.infra.persistence.orm import models  # noqa: F401  register tables on Base
from nwtrack.infra.persistence.orm.base import Base

target_metadata = Base.metadata


def run_migrations_online() -> None:
    connection = context.config.attributes.get("connection")
    if connection is None:
        raise RuntimeError(
            "nwtrack's Alembic environment requires an existing SQLAlchemy "
            "connection passed via config.attributes['connection']; it does "
            "not support ini-file or bare-URL invocation."
        )
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


run_migrations_online()
