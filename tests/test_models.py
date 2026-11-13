import pytest
from pydantic import ValidationError

from app.schemas.opportunity import OpportunityInput


def test_opportunity_input() -> None:
    value = OpportunityInput(source_code="manual", external_id="123", title="Bot",
                             description="Build a bot")
    assert value.source_code == "manual"


def test_empty_title_rejected() -> None:
    with pytest.raises(ValidationError):
        OpportunityInput(source_code="manual", external_id="123", title="",
                         description="Build a bot")
