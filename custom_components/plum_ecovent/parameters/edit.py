"""Index and validate editable ecoNET parameter payloads."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

type EditParamIndex = Mapping[str, tuple[int, dict[str, Any]]]


def build_data_index(
    edit_params: dict[str, Any],
) -> dict[str, tuple[int, dict[str, Any]]]:
    """Index valid ``editParams.data`` entries by parameter name."""
    index: dict[str, tuple[int, dict[str, Any]]] = {}
    data = edit_params.get("data")
    if not isinstance(data, dict):
        return index
    for key, entry in data.items():
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not isinstance(name, str) or name in index:
            continue
        try:
            param_id = int(key)
        except (TypeError, ValueError):
            continue
        index[name] = (param_id, entry)
    return index


def find_data_entry_by_name(
    edit_params: dict[str, Any],
    name: str,
    data_index: EditParamIndex | None = None,
) -> tuple[int, dict[str, Any]] | None:
    """Find ``editParams.data`` entry by ``name`` and return ``(id, entry)``."""
    if data_index is not None:
        return data_index.get(name)

    return build_data_index(edit_params).get(name)


def find_writable_data_entry(
    edit_params: dict[str, Any],
    reg_params: dict[str, Any] | None,
    *,
    name: str,
    expected_id: int,
    data_index: EditParamIndex | None = None,
) -> tuple[int, dict[str, Any]] | None:
    """Return an editable entry when name-to-id identity checks pass."""
    resolved = find_data_entry_by_name(edit_params, name, data_index)
    if resolved is None:
        return None

    param_id, entry = resolved
    if param_id != expected_id or entry.get("edit") is not True:
        return None

    if reg_params is not None:
        curr_numbers = reg_params.get("currNumbers")
        if isinstance(curr_numbers, dict) and name in curr_numbers:
            if not _matches_expected_param_id(curr_numbers[name], expected_id):
                return None

    return resolved


def _matches_expected_param_id(raw: Any, expected_id: int) -> bool:
    """Return True when ``raw`` is an exact integer equal to ``expected_id``.

    Rejects booleans and non-integral numbers (``int(True)`` / ``int(17.5)``
    would otherwise pass a bare ``int(...)`` conversion).
    """
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return False
    if isinstance(raw, float) and not raw.is_integer():
        return False
    try:
        return int(raw) == expected_id
    except (TypeError, ValueError, OverflowError):
        return False
