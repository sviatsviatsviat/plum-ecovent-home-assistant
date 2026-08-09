"""Resolve writable enum parameters from ecoNET wire values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self

from .edit import EditParamIndex, find_writable_data_entry
from .wire import OPTION_UNSUPPORTED, WireMappedIntEnum


@dataclass(frozen=True, slots=True)
class MappedParamStatus:
    """Validated name-to-id identity and current wire value for a mapped enum."""

    valid: bool
    wire: int | None
    _mode_cls: type[WireMappedIntEnum] = field(compare=False, hash=False, repr=False)

    @classmethod
    def invalid(cls, mode_cls: type[WireMappedIntEnum]) -> Self:
        """Return an unavailable status for ``mode_cls``."""
        return cls(valid=False, wire=None, _mode_cls=mode_cls)

    @property
    def mode(self) -> WireMappedIntEnum | None:
        """Return the writable enum member for the wire, or None."""
        if not self.valid or self.wire is None:
            return None
        return self._mode_cls.from_wire(self.wire)

    @property
    def option(self) -> str | None:
        """Return the select option for the wire, or Unsupported / None."""
        if not self.valid or self.wire is None:
            return None
        mode = self._mode_cls.from_wire(self.wire)
        return mode.option if mode is not None else OPTION_UNSUPPORTED


def parse_wire(value: Any) -> int | None:
    """Parse a curr wire value as an int, rejecting bools and non-integers."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not value.is_integer():
            return None
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def resolve_writable_curr_param(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
    *,
    name: str,
    expected_id: int,
    mode_cls: type[WireMappedIntEnum],
    data_index: EditParamIndex | None = None,
) -> MappedParamStatus:
    """Validate identity and return a mapped value from ``regParams.curr``."""
    invalid = MappedParamStatus.invalid(mode_cls)
    resolved = find_writable_data_entry(
        edit_params,
        reg_params,
        name=name,
        expected_id=expected_id,
        data_index=data_index,
    )
    if resolved is None:
        return invalid

    curr = reg_params.get("curr")
    if not isinstance(curr, dict) or name not in curr:
        return invalid

    wire = parse_wire(curr[name])
    if wire is None:
        return invalid

    return MappedParamStatus(valid=True, wire=wire, _mode_cls=mode_cls)


def resolve_writable_data_param(
    edit_params: dict[str, Any],
    *,
    name: str,
    expected_id: int,
    mode_cls: type[WireMappedIntEnum],
    reg_params: dict[str, Any] | None = None,
    data_index: EditParamIndex | None = None,
) -> MappedParamStatus:
    """Validate identity and return a mapped value from ``editParams.data``."""
    invalid = MappedParamStatus.invalid(mode_cls)
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
    wire = parse_wire(entry.get("value"))
    if wire is None:
        return invalid

    return MappedParamStatus(valid=True, wire=wire, _mode_cls=mode_cls)


# Alias used by bypass mode (#22); same editParams.data wire resolver.
resolve_writable_edit_param = resolve_writable_data_param
