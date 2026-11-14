"""Short-lived signed browser session. No API token is exposed to JavaScript."""
import hashlib
import hmac
import secrets
import time

from fastapi import Cookie, Depends, HTTPException, Request

from app.core.config import Settings, get_settings

COOKIE_NAME = "fh_session"
MAX_AGE = 8 * 3600


def _key(settings: Settings) -> bytes:
    return hashlib.sha256(("web-session-v1:" + settings.admin_api_token.get_secret_value()).encode()).digest()


def issue_session(settings: Settings, now: int | None = None) -> str:
    issued = int(time.time()) if now is None else now
    payload = f"{issued}.{secrets.token_hex(16)}"
    signature = hmac.new(_key(settings), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def valid_session(value: str | None, settings: Settings, now: int | None = None) -> bool:
    if not value or len(value) > 256:
        return False
    parts = value.split(".")
    if len(parts) != 3:
        return False
    stamp, nonce, signature = parts
    if not stamp.isdigit() or len(nonce) != 32 or len(signature) != 64:
        return False
    try:
        int(nonce, 16)
        int(signature, 16)
    except ValueError:
        return False
    current = int(time.time()) if now is None else now
    if int(stamp) > current + 30 or current - int(stamp) > MAX_AGE:
        return False
    payload = f"{stamp}.{nonce}"
    expected = hmac.new(_key(settings), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


def csrf_for(session: str, settings: Settings) -> str:
    return hmac.new(_key(settings), ("csrf:" + session).encode(), hashlib.sha256).hexdigest()


async def require_session(
    fh_session: str | None = Cookie(default=None),
    settings: Settings = Depends(get_settings),
) -> str:
    if not valid_session(fh_session, settings):
        raise HTTPException(401, "Login required")
    assert fh_session is not None
    return fh_session


async def require_csrf(
    request: Request,
    session: str = Depends(require_session),
    settings: Settings = Depends(get_settings),
) -> None:
    # Custom header + same-site cookie prevents cross-site form submissions.
    supplied = request.headers.get("x-csrf-token", "")
    if not hmac.compare_digest(supplied, csrf_for(session, settings)):
        raise HTTPException(403, "Invalid CSRF token")
