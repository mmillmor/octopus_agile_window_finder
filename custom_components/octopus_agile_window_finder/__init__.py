from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, PLATFORMS
from .coordinator import WindowFinderCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one appliance."""
    coordinator = WindowFinderCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await coordinator.async_setup()
    entry.async_on_unload(coordinator.async_shutdown)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    if not hass.services.has_service(DOMAIN, "update_windows"):

        async def handle_manual_update(call: ServiceCall) -> None:
            """Recalculate every appliance's plan now."""
            for coord in list(hass.data.get(DOMAIN, {}).values()):
                await coord.async_refresh()

        hass.services.async_register(DOMAIN, "update_windows", handle_manual_update)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload so new settings (and the optional binary sensor) take effect."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "update_windows")
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Delete the stored plan when the appliance is removed."""
    await WindowFinderCoordinator(hass, entry).async_remove_store()
