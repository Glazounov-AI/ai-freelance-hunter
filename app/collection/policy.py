from dataclasses import dataclass


@dataclass(frozen=True)
class SourcePolicy:
    code: str
    automated_collection_allowed: bool
    manual_entry_allowed: bool
    reason: str


POLICIES: dict[str, SourcePolicy] = {
    "manual": SourcePolicy("manual", False, True, "User-provided order details only"),
    "fl_ru": SourcePolicy("fl_ru", False, False, "Automated access not yet verified"),
    "kwork": SourcePolicy("kwork", False, False, "Automated access not yet verified"),
    "freelance_ru": SourcePolicy(
        "freelance_ru", False, False, "Automated access not yet verified"
    ),
}


def require_manual_source(code: str) -> None:
    policy = POLICIES.get(code)
    if policy is None or not policy.manual_entry_allowed:
        raise ValueError("Source is not approved for manual ingestion")
