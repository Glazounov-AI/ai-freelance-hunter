from unittest.mock import Mock

from app.web.auth import csrf_for, issue_session, valid_session


def settings():
    value = Mock()
    value.admin_api_token.get_secret_value.return_value = "a" * 40
    return value


def test_session_valid_then_expires():
    config = settings()
    token = issue_session(config, now=1000)
    assert valid_session(token, config, now=1000)
    assert valid_session(token, config, now=1000 + 8 * 3600)
    assert not valid_session(token, config, now=1000 + 8 * 3600 + 1)


def test_session_tampering_is_rejected():
    config = settings()
    token = issue_session(config, now=1000)
    assert not valid_session(token + "a", config, now=1000)
    assert not valid_session(token.replace("1000", "1001", 1), config, now=1001)
    assert len(csrf_for(token, config)) == 64
