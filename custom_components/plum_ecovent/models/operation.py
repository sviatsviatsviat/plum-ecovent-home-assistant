"""Resolve and validate the REKWS1 operation-mode parameter."""

from __future__ import annotations

from typing import Any

from ..const import PARAM_OPERATION_MODE, PARAM_OPERATION_MODE_ID
from ..parameters import (
    OPTION_UNSUPPORTED,
    EditParamIndex,
    MappedParamStatus,
    WireMappedIntEnum,
    resolve_writable_curr_param,
)

__all__ = [
    "OPERATION_MODES",
    "OPTION_UNSUPPORTED",
    "OperationMode",
    "OperationModeStatus",
    "resolve_operation_mode",
]

OperationModeStatus = MappedParamStatus


class OperationMode(WireMappedIntEnum):
    """Writable REKWS1 wire values (Halt + Mode 1–4)."""

    MODE_1 = 3
    MODE_2 = 4
    MODE_3 = 5
    HALT = 6
    MODE_4 = 7


# Select option order: Halt, then Mode 1–4.
OPERATION_MODES: tuple[OperationMode, ...] = (
    OperationMode.HALT,
    OperationMode.MODE_1,
    OperationMode.MODE_2,
    OperationMode.MODE_3,
    OperationMode.MODE_4,
)


def resolve_operation_mode(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
    data_index: EditParamIndex | None = None,
) -> OperationModeStatus:
    """Validate REKWS1 id/edit/curr and return the live wire value."""
    return resolve_writable_curr_param(
        reg_params,
        edit_params,
        name=PARAM_OPERATION_MODE,
        expected_id=PARAM_OPERATION_MODE_ID,
        mode_cls=OperationMode,
        data_index=data_index,
    )
