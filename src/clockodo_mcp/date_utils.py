"""Datetime normalization utilities for Clockodo API compatibility."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import overload
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "Europe/Zurich"
_DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@overload
def normalize_datetime(value: str) -> str: ...


@overload
def normalize_datetime(value: None) -> None: ...


def normalize_datetime(value: str | None) -> str | None:
    """
    Normalize a datetime string to the UTC format the Clockodo API requires.

    Clockodo v2 accepts only ``YYYY-MM-DDTHH:MM:SSZ``. Input handling:
    - Naive times ("2025-01-01 09:00", "2025-01-01T09:00:00") are interpreted
      in the zone from ``CLOCKODO_TIMEZONE`` (default ``Europe/Zurich``).
    - Aware times ("...Z", "...+02:00", "...-05:00") are converted to UTC.
    - Date-only input is refused: a time is required.

    Args:
        value: Datetime string or None.

    Returns:
        UTC string like "2025-01-01T08:00:00Z", or None if input is None.

    Raises:
        ValueError: If the string is not a valid datetime or has no time part.
    """
    if value is None:
        return None

    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid datetime format: {value!r}") from exc

    if _DATE_ONLY.match(text):
        raise ValueError(
            f"A time is required, got date only: {value!r} "
            "(use e.g. 2025-01-01T09:00:00)"
        )

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=get_local_timezone())

    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_local_timezone() -> ZoneInfo:
    """Return the zone for naive times (``CLOCKODO_TIMEZONE``, default Zurich)."""
    name = os.getenv("CLOCKODO_TIMEZONE") or DEFAULT_TIMEZONE
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"Unknown timezone in CLOCKODO_TIMEZONE: {name!r}") from exc
