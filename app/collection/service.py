from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.collection.normalize import normalize_opportunity
from app.collection.policy import require_manual_source
from app.models.opportunity import Opportunity, OpportunityStatus, Source
from app.schemas.opportunity import OpportunityInput


@dataclass(frozen=True)
class IngestResult:
    opportunity: Opportunity
    created: bool


async def ensure_manual_source(db: AsyncSession) -> Source:
    source = await db.scalar(select(Source).where(Source.code == "manual"))
    if source is None:
        source = Source(code="manual", name="Manual entry", enabled=True)
        db.add(source)
        await db.flush()
    return source


async def ingest_manual(
    db: AsyncSession,
    *,
    title: str,
    description: str,
    url: str | None,
    external_id: str | None,
) -> IngestResult:
    require_manual_source("manual")
    data = normalize_opportunity(
        OpportunityInput(
            source_code="manual",
            external_id=external_id or uuid4().hex,
            title=title,
            description=description,
            url=url,
        )
    )
    source = await ensure_manual_source(db)
    existing = await db.scalar(
        select(Opportunity).where(
            Opportunity.source_id == source.id,
            Opportunity.external_id == data.external_id,
        )
    )
    if existing is not None:
        await db.commit()
        return IngestResult(existing, False)
    opportunity = Opportunity(
        source_id=source.id,
        external_id=data.external_id,
        title=data.title,
        description=data.description,
        url=str(data.url) if data.url else None,
        status=OpportunityStatus.NEW,
    )
    # Nested savepoint makes the unique constraint safe under concurrent requests.
    try:
        async with db.begin_nested():
            db.add(opportunity)
            await db.flush()
    except IntegrityError:
        existing = await db.scalar(
            select(Opportunity).where(
                Opportunity.source_id == source.id,
                Opportunity.external_id == data.external_id,
            )
        )
        if existing is None:
            raise
        await db.commit()
        return IngestResult(existing, False)
    await db.commit()
    await db.refresh(opportunity)
    return IngestResult(opportunity, True)
