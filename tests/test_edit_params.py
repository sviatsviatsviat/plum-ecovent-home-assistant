"""Tests for editParams indexing and registry identity checks."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from custom_components.plum_ecovent.parameters.edit import find_writable_data_entry


def _payloads(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
    *,
    curr_number: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Copy fixtures and set REKWS1 currNumbers to the given raw value."""
    reg = deepcopy(reg_params)
    edit = deepcopy(edit_params)
    reg["currNumbers"]["REKWS1"] = curr_number
    return reg, edit


@pytest.mark.parametrize(
    "curr_number",
    (
        True,
        False,
        17.5,
        "17",
        None,
    ),
)
def test_find_writable_rejects_non_integral_curr_numbers(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
    curr_number: Any,
) -> None:
    """Test bools, non-integers, and non-numeric IDs fail identity checks."""
    reg, edit = _payloads(reg_params, edit_params, curr_number=curr_number)
    assert (
        find_writable_data_entry(
            edit,
            reg,
            name="REKWS1",
            expected_id=17,
        )
        is None
    )


@pytest.mark.parametrize("curr_number", (17, 17.0))
def test_find_writable_accepts_exact_integer_curr_numbers(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
    curr_number: Any,
) -> None:
    """Test exact integer IDs (including whole floats) pass identity checks."""
    reg, edit = _payloads(reg_params, edit_params, curr_number=curr_number)
    resolved = find_writable_data_entry(
        edit,
        reg,
        name="REKWS1",
        expected_id=17,
    )
    assert resolved is not None
    assert resolved[0] == 17
