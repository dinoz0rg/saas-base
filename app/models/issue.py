import enum
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text, Integer, Enum, DateTime, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.database import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid7())


class IssueStatus(str, enum.Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"
    DUPLICATE = "duplicate"


class IssuePriority(str, enum.Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


issue_labels = Table(
    "issue_labels",
    Base.metadata,
    Column("issue_id", String(36), ForeignKey("issues.id"), primary_key=True),
    Column("label_id", String(36), ForeignKey("labels.id"), primary_key=True),
)


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)

    projects: Mapped[list["Project"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(100))
    prefix: Mapped[str] = mapped_column(String(10))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)

    workspace: Mapped["Workspace"] = relationship(back_populates="projects")
    issues: Mapped[list["Issue"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    labels: Mapped[list["Label"]] = relationship(back_populates="project", cascade="all, delete-orphan")

    @property
    def next_issue_number(self) -> int:
        if not self.issues:
            return 1
        return max(i.number for i in self.issues) + 1


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(50))
    color: Mapped[str] = mapped_column(String(20), default="gray")
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)

    project: Mapped["Project"] = relationship(back_populates="labels")
    issues: Mapped[list["Issue"]] = relationship(secondary=issue_labels, back_populates="labels")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[IssueStatus] = mapped_column(Enum(IssueStatus), default=IssueStatus.BACKLOG)
    priority: Mapped[IssuePriority] = mapped_column(Enum(IssuePriority), default=IssuePriority.NONE)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    assignee_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc, onupdate=_now_utc)

    project: Mapped["Project"] = relationship(back_populates="issues")
    labels: Mapped[list["Label"]] = relationship(secondary=issue_labels, back_populates="issues")

    @property
    def identifier(self) -> str:
        return f"{self.project.prefix}-{self.number}"
