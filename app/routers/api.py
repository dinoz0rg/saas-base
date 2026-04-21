import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_admin, require_user
from app.database import get_db
from app.models.issue import Issue, IssueStatus, IssuePriority
from app.models.chat import ChatSession
from app.models.user import User

router = APIRouter(prefix="/api", tags=["api"])


class IssueCreate(BaseModel):
    title: str
    description: str | None = None
    status: IssueStatus = IssueStatus.backlog
    priority: IssuePriority = IssuePriority.none
    label: str | None = None
    assignee: str | None = None


class IssueUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: IssueStatus | None = None
    priority: IssuePriority | None = None
    label: str | None = None
    assignee: str | None = None
    sort_order: int | None = None


def _issue_dict(issue: Issue) -> dict:
    return {
        "id": issue.id,
        "identifier": issue.identifier,
        "title": issue.title,
        "description": issue.description,
        "status": issue.status.value,
        "priority": issue.priority.value,
        "label": issue.label,
        "assignee": issue.assignee,
        "sort_order": issue.sort_order,
        "created_by": issue.created_by,
        "created_at": issue.created_at.isoformat(),
        "updated_at": issue.updated_at.isoformat(),
    }


@router.get("/issues")
async def list_issues(
    status: IssueStatus | None = None,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    q = select(Issue).order_by(Issue.sort_order, Issue.created_at.desc())
    if status:
        q = q.where(Issue.status == status)
    result = await db.execute(q)
    return [_issue_dict(i) for i in result.scalars().all()]


@router.get("/issues/{issue_id}")
async def get_issue(
    issue_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return _issue_dict(issue)


@router.post("/issues", status_code=201)
async def create_issue(
    data: IssueCreate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    count = await db.scalar(select(func.count()).select_from(Issue))
    identifier = f"ACE-{(count or 0) + 1}"
    issue = Issue(
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        label=data.label,
        assignee=data.assignee,
        identifier=identifier,
        created_by=user.id,
    )
    db.add(issue)
    await db.flush()
    await db.refresh(issue)
    return _issue_dict(issue)


@router.patch("/issues/{issue_id}")
async def update_issue(
    issue_id: str,
    data: IssueUpdate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(issue, field, value)
    db.add(issue)
    await db.flush()
    await db.refresh(issue)
    return _issue_dict(issue)


@router.delete("/issues/{issue_id}", status_code=204)
async def delete_issue(
    issue_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    await db.delete(issue)


# ── Chat Sessions ───────────────────────────────────────────────────


class ChatMessagePayload(BaseModel):
    messages: list[dict]
    title: str | None = None


def _chat_dict(session: ChatSession) -> dict:
    return {
        "id": session.id,
        "title": session.title,
        "messages": json.loads(session.messages),
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


@router.get("/chats")
async def list_chats(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    return [_chat_dict(c) for c in result.scalars().all()]


@router.post("/chats", status_code=201)
async def create_chat(
    data: ChatMessagePayload,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    title = data.title or _derive_title(data.messages)
    session = ChatSession(
        user_id=user.id,
        title=title,
        messages=json.dumps(data.messages),
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return _chat_dict(session)


@router.get("/chats/{chat_id}")
async def get_chat(
    chat_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == chat_id, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Chat not found")
    return _chat_dict(session)


@router.patch("/chats/{chat_id}")
async def update_chat(
    chat_id: str,
    data: ChatMessagePayload,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == chat_id, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Chat not found")
    session.messages = json.dumps(data.messages)
    if data.title:
        session.title = data.title
    else:
        session.title = _derive_title(data.messages)
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return _chat_dict(session)


@router.delete("/chats/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == chat_id, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Chat not found")
    await db.delete(session)


def _derive_title(messages: list[dict]) -> str:
    for msg in messages:
        if msg.get("role") == "user" and msg.get("content"):
            text = msg["content"].strip()
            return text[:50] + ("..." if len(text) > 50 else "")
    return "New Chat"
