from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.event import async_track_utc_time_change, async_track_time_change
import homeassistant.util.dt as dt_util
from .const import DOMAIN

async def async_setup_entry(hass, entry):
    """Set up the integration."""

    async def force_update(now):
        """Force all entities associated with this entry to update."""
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            for entity in hass.data[DOMAIN][entry.entry_id]:
                await entity.async_update_ha_state(force_refresh=True)

    # 1. Schedule for 00 and 30 minutes past every hour
    async_track_utc_time_change(hass, force_update, minute=[0, 30], second=10)

    # 2. Schedule for exactly 16:01 (4:01 PM) local time every day
    # We use local time change helper here
    async_track_time_change(hass, force_update, hour=16, minute=1, second=0)

    async def handle_manual_update(call: ServiceCall):
        """Service handler to force an update on all instances."""
        for entry_id in hass.data.get(DOMAIN, {}):
            for entity in hass.data[DOMAIN][entry_id]:
                await entity.async_update_ha_state(force_refresh=True)

    # Register the service
    hass.services.async_register(DOMAIN, "update_windows", handle_manual_update)

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, ["sensor", "binary_sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
