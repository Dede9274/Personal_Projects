"""record monitor checks rejected by the outbound security policy

Revision ID: b6c4e8f2a913
Revises: f3a1c9d8e742
Create Date: 2026-09-21

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b6c4e8f2a913"
down_revision: Union[str, Sequence[str], None] = "f3a1c9d8e742"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "check_results",
        sa.Column(
            "security_rejected",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("check_results", "security_rejected")
