import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.engine import analyze_offline
from app.ai.llm import analyze_with_openai
from app.ai.profile import load_profile
from app.core.security import require_admin
from app.db.session import get_db
from app.models.analysis import OpportunityAnalysis
from app.models.opportunity import Opportunity, OpportunityStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"],
                   dependencies=[Depends(require_admin)])


class AnalyzeRequest(BaseModel):
    opportunity_id: int = Field(ge=1)
    mode: str = Field(default="offline", pattern="^(offline|openai)$")


class AnalyzeResponse(BaseModel):
    analysis_id: int
    opportunity_id: int
    mode: str
    score: int
    matched_skills: list[str]
    explanation: str
    warnings: list[str]
    draft: str
    requires_human_review: bool = True


@router.post("", response_model=AnalyzeResponse)
async def analyze_order(payload: AnalyzeRequest,
                        db: AsyncSession = Depends(get_db)) -> AnalyzeResponse:
    opportunity = await db.get(Opportunity, payload.opportunity_id)
    if opportunity is None:
        raise HTTPException(404, "Opportunity not found")
    if opportunity.status in {OpportunityStatus.APPROVED, OpportunityStatus.SENT,
                              OpportunityStatus.SEND_UNCERTAIN}:
        raise HTTPException(409, "Cannot reanalyze an approved or sent opportunity")
    try:
        profile = load_profile()
    except (OSError, ValueError) as exc:
        logger.warning("Profile unavailable or invalid: %s", type(exc).__name__)
        raise HTTPException(503, "Verified freelancer profile unavailable") from exc
    if payload.mode == "openai":
        try:
            result = await analyze_with_openai(opportunity.title, opportunity.description,
                                               profile)
        except Exception as exc:
            # Do not leak upstream response bodies or credentials.
            logger.warning("AI provider failed: %s", type(exc).__name__)
            raise HTTPException(502, "AI provider unavailable or response rejected") from exc
    else:
        result = analyze_offline(opportunity.title, opportunity.description, profile)
    record = OpportunityAnalysis(
        opportunity_id=opportunity.id, mode=payload.mode, score=result.score,
        explanation=result.explanation,
        matched_skills_json=json.dumps(list(result.matched_skills), ensure_ascii=False),
        warnings_json=json.dumps(list(result.warnings), ensure_ascii=False),
        draft=result.draft,
    )
    db.add(record)
    opportunity.status = OpportunityStatus.ANALYZED
    await db.commit()
    await db.refresh(record)
    return AnalyzeResponse(
        analysis_id=record.id, opportunity_id=opportunity.id, mode=payload.mode,
        score=result.score, matched_skills=list(result.matched_skills),
        explanation=result.explanation, warnings=list(result.warnings),
        draft=result.draft,
    )
