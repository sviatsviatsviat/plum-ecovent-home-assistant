"""Parse numeric values returned by the ecoNET protocol."""

from __future__ import annotations

import math
from typing import Any


def parse_finite_number(value: Any) -> float | None:
    """Return a finite float, or None if missing/invalid (including bool)."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number):
        return None
    return number
