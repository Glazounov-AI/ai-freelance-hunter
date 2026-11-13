import pytest
from pydantic import ValidationError

from app.ai.engine import analyze_offline
from app.ai.llm import LLMResult
from app.ai.profile import Evidence, FreelancerProfile


@pytest.fixture
def profile() -> FreelancerProfile:
    return FreelancerProfile(
        display_name="Test", evidence=[
            Evidence(skill="FastAPI", proof="Built a verified API"),
            Evidence(skill="Telegram", proof="Built a verified bot"),
        ]
    )


def test_offline_matches_only_verified_skills(profile: FreelancerProfile) -> None:
    result = analyze_offline("FastAPI backend", "Need a Telegram bot", profile)
    assert result.score == 50
    assert result.matched_skills == ("FastAPI", "Telegram")
    assert "Built a verified API" in result.draft
    assert "требующий проверки" in result.draft


def test_no_evidence_does_not_fabricate(profile: FreelancerProfile) -> None:
    result = analyze_offline("C++ firmware", "Embedded hardware", profile)
    assert result.score == 0
    assert result.matched_skills == ()
    assert "нет подтверждённых" in result.warnings[1].lower()


def test_llm_response_score_validated() -> None:
    with pytest.raises(ValidationError):
        LLMResult.model_validate({
            "score": 150, "matched_skills": [], "explanation": "long explanation",
            "warnings": [], "draft": "A draft that is long enough",
        })
