from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class OpportunityInput(BaseModel):
    source_code: str = Field(min_length=1, max_length=64)
    external_id: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=20000)
    url: HttpUrl | None = None


class ProcessingStage(StrEnum):
    NEW = "new"
    ANALYZED = "analyzed"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    DRAFTED = "drafted"
    APPROVED = "approved"
    SENT = "sent"
    SEND_UNCERTAIN = "send_uncertain"
