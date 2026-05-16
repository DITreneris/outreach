from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"),
    )
    supabase_service_role_key: str = ""
    supabase_publishable_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "SUPABASE_PUBLISHABLE_KEY",
            "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
        ),
    )

    def supabase_api_key(self) -> str:
        """Prefer service role for Railway; fall back to publishable for local dev only."""
        return self.supabase_service_role_key or self.supabase_publishable_key

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
