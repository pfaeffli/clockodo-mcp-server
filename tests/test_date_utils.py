import pytest

from clockodo_mcp.date_utils import normalize_datetime


def test_iso8601_passthrough():
    """Already correct ISO 8601 format should pass through unchanged."""
    assert normalize_datetime("2025-01-01T09:00:00Z") == "2025-01-01T09:00:00Z"


def test_space_separated_converted_to_iso():
    """Space-separated datetime should be converted to ISO 8601."""
    assert normalize_datetime("2025-01-01 09:00:00") == "2025-01-01T09:00:00Z"


def test_missing_z_appended():
    """ISO 8601 without Z should get Z appended."""
    assert normalize_datetime("2025-01-01T09:00:00") == "2025-01-01T09:00:00Z"


def test_with_timezone_offset_passthrough():
    """Datetime with timezone offset should pass through without adding Z."""
    assert (
        normalize_datetime("2025-01-01T09:00:00+01:00") == "2025-01-01T09:00:00+01:00"
    )


def test_none_returns_none():
    """None input should return None."""
    assert normalize_datetime(None) is None


def test_invalid_datetime_raises():
    """Invalid datetime string should raise ValueError."""
    with pytest.raises(ValueError, match="Invalid datetime format"):
        normalize_datetime("not-a-date")


def test_space_separated_with_timezone_offset():
    """Space-separated with timezone offset should convert space to T only."""
    assert (
        normalize_datetime("2025-01-01 09:00:00+01:00") == "2025-01-01T09:00:00+01:00"
    )
