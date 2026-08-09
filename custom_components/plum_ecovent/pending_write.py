"""Sticky optimistic state for writable Plum ecoVENT entities.

After a successful ``newParam`` write the LAN API may still return the previous
value from ``regParams`` / ``editParams`` for a few polls. Coordinator refreshes
continue as usual; while a pending write is within its deadline, entity state
prefers the optimistic value until the device snapshot matches or the timeout
elapses.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from .const import PENDING_WRITE_TIMEOUT

_LOGGER = logging.getLogger(__name__)

ATTR_PENDING_WRITE = "pending_write"
ATTR_PENDING_UNTIL = "pending_until"

__all__ = [
    "ATTR_PENDING_UNTIL",
    "ATTR_PENDING_WRITE",
    "PlumEconetPendingWriteMixin",
]


class PlumEconetPendingWriteMixin:
    """Overlay a pending write on top of live coordinator snapshots."""

    _pending_value: Any | None = None
    _pending_deadline: datetime | None = None
    _write_seq: int = 0
    _expiry_unsub: CALLBACK_TYPE | None = None

    def _pending_device_value(self) -> Any:
        """Return the live device value (not the pending overlay)."""
        raise NotImplementedError

    def pending_active(self) -> bool:
        """Return True when an unconfirmed pending write is still recorded."""
        return self._pending_value is not None and self._pending_deadline is not None

    def begin_write(self) -> int:
        """Bump the write sequence and return the token for this attempt."""
        self._write_seq += 1
        return self._write_seq

    def set_pending(self, value: Any, *, write_seq: int) -> bool:
        """Record an optimistic value if ``write_seq`` is still current."""
        if write_seq != self._write_seq:
            return False
        self._cancel_expiry()
        self._pending_value = value
        self._pending_deadline = dt_util.utcnow() + timedelta(
            seconds=PENDING_WRITE_TIMEOUT
        )
        self._schedule_expiry()
        return True

    def clear_pending(self) -> None:
        """Drop the optimistic overlay and cancel any expiry callback."""
        self._cancel_expiry()
        self._pending_value = None
        self._pending_deadline = None

    def _cancel_expiry(self) -> None:
        """Cancel a scheduled pending-write timeout, if any."""
        if self._expiry_unsub is not None:
            self._expiry_unsub()
            self._expiry_unsub = None

    def _schedule_expiry(self) -> None:
        """Schedule clearing pending state when the timeout elapses."""
        hass = getattr(self, "hass", None)
        if hass is None:
            return

        @callback
        def _expired(_now: datetime) -> None:
            self._expiry_unsub = None
            if not self.pending_active():
                return
            _LOGGER.debug(
                "%s pending write timed out; accepting device value %s",
                getattr(self, "entity_id", "?"),
                self._pending_device_value(),
            )
            self.clear_pending()
            self.async_write_ha_state()  # type: ignore[attr-defined]
            coordinator = getattr(self, "coordinator", None)
            if coordinator is not None:
                hass.async_create_task(
                    coordinator.async_request_refresh(),
                    name=f"{getattr(self, 'entity_id', 'plum_ecovent')} pending refresh",
                )

        self._expiry_unsub = async_call_later(
            hass, PENDING_WRITE_TIMEOUT, _expired
        )

    def effective_value(self, device_value: Any) -> Any:
        """Return pending while active, else the device value."""
        self._reconcile_pending(device_value)
        if self.pending_active():
            return self._pending_value
        return device_value

    def _reconcile_pending(self, device_value: Any) -> None:
        """Clear pending on device confirm or timeout."""
        if not self.pending_active():
            return
        assert self._pending_deadline is not None
        if device_value == self._pending_value:
            self.clear_pending()
            return
        if dt_util.utcnow() >= self._pending_deadline:
            _LOGGER.debug(
                "%s pending write timed out; accepting device value %s",
                getattr(self, "entity_id", "?"),
                device_value,
            )
            self.clear_pending()

    @property
    def assumed_state(self) -> bool:
        """Return True while showing an unconfirmed optimistic value."""
        if self.pending_active():
            self._reconcile_pending(self._pending_device_value())
        return self.pending_active()

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose pending_write markers for Lovelace/debug."""
        if self.pending_active():
            self._reconcile_pending(self._pending_device_value())
        if not self.pending_active():
            return None
        assert self._pending_deadline is not None
        return {
            ATTR_PENDING_WRITE: True,
            ATTR_PENDING_UNTIL: self._pending_deadline.isoformat(),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Combine refresh data with any still-active pending write."""
        if self.pending_active():
            self._reconcile_pending(self._pending_device_value())
        super()._handle_coordinator_update()  # type: ignore[misc]

    async def async_will_remove_from_hass(self) -> None:
        """Cancel pending expiry when the entity is removed."""
        self._cancel_expiry()
        await super().async_will_remove_from_hass()  # type: ignore[misc]
