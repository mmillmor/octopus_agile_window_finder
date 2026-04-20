import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import *

class OctopusAgileWindowFinderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default="Dishwasher"): str,
                vol.Required(CONF_CURRENT_ENTITY): selector.EntitySelector({"domain": "event"}),
                vol.Required(CONF_FUTURE_ENTITY): selector.EntitySelector({"domain": "event"}),
                vol.Required(CONF_RUN_HOURS, default=2.5): vol.Coerce(float),
                vol.Required(CONF_TOTAL_KWH, default=1.0): vol.Coerce(float),
                vol.Optional(CONF_MIN_START): selector.TimeSelector({}),
                vol.Optional(CONF_MAX_END): selector.TimeSelector({}),
                vol.Required(CONF_ENABLE_BINARY, default=True): bool,
            })
        )
