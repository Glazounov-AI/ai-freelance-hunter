from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collection.service import ingest_manual
from app.core.security import require_admin
from app.db.session import get_db
from app.models.opportunity import Opportunity, OpportunityStatus

router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunities"],
                   dependencies=[Depends(require_admin)])


class ManualOpportunityCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=20000)
    url: HttpUrl | None = None
    external_id: str | None = Field(default=None, min_length=1, max_length=255)


class OpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    external_id: str
    title: str
    description: str
    url: str | None
    status: OpportunityStatus
    created_at: datetime


class IngestResponse(BaseModel):
    created: bool
    opportunity: OpportunityRead


@router.post("/manual", response_model=IngestResponse, status_code=201)
async def create_manual(
    payload: ManualOpportunityCreate, db: AsyncSession = Depends(get_db)
) -> IngestResponse:
    try:
        result = await ingest_manual(
            db, title=payload.title, description=payload.description,
            url=str(payload.url) if payload.url else None,
            external_id=payload.external_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return IngestResponse(
        created=result.created,
        opportunity=OpportunityRead.model_validate(result.opportunity),
    )


@router.get("", response_model=list[OpportunityRead])
async def list_opportunities(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: OpportunityStatus | None = None,
) -> list[OpportunityRead]:
    statement = select(Opportunity)
    if status is not None:
        statement = statement.where(Opportunity.status == status)
    statement = statement.order_by(Opportunity.id.desc()).limit(limit).offset(offset)
    rows = (await db.scalars(statement)).all()
    return [OpportunityRead.model_validate(item) for item in rows]


@router.get("/{opportunity_id}", response_model=OpportunityRead)
async def get_opportunity(
    opportunity_id: int, db: AsyncSession = Depends(get_db)
) -> OpportunityRead:
    opportunity = await db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return OpportunityRead.model_validate(opportunity)
