from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.issue import Issue, Project, Workspace
from app.services.issue import get_board_issues, get_status_counts

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def _get_workspace_context(db: AsyncSession, workspace_slug: str, project_prefix: str):
    """Shared helper to load workspace, project, and all projects for sidebar."""
    ws_result = await db.execute(
        select(Workspace)
        .where(Workspace.slug == workspace_slug)
        .options(selectinload(Workspace.projects))
    )
    workspace = ws_result.scalar_one_or_none()
    if not workspace:
        return None, None, []

    project = next((p for p in workspace.projects if p.prefix == project_prefix), None)

    all_projects_result = await db.execute(
        select(Project)
        .where(Project.workspace_id == workspace.id)
        .options(selectinload(Project.workspace))
    )
    all_projects = all_projects_result.scalars().all()

    return workspace, project, all_projects


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Workspace).options(selectinload(Workspace.projects)).limit(1)
    )
    workspace = result.scalar_one_or_none()

    if not workspace or not workspace.projects:
        return templates.TemplateResponse("empty.html", {
            "request": request,
            "workspace": workspace,
        })

    project = workspace.projects[0]
    return templates.TemplateResponse("redirect.html", {
        "request": request,
        "url": f"/{workspace.slug}/{project.prefix}/board",
    })


@router.get("/{workspace_slug}/{project_prefix}/board", response_class=HTMLResponse)
async def board(
    request: Request,
    workspace_slug: str,
    project_prefix: str,
    db: AsyncSession = Depends(get_db),
):
    workspace, project, all_projects = await _get_workspace_context(db, workspace_slug, project_prefix)
    if not workspace:
        return HTMLResponse("Workspace not found", status_code=404)
    if not project:
        return HTMLResponse("Project not found", status_code=404)

    board_data = await get_board_issues(db, project.id)
    counts = await get_status_counts(db, project.id)

    return templates.TemplateResponse("board.html", {
        "request": request,
        "workspace": workspace,
        "project": project,
        "projects": all_projects,
        "board": board_data,
        "counts": counts,
    })


@router.get("/{workspace_slug}/{project_prefix}/inbox", response_class=HTMLResponse)
async def inbox(
    request: Request,
    workspace_slug: str,
    project_prefix: str,
    db: AsyncSession = Depends(get_db),
):
    workspace, project, all_projects = await _get_workspace_context(db, workspace_slug, project_prefix)
    if not workspace:
        return HTMLResponse("Workspace not found", status_code=404)

    # Show recently created issues as "inbox" items
    result = await db.execute(
        select(Issue)
        .where(Issue.project_id == project.id)
        .options(selectinload(Issue.labels), selectinload(Issue.project))
        .order_by(Issue.created_at.desc())
        .limit(30)
    )
    issues = result.scalars().all()

    return templates.TemplateResponse("page.html", {
        "request": request,
        "workspace": workspace,
        "project": project,
        "projects": all_projects,
        "active_page": "inbox",
        "page_title": "Inbox",
        "page_description": "Recent issues and updates across your projects.",
        "issues": issues,
        "board_url": f"/{workspace_slug}/{project_prefix}/board",
    })


@router.get("/{workspace_slug}/{project_prefix}/my-issues", response_class=HTMLResponse)
async def my_issues(
    request: Request,
    workspace_slug: str,
    project_prefix: str,
    db: AsyncSession = Depends(get_db),
):
    workspace, project, all_projects = await _get_workspace_context(db, workspace_slug, project_prefix)
    if not workspace:
        return HTMLResponse("Workspace not found", status_code=404)

    # Show issues that have an assignee (simulating "my" issues)
    result = await db.execute(
        select(Issue)
        .where(Issue.project_id == project.id, Issue.assignee_name.isnot(None))
        .options(selectinload(Issue.labels), selectinload(Issue.project))
        .order_by(Issue.updated_at.desc())
        .limit(50)
    )
    issues = result.scalars().all()

    return templates.TemplateResponse("page.html", {
        "request": request,
        "workspace": workspace,
        "project": project,
        "projects": all_projects,
        "active_page": "my_issues",
        "page_title": "My issues",
        "page_description": "Issues assigned to you.",
        "issues": issues,
        "board_url": f"/{workspace_slug}/{project_prefix}/board",
    })


