"""Base entity for Plum ecoVENT."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_MODEL, DOMAIN, MANUFACTURER, NAME
from .coordinator import PlumEconetCoordinator


class PlumEconetCoordinatorEntity(CoordinatorEntity[PlumEconetCoordinator]):
    """Base class for Plum ecoVENT entities with device registry info."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PlumEconetCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        uid = str(coordinator.sys_params["uid"])
        self._attr_unique_id = f"{uid}_{description.key}"
        model = coordinator.sys_params.get("controllerID") or DEFAULT_MODEL
        sw_version = coordinator.sys_params.get("softVer") or coordinator.sys_params.get(
            "moduleASoftVer"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, uid)},
            manufacturer=MANUFACTURER,
            model=str(model),
            name=NAME,
            sw_version=str(sw_version) if sw_version else None,
        )


class PlumEconetEntity(PlumEconetCoordinatorEntity):
    """Base class for Plum ecoVENT entities backed by regParams.curr."""

    def __init__(
        self,
        coordinator: PlumEconetCoordinator,
        description: EntityDescription,
        *,
        param_name: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, description)
        self._param_name = param_name

    @property
    def available(self) -> bool:
        """Return True when the coordinator is ok and the curr key exists."""
        if not super().available:
            return False
        curr = self.coordinator.reg_params.get("curr")
        return isinstance(curr, dict) and self._param_name in curr

    def _curr_value(self) -> Any | None:
        """Return the live curr value for this entity's parameter, if present."""
        curr = self.coordinator.reg_params.get("curr")
        if not isinstance(curr, dict):
            return None
        return curr.get(self._param_name)
