"""add investigating incident status

Revision ID: d4e8f1a2b6c9
Revises: c91e7a6b2d4f
Create Date: 2026-09-17

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e8f1a2b6c9"
down_revision: Union[str, Sequence[str], None] = "c91e7a6b2d4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ACTIVE_STATUS_PREDICATE = "status IN ('OPEN', 'INVESTIGATING')"


def upgrade() -> None:
    """Allow one OPEN or INVESTIGATING incident per monitor."""
    op.drop_index(
        "uq_incidents_one_open_per_monitor",
        table_name="incidents",
        postgresql_where=sa.text("status = 'OPEN'"),
    )
    op.drop_constraint(
        "ck_incidents_status_resolution",
        "incidents",
        type_="check",
    )
    op.create_check_constraint(
        "ck_incidents_status_resolution",
        "incidents",
        """
        (
            status IN ('OPEN', 'INVESTIGATING')
            AND resolved_at IS NULL
        )
        OR
        (status = 'RESOLVED' AND resolved_at IS NOT NULL)
        """,
    )
    op.create_index(
        "uq_incidents_one_active_per_monitor",
        "incidents",
        ["monitor_id"],
        unique=True,
        postgresql_where=sa.text(ACTIVE_STATUS_PREDICATE),
    )


def downgrade() -> None:
    """Return investigations to OPEN before restoring the old rules."""
    op.execute(
        sa.text(
            "UPDATE incidents "
            "SET status = 'OPEN' "
            "WHERE status = 'INVESTIGATING'"
        )
    )
    op.drop_index(
        "uq_incidents_one_active_per_monitor",
        table_name="incidents",
        postgresql_where=sa.text(ACTIVE_STATUS_PREDICATE),
    )
    op.drop_constraint(
        "ck_incidents_status_resolution",
        "incidents",
        type_="check",
    )
    op.create_check_constraint(
        "ck_incidents_status_resolution",
        "incidents",
        """
        (status = 'OPEN' AND resolved_at IS NULL)
        OR
        (status = 'RESOLVED' AND resolved_at IS NOT NULL)
        """,
    )
    op.create_index(
        "uq_incidents_one_open_per_monitor",
        "incidents",
        ["monitor_id"],
        unique=True,
        postgresql_where=sa.text("status = 'OPEN'"),
    )
