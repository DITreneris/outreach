import re
import socket

import dns.resolver

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def syntax_ok(email: str) -> bool:
    return bool(EMAIL_RE.match(email.strip()))


def mx_exists(domain: str) -> bool:
    try:
        answers = dns.resolver.resolve(domain, "MX")
        return len(answers) > 0
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, Exception):
        return False


def verify_email(email: str) -> tuple[bool, str]:
    """Lightweight verification: syntax + MX. No SMTP RCPT (many .edu block probes)."""
    normalized = email.strip().lower()
    if not syntax_ok(normalized):
        return False, "invalid_syntax"
    domain = normalized.split("@", 1)[1]
    if not mx_exists(domain):
        return False, "no_mx"
    return True, "mx_ok"
