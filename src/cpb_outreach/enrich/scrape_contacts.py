import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

ROLE_KEYWORDS = {
    "principal": "principal",
    "instructional_coach": "instructional",
    "media_specialist": "librarian",
    "generic_office": "office",
}


def _normalize_url(url: str) -> str:
    if not url.startswith("http"):
        return f"https://{url}"
    return url


def extract_emails_from_html(html: str, allowed_domain: str | None) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for match in EMAIL_PATTERN.findall(html):
        email = match.lower()
        domain = email.split("@", 1)[1]
        if allowed_domain and not (domain == allowed_domain or domain.endswith(f".{allowed_domain}")):
            continue
        role = "other"
        for role_name, keyword in ROLE_KEYWORDS.items():
            if keyword in email:
                role = role_name
                break
        found.append((email, role))
    return found


def scrape_school_contacts(website_url: str, timeout: float = 15.0) -> list[dict]:
    base = _normalize_url(website_url)
    parsed = urlparse(base)
    allowed_domain = parsed.netloc.removeprefix("www.")

    paths = ["", "/contact", "/contact-us", "/about", "/staff", "/directory"]
    seen: set[str] = set()
    results: list[dict] = []

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        for path in paths:
            url = urljoin(base.rstrip("/") + "/", path.lstrip("/"))
            try:
                response = client.get(url)
                if response.status_code >= 400:
                    continue
                soup = BeautifulSoup(response.text, "html.parser")
                text = soup.get_text(" ", strip=True)
                html = response.text
                for email, role in extract_emails_from_html(html + " " + text, allowed_domain):
                    if email in seen:
                        continue
                    seen.add(email)
                    results.append(
                        {
                            "email": email,
                            "role_target": role,
                            "email_source": f"website_scrape:{url}",
                        }
                    )
            except httpx.HTTPError:
                continue
    return results
