import json

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_user
from app.config import settings
from app.database import get_db
from app.models.chat import ChatSession
from app.models.issue import Issue, IssueStatus, IssuePriority
from app.models.user import User

router = APIRouter(prefix="/api", tags=["api"])


# ── Issues (Board) ──────────────────────────────────────────────────


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
    user: User = Depends(require_user),
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
    user: User = Depends(require_user),
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
    user: User = Depends(require_user),
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
    user: User = Depends(require_user),
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
    user: User = Depends(require_user),
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
    title = data.title or await _generate_title(data.messages)
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


async def _generate_title(messages: list[dict]) -> str:
    """ChatGPT-style short title (≤5 words) from the first exchange.

    Falls back to truncated first user message on any failure or when the
    OpenAI key is not configured.
    """
    fallback = _derive_title(messages)
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        return fallback

    convo = [
        {"role": m.get("role", "user"), "content": str(m.get("content", ""))}
        for m in messages
        if m.get("content") and m.get("role") in ("user", "assistant")
    ][:6]
    if not any(m["role"] == "user" for m in convo):
        return fallback

    prompt = (
        "Summarize the following conversation in a short, descriptive title "
        "of at most 5 words. Use Title Case. No quotes, no trailing period, "
        "no emoji.\n\n"
        + "\n".join(f"{m['role']}: {m['content']}" for m in convo)
    )
    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "You generate concise chat titles."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 20,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if resp.status_code >= 400:
            return fallback
        body = resp.json()
        title = body["choices"][0]["message"]["content"].strip()
        title = title.strip('"\'').rstrip(".").strip()
        if not title:
            return fallback
        return title[:60]
    except (httpx.HTTPError, KeyError, ValueError):
        return fallback


# ── AI Assistant ─────────────────────────────────────────────────────


class AskPayload(BaseModel):
    messages: list[dict]


SYSTEM_PROMPT = (
    "You are Ask Navigator, a concise AI assistant embedded in a SaaS dashboard. "
    "Help the user understand their account, navigate the app, and answer "
    "questions clearly. Use short paragraphs and Markdown when helpful."
)


@router.post("/ai/ask")
async def ai_ask(
    data: AskPayload,
    user: User = Depends(require_user),
):
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured")

    # Sanitize incoming messages: keep only role + content, drop client-side fields.
    history = [
        {"role": m.get("role", "user"), "content": str(m.get("content", ""))}
        for m in data.messages
        if m.get("content")
    ]
    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *history],
        "temperature": 0.5,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI request failed: {exc}")

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    body = resp.json()
    content = body["choices"][0]["message"]["content"]
    return {"content": content, "model": body.get("model", settings.OPENAI_MODEL)}
