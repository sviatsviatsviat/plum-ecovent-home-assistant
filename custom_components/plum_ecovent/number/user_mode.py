"""Writable User Mode number entities."""

from __future__ import annotations

from typing import override

from ..coordinator import PlumEconetCoordinator
from ..models.user_mode import UserModeNumberSpec
from ..parameters import NumberParamStatus
from .spec import PlumEconetSpecNumber


class PlumEconetUserModeNumber(PlumEconetSpecNumber):
    """Number for a User Mode fan velocity or target temperature."""

    _spec: UserModeNumberSpec

    def __init__(
        self,
        coordinator: PlumEconetCoordinator,
        spec: UserModeNumberSpec,
    ) -> None:
        """Initialize the number from a User Mode spec."""
        super().__init__(coordinator, spec)

    @override
    def _resolve(self) -> NumberParamStatus:
        """Return the resolved status for this User Mode parameter."""
        return self.coordinator.number_status(self._spec.param_name)