@router.get("/{workspace_slug}/{project_prefix}/projects", response_class=HTMLResponse)
async def projects_list(
    request: Request,
    workspace_slug: str,
    project_prefix: str,
    db: AsyncSession = Depends(get_db),
):
    workspace, project, all_projects = await _get_workspace_context(db, workspace_slug, project_prefix)
    if not workspace:
        return HTMLResponse("Workspace not found", status_code=404)

    # Build project items with issue counts
    items = []
    for p in all_projects:
        count_result = await db.execute(
            select(func.count(Issue.id)).where(Issue.project_id == p.id)
        )
        count = count_result.scalar()
        items.append({
            "url": f"/{workspace_slug}/{p.prefix}/board",
            "title": p.name,
            "subtitle": f"Prefix: {p.prefix}",
            "icon": p.prefix[0],
            "icon_bg": "from-emerald-400 to-teal-500",
            "badge": f"{count} issues",
        })

    return templates.TemplateResponse("page.html", {
        "request": request,
        "workspace": workspace,
        "project": project,
        "projects": all_projects,
        "active_page": "projects",
        "page_title": "Projects",
        "page_description": "All projects in your workspace.",
        "items": items,
    })


@router.get("/{workspace_slug}/{project_prefix}/views", response_class=HTMLResponse)
async def views(
    request: Request,
    workspace_slug: str,
    project_prefix: str,
    db: AsyncSession = Depends(get_db),
):
    workspace, project, all_projects = await _get_workspace_context(db, workspace_slug, project_prefix)
    if not workspace:
        return HTMLResponse("Workspace not found", status_code=404)

    return templates.TemplateResponse("page.html", {
        "request": request,
        "workspace": workspace,
        "project": project,
        "projects": all_projects,
        "active_page": "views",
        "page_title": "Views",
        "page_description": "Custom filtered views of your issues.",
        "empty_message": "Create custom views to filter and organize issues.",
    })


@router.get("/{workspace_slug}/{project_prefix}/initiatives", response_class=HTMLResponse)
async def initiatives(
    request: Request,
    workspace_slug: str,
    project_prefix: str,
    db: AsyncSession = Depends(get_db),
):
    workspace, project, all_projects = await _get_workspace_context(db, workspace_slug, project_prefix)
    if not workspace:
        return HTMLResponse("Workspace not found", status_code=404)

    return templates.TemplateResponse("page.html", {
        "request": request,
        "workspace": workspace,
        "project": project,
        "projects": all_projects,
        "active_page": "initiatives",
        "page_title": "Initiatives",
        "page_description": "Track high-level goals and group related projects.",
        "empty_message": "Create initiatives to track larger goals across projects.",
    })


@router.get("/{workspace_slug}/{project_prefix}/cycles", response_class=HTMLResponse)
async def cycles(
    request: Request,
    workspace_slug: str,
    project_prefix: str,
    db: AsyncSession = Depends(get_db),
):
    workspace, project, all_projects = await _get_workspace_context(db, workspace_slug, project_prefix)
    if not workspace:
        return HTMLResponse("Workspace not found", status_code=404)

    return templates.TemplateResponse("page.html", {
        "request": request,
        "workspace": workspace,
        "project": project,
        "projects": all_projects,
        "active_page": "cycles",
        "page_title": "Cycles",
        "page_description": "Plan work in time-boxed cycles.",
        "empty_message": "Create cycles to organize work into sprints.",
    })


@router.get("/{workspace_slug}/{project_prefix}/settings", response_class=HTMLResponse)
async def settings(
    request: Request,
    workspace_slug: str,
    project_prefix: str,
    db: AsyncSession = Depends(get_db),
):
    workspace, project, all_projects = await _get_workspace_context(db, workspace_slug, project_prefix)
    if not workspace:
        return HTMLResponse("Workspace not found", status_code=404)

    items = [
        {"url": "#", "title": "General", "subtitle": "Workspace name, URL, and icon", "icon": "⚙", "icon_bg": "from-neutral-400 to-neutral-500"},
        {"url": "#", "title": "Members", "subtitle": "Manage workspace members and roles", "icon": "👥", "icon_bg": "from-blue-400 to-blue-500"},
        {"url": "#", "title": "Labels", "subtitle": "Manage issue labels and colors", "icon": "🏷", "icon_bg": "from-purple-400 to-purple-500"},
        {"url": "#", "title": "Integrations", "subtitle": "Connect with other tools", "icon": "🔗", "icon_bg": "from-green-400 to-green-500"},
    ]

    return templates.TemplateResponse("page.html", {
        "request": request,
        "workspace": workspace,
        "project": project,
        "projects": all_projects,
        "active_page": "settings",
        "page_title": "Settings",
        "page_description": "Manage your workspace settings.",
        "items": items,
    })
