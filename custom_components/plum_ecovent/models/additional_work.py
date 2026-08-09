"""Resolve and validate the REKWS4 additional/timed work-mode parameter."""

from __future__ import annotations

from typing import Any

from ..const import PARAM_ADDITIONAL_WORK_MODE, PARAM_ADDITIONAL_WORK_MODE_ID
from ..parameters import (
    OPTION_UNSUPPORTED,
    EditParamIndex,
    MappedParamStatus,
    WireMappedIntEnum,
    resolve_writable_curr_param,
)

__all__ = [
    "ADDITIONAL_WORK_MODES",
    "OPTION_UNSUPPORTED",
    "AdditionalWorkMode",
    "AdditionalWorkModeStatus",
    "resolve_additional_work_mode",
]

AdditionalWorkModeStatus = MappedParamStatus


class AdditionalWorkMode(WireMappedIntEnum):
    """Writable REKWS4 wire values (Off / Outside / Party / Airing)."""

    OFF = 0
    OUTSIDE = 1
    PARTY = 2
    AIRING = 4


# Select option order: Off, Outside, Party, Airing.
ADDITIONAL_WORK_MODES: tuple[AdditionalWorkMode, ...] = (
    AdditionalWorkMode.OFF,
    AdditionalWorkMode.OUTSIDE,
    AdditionalWorkMode.PARTY,
    AdditionalWorkMode.AIRING,
)


def resolve_additional_work_mode(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
    data_index: EditParamIndex | None = None,
) -> AdditionalWorkModeStatus:
    """Validate REKWS4 id/edit/curr and return the live wire value."""
    return resolve_writable_curr_param(
        reg_params,
        edit_params,
        name=PARAM_ADDITIONAL_WORK_MODE,
        expected_id=PARAM_ADDITIONAL_WORK_MODE_ID,
        mode_cls=AdditionalWorkMode,
        data_index=data_index,
    )
