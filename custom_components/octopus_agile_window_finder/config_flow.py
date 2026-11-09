from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CURRENT_ENTITY,
    CONF_ENABLE_BINARY,
    CONF_FUTURE_ENTITY,
    CONF_MAX_END,
    CONF_MIN_BLOCK_HOURS,
    CONF_MIN_START,
    CONF_MODE,
    CONF_NAME,
    CONF_RUN_HOURS,
    CONF_TOTAL_KWH,
    DEFAULT_MODE,
    DOMAIN,
    MODE_SLOTS,
    MODE_WINDOW,
)
from .coordinator import merged_config

HOURS_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=0.5, max=24, step=0.5, unit_of_measurement="h",
        mode=selector.NumberSelectorMode.BOX,
    )
)
KWH_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=0, max=500, step=0.1, unit_of_measurement="kWh",
        mode=selector.NumberSelectorMode.BOX,
    )
)
MODE_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=[MODE_WINDOW, MODE_SLOTS],
        translation_key="mode",
        mode=selector.SelectSelectorMode.LIST,
    )
)
EVENT_SELECTOR = selector.EntitySelector(selector.EntitySelectorConfig(domain="event"))
TIME_SELECTOR = selector.TimeSelector()


def _schema(values: dict, include_name: bool) -> vol.Schema:
    """Form schema. Optional fields use suggested values so they can be cleared."""

    def suggested(key):
        val = values.get(key)
        return {"suggested_value": val} if val not in (None, "") else None

    fields: dict = {}
    if include_name:
        fields[vol.Required(CONF_NAME, default=values.get(CONF_NAME, "Dishwasher"))] = str
    fields.update(
        {
            vol.Required(
                CONF_CURRENT_ENTITY, description=suggested(CONF_CURRENT_ENTITY)
            ): EVENT_SELECTOR,
            vol.Required(
                CONF_FUTURE_ENTITY, description=suggested(CONF_FUTURE_ENTITY)
            ): EVENT_SELECTOR,
            vol.Required(CONF_MODE, default=values.get(CONF_MODE, DEFAULT_MODE)): MODE_SELECTOR,
            vol.Required(CONF_RUN_HOURS, default=values.get(CONF_RUN_HOURS, 2.5)): HOURS_SELECTOR,
            vol.Optional(
                CONF_MIN_BLOCK_HOURS, description=suggested(CONF_MIN_BLOCK_HOURS)
            ): HOURS_SELECTOR,
            vol.Required(CONF_TOTAL_KWH, default=values.get(CONF_TOTAL_KWH, 1.0)): KWH_SELECTOR,
            vol.Optional(CONF_MIN_START, description=suggested(CONF_MIN_START)): TIME_SELECTOR,
            vol.Optional(CONF_MAX_END, description=suggested(CONF_MAX_END)): TIME_SELECTOR,
            vol.Required(
                CONF_ENABLE_BINARY, default=values.get(CONF_ENABLE_BINARY, True)
            ): selector.BooleanSelector(),
        }
    )
    return vol.Schema(fields)


def _validate(user_input: dict) -> dict:
    errors = {}
    block = user_input.get(CONF_MIN_BLOCK_HOURS)
    if block and float(block) > float(user_input[CONF_RUN_HOURS]):
        errors[CONF_MIN_BLOCK_HOURS] = "min_block_too_long"
    return errors


class OctopusAgileWindowFinderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Add an appliance."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input or {}, include_name=True),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OctopusOptionsFlowHandler()


class OctopusOptionsFlowHandler(config_entries.OptionsFlow):
    """Change an appliance's settings (Configure button)."""

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        values = user_input or merged_config(self.config_entry)
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(values, include_name=False),
            errors=errors,
        )
