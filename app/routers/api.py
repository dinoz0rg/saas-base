from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.issue import Issue, IssueStatus, Label
from app.schemas.issue import IssueCreate, IssueUpdate
from app.services.issue import create_issue, update_issue

router = APIRouter(prefix="/api")


@router.get("/projects/{project_id}/issues")
async def api_list_issues(
    project_id: str,
    status: IssueStatus | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Issue)
        .where(Issue.project_id == project_id)
        .options(selectinload(Issue.labels), selectinload(Issue.project))
        .order_by(Issue.created_at.desc())
    )
    if status:
        query = query.where(Issue.status == status)
    result = await db.execute(query)
    issues = result.scalars().all()
    return [
        {
            "id": i.id,
            "number": i.number,
            "title": i.title,
            "description": i.description,
            "status": i.status.value,
            "priority": i.priority.value,
            "assignee_name": i.assignee_name,
            "project_prefix": i.project.prefix,
            "labels": [{"id": l.id, "name": l.name, "color": l.color} for l in i.labels],
            "created_at": i.created_at.isoformat(),
            "updated_at": i.updated_at.isoformat(),
        }
        for i in issues
    ]


@router.get("/issues/{issue_id}")
async def api_get_issue(
    issue_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Issue)
        .where(Issue.id == issue_id)
        .options(selectinload(Issue.labels), selectinload(Issue.project))
    )
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return {
        "id": issue.id,
        "number": issue.number,
        "title": issue.title,
        "description": issue.description,
        "status": issue.status.value,
        "priority": issue.priority.value,
        "assignee_name": issue.assignee_name,
        "project_prefix": issue.project.prefix,
        "labels": [{"id": l.id, "name": l.name, "color": l.color} for l in issue.labels],
        "created_at": issue.created_at.isoformat(),
        "updated_at": issue.updated_at.isoformat(),
    }


@router.post("/projects/{project_id}/issues")
async def api_create_issue(
    project_id: str,
    data: IssueCreate,
    db: AsyncSession = Depends(get_db),
):
    issue = await create_issue(db, project_id, data)
    await db.flush()
    # reload with relationships
    result = await db.execute(
        select(Issue)
        .where(Issue.id == issue.id)
        .options(selectinload(Issue.labels), selectinload(Issue.project))
    )
    issue = result.scalar_one()
    return {
        "id": issue.id,
        "number": issue.number,
        "title": issue.title,
        "description": issue.description,
        "status": issue.status.value,
        "priority": issue.priority.value,
        "assignee_name": issue.assignee_name,
        "project_prefix": issue.project.prefix,
        "labels": [{"id": l.id, "name": l.name, "color": l.color} for l in issue.labels],
    }


@router.patch("/issues/{issue_id}")
async def api_update_issue(
    issue_id: str,
    data: IssueUpdate,
    db: AsyncSession = Depends(get_db),
):
    issue = await update_issue(db, issue_id, data)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    await db.flush()
    result = await db.execute(
        select(Issue)
        .where(Issue.id == issue.id)
        .options(selectinload(Issue.labels), selectinload(Issue.project))
    )
    issue = result.scalar_one()
    return {
        "id": issue.id,
        "number": issue.number,
        "title": issue.title,
        "description": issue.description,
        "status": issue.status.value,
        "priority": issue.priority.value,
        "assignee_name": issue.assignee_name,
        "project_prefix": issue.project.prefix,
        "labels": [{"id": l.id, "name": l.name, "color": l.color} for l in issue.labels],
    }


@router.delete("/issues/{issue_id}")
async def api_delete_issue(
    issue_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    await db.delete(issue)
    return {"ok": True}


@router.get("/projects/{project_id}/labels")
async def api_list_labels(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Label).where(Label.project_id == project_id).order_by(Label.name)
    )
    labels = result.scalars().all()
    return [{"id": l.id, "name": l.name, "color": l.color} for l in labels]
