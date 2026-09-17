"""add monitor purpose

Revision ID: c91e7a6b2d4f
Revises: a7c9d2e4f681
Create Date: 2026-09-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c91e7a6b2d4f"
down_revision: Union[str, Sequence[str], None] = "a7c9d2e4f681"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add a description of what each monitored API is used for."""
    op.add_column(
        "monitors",
        sa.Column(
            "purpose",
            sa.Text(),
            server_default=sa.text("''"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove the monitor purpose."""
    op.drop_column("monitors", "purpose")
