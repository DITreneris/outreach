from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = ""
    supabase_service_role_key: str = ""

    resend_api_key: str = ""
    resend_webhook_secret: str = ""
    outreach_from_email: str = "hello@news.promptanatomy.online"
    outreach_from_name: str = "Prompt Anatomy"

    unsubscribe_signing_secret: str = ""
    internal_api_key: str = ""

    public_base_url: str = "http://localhost:8000"
    product_url: str = "https://promptanatomy.online"
    physical_address: str = "Prompt Anatomy, United States"

    dry_run_default: bool = True
    send_rate_per_second: float = 0.2

    # Warmup caps (override via campaign.daily_cap)
    warmup_week1_daily_cap: int = 50


@lru_cache
def get_settings() -> Settings:
    return Settings()
