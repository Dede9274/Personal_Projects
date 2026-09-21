from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    Index,
    Integer,
    JSON,
    String,
    Text,
    false,
    func,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class MonitorDB(Base):
    __tablename__ = "monitors"

    __table_args__ = (
        CheckConstraint(
            "interval_seconds > 0",
            name="ck_monitors_interval_positive",
        ),
        CheckConstraint(
            "timeout_seconds > 0",
            name="ck_monitors_timeout_positive",
        ),
        CheckConstraint(
            "expected_status_code BETWEEN 100 AND 599",
            name="ck_monitors_expected_status_valid",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("''"),
    )
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    timeout_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    expected_status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=true(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    check_results: Mapped[list["CheckResultDB"]] = relationship(
        back_populates="monitor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    incidents: Mapped[list["IncidentDB"]] = relationship(
        back_populates="monitor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CheckResultDB(Base):
    __tablename__ = "check_results"

    __table_args__ = (
        CheckConstraint(
            "latency_ms >= 0",
            name="ck_check_results_latency_nonnegative",
        ),
        Index(
            "ix_check_results_monitor_checked_at",
            "monitor_id",
            "checked_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )
    monitor_id: Mapped[int] = mapped_column(
        ForeignKey("monitors.id", ondelete="CASCADE"),
        nullable=False,
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    security_rejected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=false(),
    )

    monitor: Mapped["MonitorDB"] = relationship(
        back_populates="check_results",
    )


class IncidentDB(Base):
    __tablename__ = "incidents"

    __table_args__ = (
        CheckConstraint(
            "failure_count >= 1",
            name="ck_incidents_failure_count_positive",
        ),

        CheckConstraint(
            "resolved_at IS NULL OR resolved_at >= started_at",
            name="ck_incidents_resolved_after_started",
        ),
        CheckConstraint(
            "last_failure_at >= started_at",
            name="ck_incidents_last_failure_after_started",
        ),

        CheckConstraint(
            """
            (
                status IN ('OPEN', 'INVESTIGATING')
                AND resolved_at IS NULL
            )
            OR
            (status = 'RESOLVED' AND resolved_at IS NOT NULL)
            """,
            name="ck_incidents_status_resolution",
        ),

        Index(
            "ix_incidents_monitor_started_at",
            "monitor_id",
            "started_at",
        ),

        Index(
            "uq_incidents_one_active_per_monitor",
            "monitor_id",
            unique=True,
            postgresql_where=text(
                "status IN ('OPEN', 'INVESTIGATING')"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(),
        primary_key=True,
    )

    monitor_id: Mapped[int] = mapped_column(
        ForeignKey("monitors.id", ondelete="CASCADE"),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_failure_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'OPEN'"),
    )
    failure_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    monitor: Mapped["MonitorDB"] = relationship(
        back_populates="incidents",
    )


class NotificationSettingsDB(Base):
    __tablename__ = "notification_settings"

    __table_args__ = (
        CheckConstraint(
            "id = 1",
            name="ck_notification_settings_singleton",
        ),
        CheckConstraint(
            "email_timeout_seconds > 0 "
            "AND email_timeout_seconds <= 120",
            name="ck_notification_settings_email_timeout",
        ),
        CheckConstraint(
            "webhook_timeout_seconds > 0 "
            "AND webhook_timeout_seconds <= 120",
            name="ck_notification_settings_webhook_timeout",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=False,
    )
    email_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=false(),
    )
    email_recipients: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        server_default=text("'[]'"),
    )
    email_timeout_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        server_default=text("10"),
    )
    webhook_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=false(),
    )
    webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    webhook_timeout_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        server_default=text("10"),
    )
    notify_incident_opened: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=true(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
