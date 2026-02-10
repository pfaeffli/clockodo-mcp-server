"""Datetime normalization utilities for Clockodo API compatibility."""

from __future__ import annotations

from datetime import datetime
from typing import overload


@overload
def normalize_datetime(value: str) -> str: ...


@overload
def normalize_datetime(value: None) -> None: ...


def normalize_datetime(value: str | None) -> str | None:
    """
    Normalize a datetime string to ISO 8601 format for the Clockodo API.

    Handles common LLM-generated formats:
    - "2025-01-01 09:00:00" → "2025-01-01T09:00:00Z"
    - "2025-01-01T09:00:00" → "2025-01-01T09:00:00Z"
    - "2025-01-01T09:00:00Z" → "2025-01-01T09:00:00Z" (passthrough)
    - "2025-01-01T09:00:00+01:00" → "2025-01-01T09:00:00+01:00" (passthrough)

    Args:
        value: Datetime string or None.

    Returns:
        Normalized ISO 8601 string, or None if input is None.

    Raises:
        ValueError: If the string cannot be parsed as a valid datetime.
    """
    if value is None:
        return None

    # Replace space separator with T
    normalized = value.replace(" ", "T", 1)

    # Validate by parsing
    try:
        datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid datetime format: {value!r}") from exc

    # Append Z if no timezone info present
    if "+" not in normalized and not normalized.endswith("Z"):
        normalized += "Z"

    return normalized
