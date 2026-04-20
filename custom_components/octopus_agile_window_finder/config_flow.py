import voluptuous as vol
from homeassistant import config_entries
from .const import *

class OctopusFinderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            # Uses the device name (e.g. "Dishwasher") as the title in Integrations list
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default="Dishwasher"): str,
                vol.Required(CONF_CURRENT_ENTITY): str,
                vol.Required(CONF_FUTURE_ENTITY): str,
                vol.Required(CONF_RUN_HOURS, default=2.5): float,
                vol.Required(CONF_TOTAL_KWH, default=5.0): float,
                vol.Optional(CONF_MIN_START): str,
                vol.Optional(CONF_MAX_END): str,
                vol.Required(CONF_ENABLE_BINARY, default=True): bool,
            })
        )
