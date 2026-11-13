import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.collection.normalize import normalize_opportunity
from app.collection.policy import POLICIES, require_manual_source
from app.collection.service import ingest_manual
from app.db.base import Base
from app.models.opportunity import OpportunityStatus
from app.schemas.opportunity import OpportunityInput


def test_normalization() -> None:
    value = normalize_opportunity(
        OpportunityInput(
            source_code=" MANUAL ", external_id="  A  ",
            title="  Python   developer ", description=" Need   an API "
        )
    )
    assert value.source_code == "manual"
    assert value.title == "Python developer"


def test_unknown_or_unverified_sources_blocked() -> None:
    assert POLICIES["fl_ru"].automated_collection_allowed is False
    for code in ("fl_ru", "kwork", "unknown"):
        with pytest.raises(ValueError):
            require_manual_source(code)


@pytest.mark.asyncio
async def test_manual_ingestion_idempotent() -> None:
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        first = await ingest_manual(
            session, title="  API   development  ", description=" Build an API ",
            url=None, external_id="order-123",
        )
        second = await ingest_manual(
            session, title="API development", description="Build an API",
            url=None, external_id="order-123",
        )
        assert first.created is True
        assert second.created is False
        assert first.opportunity.id == second.opportunity.id
        assert first.opportunity.title == "API development"
        assert first.opportunity.status == OpportunityStatus.NEW
    await engine.dispose()
