import os

from cpb_outreach.unsubscribe_tokens import (
    create_unsubscribe_token,
    unsubscribe_url,
    verify_unsubscribe_token,
)


def test_unsubscribe_roundtrip(monkeypatch):
    monkeypatch.setenv("UNSUBSCRIBE_SIGNING_SECRET", "test-secret-key-32bytes-long!!")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://example.com")
    from cpb_outreach.config import get_settings

    get_settings.cache_clear()

    email = "Teacher@School.edu"
    token = create_unsubscribe_token(email)
    assert verify_unsubscribe_token(email, token)
    assert "unsubscribe" in unsubscribe_url(email)
