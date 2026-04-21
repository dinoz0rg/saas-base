import enum
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Enum, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from uuid_utils import uuid7

from app.database import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid7())


class IssueStatus(str, enum.Enum):
    backlog = "backlog"
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    cancelled = "cancelled"


class IssuePriority(str, enum.Enum):
    urgent = "urgent"
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    identifier: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[IssueStatus] = mapped_column(Enum(IssueStatus), default=IssueStatus.backlog)
    priority: Mapped[IssuePriority] = mapped_column(Enum(IssuePriority), default=IssuePriority.none)
    label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assignee: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc, onupdate=_now_utc)
