"""Writable additional / timed work mode number entities."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ..models.additional_work_presets import AdditionalWorkModeNumberSpec
from ..parameters import NumberParamStatus
from .spec import PlumEconetSpecNumber

if TYPE_CHECKING:
    from ..coordinator import PlumEconetCoordinator


class PlumEconetAdditionalWorkModeNumber(PlumEconetSpecNumber):
    """Number for a Party / Outside / Airing duration, fan, or temperature."""

    _spec: AdditionalWorkModeNumberSpec

    def __init__(
        self,
        coordinator: PlumEconetCoordinator,
        spec: AdditionalWorkModeNumberSpec,
    ) -> None:
        """Initialize the number from an additional-mode preset spec."""
        super().__init__(coordinator, spec)

    @override
    def _resolve(self) -> NumberParamStatus:
        """Return the resolved status for this preset parameter."""
        return self.coordinator.number_status(self._spec.param_name)
