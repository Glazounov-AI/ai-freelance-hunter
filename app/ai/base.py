from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.schemas.opportunity import OpportunityInput


class OpportunityAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    rationale: str
    uncertainties: list[str] = Field(default_factory=list)


class OpportunityAnalyzer(ABC):
    @abstractmethod
    async def analyze(self, opportunity: OpportunityInput) -> OpportunityAssessment:
        """Analyze untrusted opportunity text without side effects."""
