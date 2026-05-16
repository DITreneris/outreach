from pathlib import Path

from cpb_outreach.config import get_settings
from cpb_outreach.unsubscribe_tokens import unsubscribe_url

REPO_ROOT = Path(__file__).resolve().parents[2]


def product_link(utm_campaign: str) -> str:
    base = get_settings().product_url.rstrip("/")
    return (
        f"{base}/?utm_source=email&utm_medium=outreach"
        f"&utm_campaign={utm_campaign}"
    )


def render_template(
    template_path: str,
    *,
    contact_name: str | None,
    state: str | None,
    utm_campaign: str,
    to_email: str,
) -> tuple[str, str]:
    path = REPO_ROOT / template_path
    html = path.read_text(encoding="utf-8")
    settings = get_settings()
    greeting = f" {contact_name}" if contact_name else ""
    html = (
        html.replace("{{contact_name_greeting}}", greeting)
        .replace("{{state}}", state or "your")
        .replace("{{product_link}}", product_link(utm_campaign))
        .replace("{{unsubscribe_link}}", unsubscribe_url(to_email))
        .replace("{{physical_address}}", settings.physical_address)
    )
    subject = f"Free K–12 prompt builder for {state or 'US'} teachers"
    return subject, html
