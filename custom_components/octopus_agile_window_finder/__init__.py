from .const import DOMAIN

async def async_setup_entry(hass, entry):
    # Load both platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True

async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_forward_entry_unload(entry, ["sensor", "binary_sensor"])
