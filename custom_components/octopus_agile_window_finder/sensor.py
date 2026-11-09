from __future__ import annotations

import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import SensorEntity

from .const import (
    CONF_MODE,
    CONF_NAME,
    DEFAULT_MODE,
    DOMAIN,
    STATUS_NO_WINDOW,
    STATUS_WAITING,
)
from .coordinator import WindowFinderCoordinator


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator: WindowFinderCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([OctopusBestWindowSensor(coordinator)])


class OctopusBestWindowSensor(SensorEntity):
    """Start time of the current or next planned run."""

    _attr_should_poll = False
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator: WindowFinderCoordinator) -> None:
        self.coordinator = coordinator
        entry = coordinator.entry
        self._attr_name = f"{entry.data[CONF_NAME]} Best Window"
        self._attr_unique_id = f"{entry.entry_id}_window"

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    @property
    def native_value(self) -> str:
        plan = self.coordinator.plan
        block = plan.current_or_next_block(dt_util.now())
        if block:
            return dt_util.as_local(block[0]).strftime("%I:%M %p").lower()
        if plan.status == "no_window":
            return STATUS_NO_WINDOW
        return STATUS_WAITING

    @property
    def extra_state_attributes(self) -> dict:
        coordinator = self.coordinator
        plan = coordinator.plan
        now = dt_util.now()
        block = plan.current_or_next_block(now)
        attrs = {
            "mode": coordinator.conf.get(CONF_MODE, DEFAULT_MODE),
            "status": plan.status,
            "blocks": [
                {"start": s.isoformat(), "end": e.isoformat()} for s, e in plan.blocks()
            ],
            "planned_hours": len(plan.slots) / 2,
        }
        if block:
            # start_time kept for compatibility with existing automations.
            attrs["start_time"] = block[0].isoformat()
            attrs["end_time"] = block[1].isoformat()
        if plan.slots:
            cost = sum(s.price for s in plan.slots) * coordinator.slot_kwh
            attrs["estimated_cost_pence"] = round(cost * 100, 2)
            attrs["average_rate_pence"] = round(
                sum(s.price for s in plan.slots) / len(plan.slots) * 100, 2
            )
        if plan.period_start and plan.period_end:
            attrs["period_start"] = plan.period_start.isoformat()
            attrs["period_end"] = plan.period_end.isoformat()
        if coordinator.last_calculated:
            attrs["last_calculated"] = coordinator.last_calculated.isoformat()
        return attrs
