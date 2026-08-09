"""Tests for shared numeric parsing helpers."""

from __future__ import annotations

from custom_components.plum_ecovent.parameters.numeric import parse_finite_number


def test_parse_finite_number_rejects_bool_none_and_non_finite() -> None:
    """Test bool, None, and non-finite values return None."""
    assert parse_finite_number(None) is None
    assert parse_finite_number(True) is None
    assert parse_finite_number(False) is None
    assert parse_finite_number(float("nan")) is None
    assert parse_finite_number(float("inf")) is None
    assert parse_finite_number(float("-inf")) is None
    assert parse_finite_number("not-a-number") is None


def test_parse_finite_number_accepts_numeric_inputs() -> None:
    """Test ints, floats, and numeric strings parse to finite floats."""
    assert parse_finite_number(20) == 20.0
    assert parse_finite_number(25.6) == 25.6
    assert parse_finite_number("21.5") == 21.5


def test_parse_finite_number_rejects_overflow() -> None:
    """Test oversized ints that cannot convert to float return None."""
    assert parse_finite_number(10**10000) is None
