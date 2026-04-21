import enum
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text, Integer, Float, Enum, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.database import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid7())


class ActivityType(str, enum.Enum):
    PAGE_VIEW = "page_view"
    LOGIN = "login"
    SIGNUP = "signup"
    EXPORT = "export"
    SETTINGS_CHANGE = "settings_change"
    API_CALL = "api_call"
    UPLOAD = "upload"
    INVITE_SENT = "invite_sent"


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    user_name: Mapped[str] = mapped_column(String(100))
    action: Mapped[ActivityType] = mapped_column(Enum(ActivityType))
    description: Mapped[str] = mapped_column(String(500))
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)

    owner: Mapped["app.models.user.User"] = relationship(back_populates="activities")


class MetricPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))
    value: Mapped[float] = mapped_column(Float)
    period: Mapped[MetricPeriod] = mapped_column(Enum(MetricPeriod), default=MetricPeriod.DAILY)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)

    owner: Mapped["app.models.user.User"] = relationship(back_populates="metrics")


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc, onupdate=_now_utc)

    owner: Mapped["app.models.user.User"] = relationship(back_populates="pages")
