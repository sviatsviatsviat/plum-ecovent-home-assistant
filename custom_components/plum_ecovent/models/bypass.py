"""Resolve and validate the BYPmodSett bypass-mode parameter."""

from __future__ import annotations

from typing import Any

from ..const import PARAM_BYPASS_MODE, PARAM_BYPASS_MODE_ID, PARAM_BYPASS_MOTOR_STATE
from ..parameters import (
    OPTION_UNSUPPORTED,
    EditParamIndex,
    MappedParamStatus,
    WireMappedIntEnum,
    parse_wire,
    resolve_writable_edit_param,
)

__all__ = [
    "BYPASS_MODES",
    "BYPASS_MOTOR_STATES",
    "BypassMode",
    "BypassModeStatus",
    "BypassMotorState",
    "OPTION_UNSUPPORTED",
    "resolve_bypass_mode",
    "resolve_bypass_motor_state_option",
]

BypassModeStatus = MappedParamStatus


class BypassMode(WireMappedIntEnum):
    """Writable BYPmodSett wire values (Auto / Open / Close)."""

    CLOSE = 265
    OPEN = 273
    AUTO = 289


# Select option order: Auto, Open, Close.
BYPASS_MODES: tuple[BypassMode, ...] = (
    BypassMode.AUTO,
    BypassMode.OPEN,
    BypassMode.CLOSE,
)


class BypassMotorState(WireMappedIntEnum):
    """Live BYPmodState wire values (Off / On)."""

    OFF = 0
    ON = 1


BYPASS_MOTOR_STATES: tuple[BypassMotorState, ...] = (
    BypassMotorState.OFF,
    BypassMotorState.ON,
)


def resolve_bypass_mode(
    edit_params: dict[str, Any],
    data_index: EditParamIndex | None = None,
) -> BypassModeStatus:
    """Validate BYPmodSett id/edit and return the wire from editParams.data."""
    return resolve_writable_edit_param(
        edit_params,
        name=PARAM_BYPASS_MODE,
        expected_id=PARAM_BYPASS_MODE_ID,
        mode_cls=BypassMode,
        data_index=data_index,
    )


def resolve_bypass_motor_state_option(reg_params: dict[str, Any]) -> str | None:
    """Return Off/On/Unsupported from regParams.curr, or None if missing."""
    curr = reg_params.get("curr")
    if not isinstance(curr, dict) or PARAM_BYPASS_MOTOR_STATE not in curr:
        return None
    wire = parse_wire(curr[PARAM_BYPASS_MOTOR_STATE])
    if wire is None:
        return None
    mode = BypassMotorState.from_wire(wire)
    return mode.option if mode is not None else OPTION_UNSUPPORTED
