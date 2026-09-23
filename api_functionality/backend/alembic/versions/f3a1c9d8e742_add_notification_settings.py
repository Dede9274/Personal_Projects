"""add persisted notification settings

Revision ID: f3a1c9d8e742
Revises: d4e8f1a2b6c9
Create Date: 2026-09-21

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a1c9d8e742"
down_revision: Union[str, Sequence[str], None] = "d4e8f1a2b6c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notification_settings",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "email_enabled",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column(
            "email_recipients",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column(
            "email_timeout_seconds",
            sa.Float(),
            server_default=sa.text("10"),
            nullable=False,
        ),
        sa.Column(
            "webhook_enabled",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("webhook_url", sa.Text(), nullable=True),
        sa.Column(
            "webhook_timeout_seconds",
            sa.Float(),
            server_default=sa.text("10"),
            nullable=False,
        ),
        sa.Column(
            "notify_incident_opened",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "id = 1",
            name="ck_notification_settings_singleton",
        ),
        sa.CheckConstraint(
            "email_timeout_seconds > 0 "
            "AND email_timeout_seconds <= 120",
            name="ck_notification_settings_email_timeout",
        ),
        sa.CheckConstraint(
            "webhook_timeout_seconds > 0 "
            "AND webhook_timeout_seconds <= 120",
            name="ck_notification_settings_webhook_timeout",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        sa.text(
            "INSERT INTO notification_settings (id) VALUES (1)"
        )
    )


def downgrade() -> None:
    op.drop_table("notification_settings")
