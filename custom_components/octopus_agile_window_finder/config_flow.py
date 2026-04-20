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

        def get_val(key):
            return self.config_entry.options.get(key, self.config_entry.data.get(key))

        # Build optional time fields only if a value exists — passing None as a
        # default to TimeSelector causes a 400 when the form loads.
        schema_dict = {
            vol.Required(
                CONF_RUN_HOURS,
                default=get_val(CONF_RUN_HOURS)
            ): vol.Coerce(float),
            vol.Required(
                CONF_TOTAL_KWH,
                default=get_val(CONF_TOTAL_KWH)
            ): vol.Coerce(float),
        }

        min_start = get_val(CONF_MIN_START)
        max_end = get_val(CONF_MAX_END)

        if min_start is not None:
            schema_dict[vol.Optional(CONF_MIN_START, default=min_start)] = selector.TimeSelector({})
        else:
            schema_dict[vol.Optional(CONF_MIN_START)] = selector.TimeSelector({})

        if max_end is not None:
            schema_dict[vol.Optional(CONF_MAX_END, default=max_end)] = selector.TimeSelector({})
        else:
            schema_dict[vol.Optional(CONF_MAX_END)] = selector.TimeSelector({})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict)
        )
