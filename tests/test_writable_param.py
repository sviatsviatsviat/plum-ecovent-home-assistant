"""Tests for writable curr-param resolution and unmapped-wire warnings."""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any

import pytest

from custom_components.plum_ecovent import parameters as parameters_mod
from custom_components.plum_ecovent.const import (
    PARAM_ADDITIONAL_WORK_MODE,
    PARAM_ADDITIONAL_WORK_MODE_ID,
    PARAM_BYPASS_MODE,
    PARAM_BYPASS_MODE_ID,
    PARAM_OPERATION_MODE,
    PARAM_OPERATION_MODE_ID,
)
from custom_components.plum_ecovent.models.additional_work import AdditionalWorkMode
from custom_components.plum_ecovent.models.bypass import BypassMode
from custom_components.plum_ecovent.models.operation import OperationMode
from custom_components.plum_ecovent.parameters import (
    WireMappedIntEnum,
    resolve_writable_curr_param,
    resolve_writable_edit_param,
)

PARAM_CASES = (
    pytest.param(
        PARAM_OPERATION_MODE,
        PARAM_OPERATION_MODE_ID,
        OperationMode,
        0,
        OperationMode.HALT,
        id="rekws1",
    ),
    pytest.param(
        PARAM_ADDITIONAL_WORK_MODE,
        PARAM_ADDITIONAL_WORK_MODE_ID,
        AdditionalWorkMode,
        3,
        AdditionalWorkMode.OFF,
        id="rekws4",
    ),
)


def _resolve(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
    *,
    name: str,
    expected_id: int,
    mode_cls: type[WireMappedIntEnum],
    wire: int,
) -> None:
    reg = deepcopy(reg_params)
    reg["curr"] = {**reg["curr"], name: wire}
    resolve_writable_curr_param(
        reg,
        edit_params,
        name=name,
        expected_id=expected_id,
        mode_cls=mode_cls,
    )


@pytest.mark.parametrize(
    ("name", "expected_id", "mode_cls", "unmapped_wire", "_mapped_wire"),
    PARAM_CASES,
)
def test_unmapped_wire_resolver_is_pure(
    caplog: pytest.LogCaptureFixture,
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
    name: str,
    expected_id: int,
    mode_cls: type[WireMappedIntEnum],
    unmapped_wire: int,
    _mapped_wire: WireMappedIntEnum,
) -> None:
    """Test unexpected wires resolve without logging from the pure helper."""
    with caplog.at_level(logging.WARNING, logger=parameters_mod.__name__):
        _resolve(
            reg_params,
            edit_params,
            name=name,
            expected_id=expected_id,
            mode_cls=mode_cls,
            wire=unmapped_wire,
        )
        _resolve(
            reg_params,
            edit_params,
            name=name,
            expected_id=expected_id,
            mode_cls=mode_cls,
            wire=unmapped_wire,
        )

    messages = [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.WARNING
    ]
    assert messages == []


@pytest.mark.parametrize(
    ("name", "expected_id", "mode_cls", "_unmapped_wire", "mapped_wire"),
    PARAM_CASES,
)
def test_mapped_wire_does_not_log(
    caplog: pytest.LogCaptureFixture,
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
    name: str,
    expected_id: int,
    mode_cls: type[WireMappedIntEnum],
    _unmapped_wire: int,
    mapped_wire: WireMappedIntEnum,
) -> None:
    """Test known enum wires do not warn for each mapped select."""
    with caplog.at_level(logging.WARNING, logger=parameters_mod.__name__):
        _resolve(
            reg_params,
            edit_params,
            name=name,
            expected_id=expected_id,
            mode_cls=mode_cls,
            wire=int(mapped_wire),
        )

    assert not [
        record
        for record in caplog.records
        if record.levelno == logging.WARNING
        and "Unsupported" in record.getMessage()
    ]


def _resolve_edit(
    edit_params: dict[str, Any],
    *,
    name: str,
    expected_id: int,
    mode_cls: type[WireMappedIntEnum],
    wire: int,
) -> None:
    edit = deepcopy(edit_params)
    edit["data"][str(expected_id)] = {
        **edit["data"][str(expected_id)],
        "value": wire,
    }
    resolve_writable_edit_param(
        edit,
        name=name,
        expected_id=expected_id,
        mode_cls=mode_cls,
    )


def test_edit_param_unmapped_wire_resolver_is_pure(
    caplog: pytest.LogCaptureFixture,
    edit_params: dict[str, Any],
) -> None:
    """Test editParams wire resolution leaves transition logging to coordinator."""
    with caplog.at_level(logging.WARNING, logger=parameters_mod.__name__):
        _resolve_edit(
            edit_params,
            name=PARAM_BYPASS_MODE,
            expected_id=PARAM_BYPASS_MODE_ID,
            mode_cls=BypassMode,
            wire=257,
        )
        _resolve_edit(
            edit_params,
            name=PARAM_BYPASS_MODE,
            expected_id=PARAM_BYPASS_MODE_ID,
            mode_cls=BypassMode,
            wire=257,
        )

    messages = [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.WARNING
    ]
    assert messages == []


def test_edit_param_mapped_wire_does_not_log(
    caplog: pytest.LogCaptureFixture,
    edit_params: dict[str, Any],
) -> None:
    """Test known BYPmodSett wires do not warn."""
    with caplog.at_level(logging.WARNING, logger=parameters_mod.__name__):
        _resolve_edit(
            edit_params,
            name=PARAM_BYPASS_MODE,
            expected_id=PARAM_BYPASS_MODE_ID,
            mode_cls=BypassMode,
            wire=int(BypassMode.AUTO),
        )

    assert not [
        record
        for record in caplog.records
        if record.levelno == logging.WARNING
        and "Unsupported" in record.getMessage()
    ]
