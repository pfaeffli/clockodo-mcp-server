"""Tests for normalize_datetime (naive local time -> UTC Z)."""

import pytest

from clockodo_mcp.date_utils import normalize_datetime


@pytest.mark.parametrize(
    "value,expected",
    [
        ("2025-01-01T09:00:00Z", "2025-01-01T09:00:00Z"),
        # Naive input is Europe/Zurich: CET (+1) in winter, CEST (+2) in summer.
        ("2025-01-01T09:00:00", "2025-01-01T08:00:00Z"),
        ("2025-01-01 09:00:00", "2025-01-01T08:00:00Z"),
        ("2025-07-01T09:00:00", "2025-07-01T07:00:00Z"),
        ("2025-07-01 09:00", "2025-07-01T07:00:00Z"),
        # DST end 2026-10-25: 01:30 is still CEST, 03:30 is CET.
        ("2026-10-25T01:30:00", "2026-10-24T23:30:00Z"),
        ("2026-10-25T03:30:00", "2026-10-25T02:30:00Z"),
        # Aware input is converted.
        ("2025-07-01T09:00:00+02:00", "2025-07-01T07:00:00Z"),
        ("2025-01-01 09:00:00+01:00", "2025-01-01T08:00:00Z"),
        ("2025-01-01T09:00:00-05:00", "2025-01-01T14:00:00Z"),
        ("2025-01-01T09:00:00+00:00", "2025-01-01T09:00:00Z"),
    ],
)
def test_normalize_to_utc(value, expected):
    """Every accepted format ends up as UTC with a Z suffix."""
    assert normalize_datetime(value) == expected


def test_timezone_env_override(monkeypatch):
    """CLOCKODO_TIMEZONE changes the zone used for naive input."""
    monkeypatch.setenv("CLOCKODO_TIMEZONE", "America/New_York")
    assert normalize_datetime("2025-01-01T09:00:00") == "2025-01-01T14:00:00Z"


def test_none_returns_none():
    """None input should return None."""
    assert normalize_datetime(None) is None


def test_invalid_datetime_raises():
    """Invalid datetime string should raise ValueError."""
    with pytest.raises(ValueError, match="Invalid datetime format"):
        normalize_datetime("not-a-date")


def test_date_only_raises():
    """Date-only input is ambiguous and must be refused."""
    with pytest.raises(ValueError, match="time is required"):
        normalize_datetime("2025-01-01")
