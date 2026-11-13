from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_admin
from app.db.session import get_db
from app.models.analysis import OpportunityAnalysis
from app.models.application import Application, ApplicationEvent, ApplicationStatus
from app.models.opportunity import Opportunity, OpportunityStatus
from app.review.rules import InvalidTransition, clean_draft, next_status

router = APIRouter(
    prefix="/api/v1/applications", tags=["applications"],
    dependencies=[Depends(require_admin)],
)


class CreateApplication(BaseModel):
    analysis_id: int = Field(ge=1)


class EditDraft(BaseModel):
    draft: str = Field(min_length=10, max_length=10000)


class Decision(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    opportunity_id: int
    analysis_id: int
    draft: str
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    sequence: int
    action: str
    note: str | None
    created_at: datetime


async def _locked_application(db: AsyncSession, application_id: int) -> Application:
    result = await db.scalar(
        select(Application).where(Application.id == application_id).with_for_update()
    )
    if result is None:
        raise HTTPException(404, "Application not found")
    return result


async def _append_event(
    db: AsyncSession, application_id: int, action: str, note: str | None, sequence: int
) -> None:
    db.add(ApplicationEvent(
        application_id=application_id, action=action, note=note, sequence=sequence
    ))


async def _next_sequence(db: AsyncSession, application_id: int) -> int:
    from sqlalchemy import func
    current = await db.scalar(
        select(func.max(ApplicationEvent.sequence)).where(
            ApplicationEvent.application_id == application_id
        )
    )
    return (current or 0) + 1


@router.post("", response_model=ApplicationRead, status_code=201)
async def create_application(
    payload: CreateApplication, db: AsyncSession = Depends(get_db)
) -> Application:
    analysis = await db.get(OpportunityAnalysis, payload.analysis_id)
    if analysis is None:
        raise HTTPException(404, "Analysis not found")
    opportunity = await db.scalar(
        select(Opportunity).where(Opportunity.id == analysis.opportunity_id).with_for_update()
    )
    if opportunity is None:
        raise HTTPException(404, "Opportunity not found")
    if opportunity.status != OpportunityStatus.ANALYZED:
        raise HTTPException(409, "Opportunity is not ready for drafting")
    if await db.scalar(select(Application.id).where(
        Application.opportunity_id == opportunity.id
    )) is not None:
        raise HTTPException(409, "Application already exists for this opportunity")
    try:
        draft = clean_draft(analysis.draft)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    application = Application(
        opportunity_id=opportunity.id, analysis_id=analysis.id, draft=draft,
        status=ApplicationStatus.DRAFT,
    )
    db.add(application)
    opportunity.status = OpportunityStatus.DRAFTED
    try:
        await db.flush()
        await _append_event(db, application.id, "created", None, 1)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "Application already exists for this opportunity") from exc
    await db.refresh(application)
    return application


@router.get("", response_model=list[ApplicationRead])
async def list_applications(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: ApplicationStatus | None = None,
) -> list[Application]:
    query = select(Application)
    if status is not None:
        query = query.where(Application.status == status)
    return list((await db.scalars(
        query.order_by(Application.id.desc()).limit(limit).offset(offset)
    )).all())


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(
    application_id: int, db: AsyncSession = Depends(get_db)
) -> Application:
    application = await db.get(Application, application_id)
    if application is None:
        raise HTTPException(404, "Application not found")
    return application


@router.get("/{application_id}/history", response_model=list[EventRead])
async def get_history(
    application_id: int, db: AsyncSession = Depends(get_db)
) -> list[ApplicationEvent]:
    if await db.get(Application, application_id) is None:
        raise HTTPException(404, "Application not found")
    return list((await db.scalars(
        select(ApplicationEvent).where(ApplicationEvent.application_id == application_id)
        .order_by(ApplicationEvent.sequence)
    )).all())


@router.patch("/{application_id}/draft", response_model=ApplicationRead)
async def edit_draft(
    application_id: int, payload: EditDraft, db: AsyncSession = Depends(get_db)
) -> Application:
    application = await _locked_application(db, application_id)
    if application.status != ApplicationStatus.DRAFT:
        raise HTTPException(409, "Only draft applications can be edited")
    try:
        application.draft = clean_draft(payload.draft)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    await _append_event(db, application.id, "edited", None,
                        await _next_sequence(db, application.id))
    await db.commit()
    await db.refresh(application)
    return application


async def _decide(
    application_id: int, action: str, note: str | None, db: AsyncSession
) -> Application:
    application = await _locked_application(db, application_id)
    try:
        application.status = next_status(application.status, action)
    except InvalidTransition as exc:
        raise HTTPException(409, str(exc)) from exc
    opportunity = await db.get(Opportunity, application.opportunity_id)
    if opportunity is None:
        raise HTTPException(409, "Opportunity missing")
    opportunity.status = (
        OpportunityStatus.APPROVED if action == "approve" else OpportunityStatus.REJECTED
    )
    await _append_event(db, application.id, action, note,
                        await _next_sequence(db, application.id))
    await db.commit()
    await db.refresh(application)
    return application


@router.post("/{application_id}/approve", response_model=ApplicationRead)
async def approve(
    application_id: int, payload: Decision, db: AsyncSession = Depends(get_db)
) -> Application:
    return await _decide(application_id, "approve", payload.note, db)


@router.post("/{application_id}/reject", response_model=ApplicationRead)
async def reject(
    application_id: int, payload: Decision, db: AsyncSession = Depends(get_db)
) -> Application:
    return await _decide(application_id, "reject", payload.note, db)
