import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_CURRENT_ENTITY,
    CONF_FUTURE_ENTITY,
    CONF_RUN_HOURS,
    CONF_TOTAL_KWH,
    CONF_MIN_START,
    CONF_MAX_END,
    CONF_ENABLE_BINARY,
)

class OctopusAgileWindowFinderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Octopus Agile Window Finder."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup when adding the integration."""
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Handle the edit/configuration flow."""
        return OctopusOptionsFlowHandler()


class OctopusOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle the options flow (Configure button)."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # We pull current values from both .options (previously edited) 
        # and .data (original setup) to pre-fill the form correctly.
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_RUN_HOURS, 
                    default=self.config_entry.options.get(
                        CONF_RUN_HOURS, self.config_entry.data.get(CONF_RUN_HOURS)
                    )
                ): vol.Coerce(float),
                vol.Required(
                    CONF_TOTAL_KWH, 
                    default=self.config_entry.options.get(
                        CONF_TOTAL_KWH, self.config_entry.data.get(CONF_TOTAL_KWH)
                    )
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_MIN_START, 
                    default=self.config_entry.options.get(
                        CONF_MIN_START, self.config_entry.data.get(CONF_MIN_START)
                    )
                ): selector.TimeSelector({"nullable": True}),
                vol.Optional(
                    CONF_MAX_END, 
                    default=self.config_entry.options.get(
                        CONF_MAX_END, self.config_entry.data.get(CONF_MAX_END)
                    )
                ): selector.TimeSelector({"nullable": True}),
            })
        )
