from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.issue import Issue, IssueStatus, Label, Project
from app.schemas.issue import IssueCreate, IssueUpdate


async def get_board_issues(db: AsyncSession, project_id: str) -> dict[str, list[Issue]]:
    result = await db.execute(
        select(Issue)
        .where(Issue.project_id == project_id)
        .options(selectinload(Issue.labels), selectinload(Issue.project))
        .order_by(Issue.created_at.desc())
    )
    issues = result.scalars().all()

    board: dict[str, list[Issue]] = {}
    for status in IssueStatus:
        board[status.value] = []
    for issue in issues:
        board[issue.status.value].append(issue)
    return board


async def get_status_counts(db: AsyncSession, project_id: str) -> dict[str, int]:
    result = await db.execute(
        select(Issue.status, func.count(Issue.id))
        .where(Issue.project_id == project_id)
        .group_by(Issue.status)
    )
    counts = {status.value: 0 for status in IssueStatus}
    for status, count in result.all():
        counts[status.value] = count
    return counts


async def create_issue(db: AsyncSession, project_id: str, data: IssueCreate) -> Issue:
    max_num = await db.execute(
        select(func.coalesce(func.max(Issue.number), 0))
        .where(Issue.project_id == project_id)
    )
    next_number = max_num.scalar() + 1

    issue = Issue(
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        project_id=project_id,
        assignee_name=data.assignee_name,
        number=next_number,
    )

    if data.label_ids:
        labels_result = await db.execute(
            select(Label).where(Label.id.in_(data.label_ids))
        )
        issue.labels = list(labels_result.scalars().all())

    db.add(issue)
    await db.flush()
    return issue


async def update_issue(db: AsyncSession, issue_id: str, data: IssueUpdate) -> Issue | None:
    result = await db.execute(
        select(Issue).where(Issue.id == issue_id).options(selectinload(Issue.labels))
    )
    issue = result.scalar_one_or_none()
    if not issue:
        return None

    update_data = data.model_dump(exclude_unset=True)
    label_ids = update_data.pop("label_ids", None)

    for key, value in update_data.items():
        setattr(issue, key, value)

    if label_ids is not None:
        labels_result = await db.execute(
            select(Label).where(Label.id.in_(label_ids))
        )
        issue.labels = list(labels_result.scalars().all())

    await db.flush()
    return issue


async def get_project_with_details(db: AsyncSession, project_id: str) -> Project | None:
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.workspace), selectinload(Project.labels))
    )
    return result.scalar_one_or_none()
