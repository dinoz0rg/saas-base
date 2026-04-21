from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_admin
from app.database import get_db
from app.models.issue import Issue, IssueStatus
from app.models.user import User

router = APIRouter(prefix="/dashboard/board", tags=["board"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def board(
    request: Request,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    board_data = {}
    for status in IssueStatus:
        result = await db.execute(
            select(Issue)
            .where(Issue.status == status)
            .order_by(Issue.sort_order, Issue.created_at.desc())
        )
        board_data[status.value] = result.scalars().all()

    counts = {}
    for status in IssueStatus:
        counts[status.value] = len(board_data[status.value])

    return templates.TemplateResponse("board.html", {
        "request": request,
        "user": user,
        "active_page": "board",
        "board": board_data,
        "counts": counts,
    })
