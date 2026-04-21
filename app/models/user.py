from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.database import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid7())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    hashed_password: Mapped[str] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc, onupdate=_now_utc)
    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=_now_utc)

    # 2FA fields
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    activities: Mapped[list["app.models.workspace.Activity"]] = relationship(back_populates="owner")
    metrics: Mapped[list["app.models.workspace.Metric"]] = relationship(back_populates="owner")
    pages: Mapped[list["app.models.workspace.Page"]] = relationship(back_populates="owner")
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    browser: Mapped[str | None] = mapped_column(String(100), nullable=True)
    os: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_active: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)

    owner: Mapped["User"] = relationship(back_populates="sessions")
