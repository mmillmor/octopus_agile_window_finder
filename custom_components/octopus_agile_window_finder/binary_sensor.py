from __future__ import annotations

import homeassistant.util.dt as dt_util
from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import CONF_ENABLE_BINARY, CONF_NAME, DOMAIN
from .coordinator import WindowFinderCoordinator


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator: WindowFinderCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    if coordinator.conf.get(CONF_ENABLE_BINARY):
        async_add_entities([OctopusWindowActiveSensor(coordinator)])


class OctopusWindowActiveSensor(BinarySensorEntity):
    """On while the current time is inside a planned slot."""

    _attr_should_poll = False
    _attr_icon = "mdi:power"

    def __init__(self, coordinator: WindowFinderCoordinator) -> None:
        self.coordinator = coordinator
        entry = coordinator.entry
        self._attr_name = f"{entry.data[CONF_NAME]} Window Active"
        self._attr_unique_id = f"{entry.entry_id}_active"

    async def async_added_to_hass(self) -> None:
        # The coordinator refreshes at every half-hour boundary, so this
        # switches on and off within a few seconds of each slot changing.
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    @property
    def is_on(self) -> bool:
        return self.coordinator.plan.is_active(dt_util.now())

    @property
    def extra_state_attributes(self) -> dict:
        block = self.coordinator.plan.current_or_next_block(dt_util.now())
        if not block:
            return {}
        return {"block_start": block[0].isoformat(), "block_end": block[1].isoformat()}
