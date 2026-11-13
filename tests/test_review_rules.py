import pytest

from app.models.application import ApplicationStatus
from app.review.rules import InvalidTransition, clean_draft, next_status


def test_approve_draft() -> None:
    assert next_status(ApplicationStatus.DRAFT, "approve") == ApplicationStatus.APPROVED


def test_reject_draft() -> None:
    assert next_status(ApplicationStatus.DRAFT, "reject") == ApplicationStatus.REJECTED


@pytest.mark.parametrize("status", [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED])
def test_final_decisions_cannot_be_changed(status: ApplicationStatus) -> None:
    with pytest.raises(InvalidTransition):
        next_status(status, "approve")


def test_unknown_action_rejected() -> None:
    with pytest.raises(InvalidTransition):
        next_status(ApplicationStatus.DRAFT, "send")


def test_draft_trimmed() -> None:
    assert clean_draft("  Valid draft text  ") == "Valid draft text"


@pytest.mark.parametrize("draft", ["", "short", "x" * 10001])
def test_invalid_draft_rejected(draft: str) -> None:
    with pytest.raises(ValueError):
        clean_draft(draft)
