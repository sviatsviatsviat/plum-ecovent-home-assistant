"""Map integer protocol values to Home Assistant option keys."""

from __future__ import annotations

from enum import IntEnum
from typing import Self

OPTION_UNSUPPORTED = "unsupported"


class WireMappedIntEnum(IntEnum):
    """IntEnum with select option keys derived from member names."""

    @property
    def option(self) -> str:
        """Return the select/translation key (e.g. ``halt``, ``airing``)."""
        return self.name.lower()

    @classmethod
    def from_wire(cls, wire: int) -> Self | None:
        """Return the member for a wire value, or None if not writable."""
        try:
            return cls(wire)
        except ValueError:
            return None

    @classmethod
    def from_option(cls, option: str) -> Self | None:
        """Return the member for a select option key, or None if invalid."""
        try:
            return cls[option.upper()]
        except KeyError:
            return None
