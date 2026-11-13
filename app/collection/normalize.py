import re
import unicodedata

from app.schemas.opportunity import OpportunityInput


def normalize_opportunity(data: OpportunityInput) -> OpportunityInput:
    def clean(value: str) -> str:
        return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()

    values = data.model_dump()
    for field in ("source_code", "external_id", "title", "description"):
        values[field] = clean(values[field])
    values["source_code"] = values["source_code"].lower()
    if any(not values[field] for field in ("source_code", "external_id", "title", "description")):
        raise ValueError("Required fields cannot be blank after normalization")
    return OpportunityInput.model_validate(values)
