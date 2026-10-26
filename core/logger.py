"""Logger yang disanitasi: tidak mencatat data sensitif (password, token, cookie, secret)."""

from __future__ import annotations

import re
from typing import Optional


_SENSITIVE_KEYS = re.compile(
    r"(password|token|secret|cookie|authorization|api_key|apikey|access_token|refresh_token)\s*[:=]\s*([^\s,&]+)",
    re.IGNORECASE,
)


def sanitize(value: str) -> str:
    return _SENSITIVE_KEYS.sub(r"\1=***REDACTED***", value)


def safe_log(message: str, level: str = "INFO", sensitive: Optional[str] = None) -> None:
    msg = sanitize(message)
    if sensitive:
        msg = f"{msg} | sensitive_len={len(sensitive)}"
    print(f"[{level}] {msg}")


def info(message: str) -> None:
    safe_log(message, "INFO")


def debug(message: str) -> None:
    safe_log(message, "DEBUG")


def warning(message: str) -> None:
    safe_log(message, "WARNING")


def error(message: str) -> None:
    safe_log(message, "ERROR")