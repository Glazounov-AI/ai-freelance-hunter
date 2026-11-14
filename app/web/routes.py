"""Operator-only dashboard routes; reuse existing application business rules."""
import json
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.applications import (
    CreateApplication,
    Decision,
    EditDraft,
    approve,
    create_application,
    edit_draft,
    get_history,
    reject,
)
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.analysis import OpportunityAnalysis
from app.models.application import Application
from app.models.opportunity import Opportunity, Source
from app.web.auth import COOKIE_NAME, csrf_for, issue_session, require_csrf, require_session

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
STATIC = Path(__file__).resolve().parent / "static"


@router.get("/login", response_class=HTMLResponse)
async def login_page() -> HTMLResponse:
    return HTMLResponse((STATIC / "login.html").read_text(encoding="utf-8"), headers={"Cache-Control": "no-store"})


@router.post("/login")
async def login(request: Request, token: str = Form(...), settings: Settings = Depends(get_settings)):
    if not secrets.compare_digest(token, settings.admin_api_token.get_secret_value()):
        raise HTTPException(401, "Invalid credentials")
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(COOKIE_NAME, issue_session(settings), httponly=True,
                        secure=request.url.scheme == "https", samesite="strict",
                        max_age=8 * 3600, path="/dashboard")
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request, session: str = Depends(require_session),
                    settings: Settings = Depends(get_settings)):
    template = (STATIC / "index.html").read_text(encoding="utf-8")
    # Only a derived anti-CSRF token is embedded, never ADMIN_API_TOKEN.
    template = template.replace("__CSRF_TOKEN__", csrf_for(session, settings))
    return HTMLResponse(template, headers={"Cache-Control": "no-store", "X-Frame-Options": "DENY"})


@router.get("/style.css")
async def style():
    return FileResponse(STATIC / "style.css", media_type="text/css", headers={"Cache-Control": "no-store"})


@router.get("/app.js")
async def script():
    return FileResponse(STATIC / "app.js", media_type="text/javascript", headers={"Cache-Control": "no-store"})


@router.post("/logout", dependencies=[Depends(require_csrf)])
async def logout():
    response = RedirectResponse("/dashboard/login", status_code=303)
    response.delete_cookie(COOKIE_NAME, path="/dashboard")
    return response


@router.get("/data", dependencies=[Depends(require_session)])
async def dashboard_data(db: AsyncSession = Depends(get_db),
                         limit: int = Query(default=100, ge=1, le=100)):
    opportunities = (await db.scalars(select(Opportunity).order_by(Opportunity.id.desc()).limit(limit))).all()
    ids = [o.id for o in opportunities]
    if not ids:
        return []
    analyses = (await db.scalars(select(OpportunityAnalysis)
                .where(OpportunityAnalysis.opportunity_id.in_(ids))
                .order_by(OpportunityAnalysis.id.desc()))).all()
    apps = (await db.scalars(select(Application).where(Application.opportunity_id.in_(ids)))).all()
    sources = {s.id: s.name for s in (await db.scalars(select(Source))).all()}
    latest = {}
    for analysis in analyses:
        latest.setdefault(analysis.opportunity_id, analysis)
    app_by_opportunity = {a.opportunity_id: a for a in apps}
    result = []
    for o in opportunities:
        a = latest.get(o.id)
        application = app_by_opportunity.get(o.id)
        result.append({
            "id": o.id, "title": o.title, "description": o.description,
            "url": o.url, "source": sources.get(o.source_id, "Неизвестно"),
            "status": o.status.value, "created_at": o.created_at.isoformat(),
            "analysis": None if a is None else {
                "id": a.id, "score": a.score, "mode": a.mode,
                "explanation": a.explanation, "warnings": json.loads(a.warnings_json),
                "skills": json.loads(a.matched_skills_json), "draft": a.draft,
            },
            "application": None if application is None else {
                "id": application.id, "status": application.status.value,
                "draft": application.draft,
            },
        })
    return result


class DraftInput(BaseModel):
    draft: str = Field(min_length=10, max_length=10000)


class ReviewInput(BaseModel):
    note: str | None = Field(default=None, max_length=500)


@router.post("/applications", dependencies=[Depends(require_csrf)])
async def create(payload: CreateApplication, db: AsyncSession = Depends(get_db)):
    return await create_application(payload, db)


@router.patch("/applications/{application_id}/draft", dependencies=[Depends(require_csrf)])
async def update_draft(application_id: int, payload: DraftInput,
                       db: AsyncSession = Depends(get_db)):
    return await edit_draft(application_id, EditDraft(draft=payload.draft), db)


@router.post("/applications/{application_id}/approve", dependencies=[Depends(require_csrf)])
async def approve_draft(application_id: int, payload: ReviewInput,
                        db: AsyncSession = Depends(get_db)):
    return await approve(application_id, Decision(note=payload.note), db)


@router.post("/applications/{application_id}/reject", dependencies=[Depends(require_csrf)])
async def reject_draft(application_id: int, payload: ReviewInput,
                       db: AsyncSession = Depends(get_db)):
    return await reject(application_id, Decision(note=payload.note), db)


@router.get("/applications/{application_id}/history", dependencies=[Depends(require_session)])
async def history(application_id: int, db: AsyncSession = Depends(get_db)):
    return await get_history(application_id, db)
