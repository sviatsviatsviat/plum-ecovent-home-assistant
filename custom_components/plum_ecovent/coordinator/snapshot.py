"""Atomic ecoNET data snapshot construction."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from ..models.additional_work import (
    AdditionalWorkModeStatus,
    resolve_additional_work_mode,
)
from ..models.additional_work_presets import (
    ADDITIONAL_WORK_MODE_COUNTDOWNS,
    ADDITIONAL_WORK_MODE_NUMBERS,
    resolve_additional_work_mode_countdown,
    resolve_additional_work_mode_number,
)
from ..models.bypass import BypassModeStatus, resolve_bypass_mode
from ..models.filter import FilterStatus, resolve_filter_status
from ..models.operation import OperationModeStatus, resolve_operation_mode
from ..models.summer_winter import (
    SummerWinterModeStatus,
    resolve_summer_hysteresis,
    resolve_summer_winter_mode,
    resolve_winter_active_temp,
)
from ..models.user_mode import USER_MODE_NUMBERS, resolve_user_mode_number
from ..models.work import WorkStatus, resolve_work_status
from ..parameters import (
    EditableNumberStatus,
    EditParamIndex,
    NumberParamStatus,
    build_data_index,
)


@dataclass(frozen=True, slots=True)
class PlumEconetData:
    """One validated, atomic snapshot of the ecoNET module."""

    sys_params: dict[str, Any]
    reg_params: dict[str, Any]
    edit_params: dict[str, Any]
    edit_param_index: EditParamIndex
    filter_status: FilterStatus
    work_status: WorkStatus
    operation_mode: OperationModeStatus
    additional_work_mode: AdditionalWorkModeStatus
    summer_winter_mode: SummerWinterModeStatus
    winter_active_temp: EditableNumberStatus
    summer_hysteresis: EditableNumberStatus
    bypass_mode: BypassModeStatus
    number_statuses: Mapping[str, NumberParamStatus]


def build_snapshot(
    sys_params: dict[str, Any],
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> PlumEconetData:
    """Build all indexes and derived states before publishing a snapshot."""
    data_index = MappingProxyType(build_data_index(edit_params))
    number_statuses = {
        spec.param_name: resolve_additional_work_mode_number(
            reg_params,
            edit_params,
            spec,
            data_index,
        )
        for spec in ADDITIONAL_WORK_MODE_NUMBERS
    }
    number_statuses.update(
        {
            spec.param_name: resolve_user_mode_number(
                reg_params,
                edit_params,
                spec,
                data_index,
            )
            for spec in USER_MODE_NUMBERS
        }
    )
    number_statuses.update(
        {
            spec.param_name: resolve_additional_work_mode_countdown(
                edit_params,
                spec,
                data_index,
            )
            for spec in ADDITIONAL_WORK_MODE_COUNTDOWNS
        }
    )
    return PlumEconetData(
        sys_params=sys_params,
        reg_params=reg_params,
        edit_params=edit_params,
        edit_param_index=data_index,
        filter_status=resolve_filter_status(edit_params, data_index),
        work_status=resolve_work_status(edit_params),
        operation_mode=resolve_operation_mode(reg_params, edit_params, data_index),
        additional_work_mode=resolve_additional_work_mode(
            reg_params, edit_params, data_index
        ),
        summer_winter_mode=resolve_summer_winter_mode(
            edit_params, reg_params, data_index
        ),
        winter_active_temp=resolve_winter_active_temp(
            edit_params, reg_params, data_index
        ),
        summer_hysteresis=resolve_summer_hysteresis(
            edit_params, reg_params, data_index
        ),
        bypass_mode=resolve_bypass_mode(edit_params, data_index),
        number_statuses=MappingProxyType(number_statuses),
    )
