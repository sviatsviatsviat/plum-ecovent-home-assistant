"""Resolve writable and read-only numeric ecoNET parameters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from .edit import (
    EditParamIndex,
    find_data_entry_by_name,
    find_writable_data_entry,
)
from .numeric import parse_finite_number


@dataclass(frozen=True, slots=True)
class EditableNumberStatus:
    """Validated identity and numeric value from ``editParams.data``."""

    valid: bool
    value: float | None
    min_value: float | None
    max_value: float | None

    @classmethod
    def invalid(cls) -> Self:
        """Return an unavailable numeric status."""
        return cls(valid=False, value=None, min_value=None, max_value=None)


@dataclass(frozen=True, slots=True)
class NumberParamStatus:
    """Validated identity and live numeric value for a writable parameter."""

    valid: bool
    value: float | None
    min_value: float | None
    max_value: float | None
    param_id: int | None

    @classmethod
    def invalid(cls) -> Self:
        """Return an unavailable numeric status."""
        return cls(
            valid=False,
            value=None,
            min_value=None,
            max_value=None,
            param_id=None,
        )


def resolve_writable_data_number(
    edit_params: dict[str, Any],
    *,
    name: str,
    expected_id: int,
    reg_params: dict[str, Any] | None = None,
    fallback_min: float | None = None,
    fallback_max: float | None = None,
    data_index: EditParamIndex | None = None,
) -> EditableNumberStatus:
    """Validate identity and return value/min/max from ``editParams.data``."""
    invalid = EditableNumberStatus.invalid()
    resolved = find_writable_data_entry(
        edit_params,
        reg_params,
        name=name,
        expected_id=expected_id,
        data_index=data_index,
    )
    if resolved is None:
        return invalid

    _, entry = resolved
    value = parse_finite_number(entry.get("value"))
    if value is None:
        return invalid

    min_value = parse_finite_number(entry.get("minv"))
    max_value = parse_finite_number(entry.get("maxv"))
    if (
        min_value is None
        or max_value is None
        or (min_value == 0.0 and max_value == 0.0)
        or min_value > max_value
    ):
        if fallback_min is None or fallback_max is None:
            return invalid
        min_value = fallback_min
        max_value = fallback_max

    return EditableNumberStatus(
        valid=True,
        value=value,
        min_value=min_value,
        max_value=max_value,
    )


def resolve_writable_number_param(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
    *,
    name: str,
    expected_id: int,
    fallback_min: float,
    fallback_max: float,
    data_index: EditParamIndex | None = None,
) -> NumberParamStatus:
    """Validate identity and return the live writable numeric value."""
    invalid = NumberParamStatus.invalid()
    resolved = find_writable_data_entry(
        edit_params,
        reg_params,
        name=name,
        expected_id=expected_id,
        data_index=data_index,
    )
    if resolved is None:
        return invalid

    param_id, entry = resolved
    curr = reg_params.get("curr")
    raw = curr[name] if isinstance(curr, dict) and name in curr else entry.get("value")

    value = parse_finite_number(raw)
    if value is None:
        return invalid

    min_value = parse_finite_number(entry.get("minv"))
    max_value = parse_finite_number(entry.get("maxv"))
    if (
        min_value is None
        or max_value is None
        or (min_value == 0.0 and max_value == 0.0)
        or min_value > max_value
    ):
        min_value = fallback_min
        max_value = fallback_max

    return NumberParamStatus(
        valid=True,
        value=value,
        min_value=min_value,
        max_value=max_value,
        param_id=param_id,
    )


def resolve_readonly_number_param(
    edit_params: dict[str, Any],
    *,
    name: str,
    expected_id: int,
    idle_sentinel: float = -1.0,
    data_index: EditParamIndex | None = None,
) -> NumberParamStatus:
    """Resolve a read-only ``editParams.data`` numeric value by name and id."""
    invalid = NumberParamStatus.invalid()
    resolved = find_data_entry_by_name(edit_params, name, data_index)
    if resolved is None:
        return invalid

    param_id, entry = resolved
    if param_id != expected_id:
        return invalid

    value = parse_finite_number(entry.get("value"))
    if value is None:
        return invalid
    if value == idle_sentinel:
        value = 0.0

    return NumberParamStatus(
        valid=True,
        value=value,
        min_value=None,
        max_value=None,
        param_id=param_id,
    )
