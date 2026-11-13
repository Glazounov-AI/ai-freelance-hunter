import pytest
from pydantic import ValidationError

from app.ai.engine import analyze_offline
from app.ai.profile import Evidence, FreelancerProfile


@pytest.mark.parametrize(
    "proof",
    [
        "Укажите проверяемый факт о собственном проекте.",
        "TODO: добавить описание проекта",
        "Your proof here",
    ],
)
def test_placeholder_proof_rejected(proof: str) -> None:
    with pytest.raises(ValidationError):
        Evidence(skill="Telegram", proof=proof)


def test_valid_proof_accepted() -> None:
    evidence = Evidence(
        skill="Telegram",
        proof="Разработал Telegram-бота для сбора заявок.",
    )
    assert evidence.skill == "Telegram"


def test_draft_has_no_double_period() -> None:
    profile = FreelancerProfile(
        display_name="Исполнитель",
        evidence=[
            Evidence(
                skill="Telegram",
                proof="Разработал Telegram-бота для сбора заявок.",
            )
        ],
        restrictions=[],
    )

    result = analyze_offline(
        title="Разработка Telegram-бота",
        description="Нужен Telegram-бот для бизнеса",
        profile=profile,
    )

    assert "заявок.. " not in result.draft
    assert "заявок. Могу обсудить" in result.draft