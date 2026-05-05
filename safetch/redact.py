from __future__ import annotations

import re
from urllib.parse import SplitResult, urlsplit, urlunsplit

SENSITIVE_HEADER_NAMES = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
}


def redact_url(value: str) -> str:
    parts = urlsplit(value)
    if not parts.scheme or "@" not in parts.netloc:
        return value

    credentials, host = parts.netloc.rsplit("@", 1)
    if not credentials:
        return value

    redacted = SplitResult(
        scheme=parts.scheme,
        netloc=f"[REDACTED]@{host}",
        path=parts.path,
        query=parts.query,
        fragment=parts.fragment,
    )
    return urlunsplit(redacted)


def redact_header(value: str) -> str:
    if ":" not in value:
        return value

    name, header_value = value.split(":", 1)
    normalized = name.strip().lower()
    stripped_value = header_value.strip()

    if normalized in SENSITIVE_HEADER_NAMES:
        return f"{name}: [REDACTED]"

    if re.search(r"\b(bearer|token|secret|apikey)\b", stripped_value, flags=re.IGNORECASE):
        return f"{name}: [REDACTED]"

    return value


def redact_text(value: str) -> str:
    redacted = re.sub(
        r"(?P<scheme>https?://)(?P<creds>[^/\s:@]+(?::[^/\s@]+)?@)",
        lambda match: f"{match.group('scheme')}[REDACTED]@",
        value,
        flags=re.IGNORECASE,
    )
    redacted = re.sub(
        r"(?i)\b(authorization|proxy-authorization|x-api-key)\s*:\s*[^\r\n]+",
        lambda match: f"{match.group(1)}: [REDACTED]",
        redacted,
    )
    redacted = re.sub(
        r"(?i)\b(bearer)\s+[A-Za-z0-9._~+/=-]+",
        r"\1 [REDACTED]",
        redacted,
    )
    return redacted
