from functools import lru_cache

from supabase import Client, create_client

from cpb_outreach.config import get_settings


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    api_key = settings.supabase_api_key()
    if not settings.supabase_url or not api_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or publishable key for dev) are required"
        )
    return create_client(settings.supabase_url, api_key)


def normalize_email(email: str) -> str:
    return email.strip().lower()
