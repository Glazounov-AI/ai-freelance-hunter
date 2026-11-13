import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

PLACEHOLDER_PHRASES = (
    "укажите проверяемый факт",
    "укажите подтверждённый опыт",
    "укажите подтвержденный опыт",
    "заполните описание",
    "todo",
    "tbd",
    "your proof here",
)


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill: str = Field(min_length=2, max_length=80)
    proof: str = Field(min_length=5, max_length=500)

    @field_validator("skill", "proof")
    @classmethod
    def validate_evidence(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Поле не может быть пустым")

        normalized = value.casefold()

        if any(phrase in normalized for phrase in PLACEHOLDER_PHRASES):
            raise ValueError(
                "Профиль содержит незаполненный шаблон вместо подтверждённого опыта"
            )

        return value


class FreelancerProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=100)
    evidence: list[Evidence] = Field(min_length=1, max_length=30)
    restrictions: list[str] = Field(default_factory=list, max_length=20)


def load_profile(path: str = "config/freelancer-profile.json") -> FreelancerProfile:
    # No arbitrary path supplied by an API client.
    raw = Path(path).read_text(encoding="utf-8")

    if len(raw) > 30000:
        raise ValueError("Profile is too large")

    return FreelancerProfile.model_validate(json.loads(raw))
