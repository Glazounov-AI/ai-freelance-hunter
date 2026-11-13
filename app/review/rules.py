from app.models.application import ApplicationStatus


class InvalidTransition(ValueError):
    pass


def next_status(current: ApplicationStatus, action: str) -> ApplicationStatus:
    allowed = {
        (ApplicationStatus.DRAFT, "approve"): ApplicationStatus.APPROVED,
        (ApplicationStatus.DRAFT, "reject"): ApplicationStatus.REJECTED,
    }
    try:
        return allowed[(current, action)]
    except KeyError as exc:
        raise InvalidTransition(f"Cannot {action} an application in status {current.value}") from exc


def clean_draft(value: str) -> str:
    value = value.strip()
    if not 10 <= len(value) <= 10000:
        raise ValueError("Draft must contain 10 to 10000 characters")
    return value
