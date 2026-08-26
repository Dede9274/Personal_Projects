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
    String,
    Text,
    func,
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

    monitor: Mapped["MonitorDB"] = relationship(
        back_populates="check_results",
    )
