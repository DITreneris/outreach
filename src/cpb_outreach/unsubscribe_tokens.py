import hashlib
import hmac
import time
from urllib.parse import urlencode

from cpb_outreach.config import get_settings
from cpb_outreach.db import normalize_email


def _sign(payload: str) -> str:
    secret = get_settings().unsubscribe_signing_secret
    if not secret:
        raise RuntimeError("UNSUBSCRIBE_SIGNING_SECRET is required")
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def create_unsubscribe_token(email: str, max_age_seconds: int = 60 * 60 * 24 * 365) -> str:
    normalized = normalize_email(email)
    expires = int(time.time()) + max_age_seconds
    payload = f"{normalized}:{expires}"
    sig = _sign(payload)
    return f"{expires}.{sig}"


def verify_unsubscribe_token(email: str, token: str) -> bool:
    normalized = normalize_email(email)
    try:
        expires_str, sig = token.split(".", 1)
        expires = int(expires_str)
    except ValueError:
        return False
    if time.time() > expires:
        return False
    payload = f"{normalized}:{expires}"
    expected = _sign(payload)
    return hmac.compare_digest(expected, sig)


def unsubscribe_url(email: str) -> str:
    settings = get_settings()
    token = create_unsubscribe_token(email)
    qs = urlencode({"email": normalize_email(email), "token": token})
    return f"{settings.public_base_url.rstrip('/')}/unsubscribe?{qs}"
