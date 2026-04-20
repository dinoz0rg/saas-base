from pydantic import BaseModel

from app.models.issue import IssuePriority, IssueStatus


class IssueCreate(BaseModel):
    title: str
    description: str | None = None
    status: IssueStatus = IssueStatus.BACKLOG
    priority: IssuePriority = IssuePriority.NONE
    assignee_name: str | None = None
    label_ids: list[str] = []


class IssueUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: IssueStatus | None = None
    priority: IssuePriority | None = None
    assignee_name: str | None = None
    label_ids: list[str] | None = None


class ProjectCreate(BaseModel):
    name: str
    prefix: str


class LabelCreate(BaseModel):
    name: str
    color: str = "gray"
