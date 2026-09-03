"""add incident last failure timestamp

Revision ID: a7c9d2e4f681
Revises: fb04f4b3b9b6
Create Date: 2026-08-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a7c9d2e4f681"
down_revision: Union[str, Sequence[str], None] = "fb04f4b3b9b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add and backfill the timestamp of the most recent failure."""
    op.add_column(
        "incidents",
        sa.Column(
            "last_failure_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE incidents "
            "SET last_failure_at = started_at"
        )
    )
    op.alter_column(
        "incidents",
        "last_failure_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.create_check_constraint(
        "ck_incidents_last_failure_after_started",
        "incidents",
        "last_failure_at >= started_at",
    )


def downgrade() -> None:
    """Remove the timestamp of the most recent failure."""
    op.drop_constraint(
        "ck_incidents_last_failure_after_started",
        "incidents",
        type_="check",
    )
    op.drop_column("incidents", "last_failure_at")
