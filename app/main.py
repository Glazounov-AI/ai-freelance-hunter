import logging

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.analysis import router as analysis_router
from app.api.applications import router as applications_router
from app.api.opportunities import router as opportunities_router
from app.core.security import require_admin
from app.db.session import get_db
from app.web.routes import router as dashboard_router

logger = logging.getLogger(__name__)
app = FastAPI(title="AI Freelance Hunter", version="0.5.0", docs_url=None, redoc_url=None)
app.include_router(opportunities_router)
app.include_router(analysis_router)
app.include_router(applications_router)
app.include_router(dashboard_router)


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", dependencies=[Depends(require_admin)])
async def ready(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.get("/api/v1/status", dependencies=[Depends(require_admin)])
async def status() -> dict[str, str]:
    return {"service": "ai-freelance-hunter", "phase": "dashboard"}
