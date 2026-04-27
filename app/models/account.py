import enum
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text, Enum, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.database import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid7())


class ActivityType(str, enum.Enum):
    LOGIN = "login"
    SIGNUP = "signup"
    SETTINGS_CHANGE = "settings_change"
    API_CALL = "api_call"


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


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    prefix: Mapped[str] = mapped_column(String(12))            # short displayable prefix e.g. "sk_live_a1b2"
    hashed_key: Mapped[str] = mapped_column(String(255))       # bcrypt hash of full key
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)

    owner: Mapped["app.models.user.User"] = relationship(back_populates="api_keys")


class Subscription(Base):
    """A user's active billing subscription.

    One row per user, upserted on plan changes. Free plans are recorded too,
    so the dashboard can always show a "current plan" without nullable joins.
    """
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    plan: Mapped[str] = mapped_column(String(32), default="free")            # plan slug
    interval: Mapped[str] = mapped_column(String(16), default="monthly")     # 'monthly' | 'yearly'
    status: Mapped[str] = mapped_column(String(20), default="active")        # 'active' | 'cancelled'
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc, onupdate=_now_utc)


class Invoice(Base):
    """A billing invoice (mock — no real payment processor wired up)."""
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[str] = mapped_column(String(32), unique=True)             # e.g. "INV-2024-0001"
    plan: Mapped[str] = mapped_column(String(32))
    interval: Mapped[str] = mapped_column(String(16))
    amount_cents: Mapped[int] = mapped_column(default=0)
    currency: Mapped[str] = mapped_column(String(8), default="usd")
    status: Mapped[str] = mapped_column(String(16), default="paid")          # 'paid' | 'open' | 'void'
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)
