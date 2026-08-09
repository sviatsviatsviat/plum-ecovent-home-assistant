"""Shared sensor entity description for Plum ecoVENT."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntityDescription


@dataclass(frozen=True, kw_only=True)
class PlumEconetSensorEntityDescription(SensorEntityDescription):
    """Describes a Plum ecoVENT sensor."""

    param_name: str
