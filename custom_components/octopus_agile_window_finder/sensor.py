from datetime import datetime, time
import math
import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import SensorEntity
from .const import *

async def async_setup_entry(hass, config_entry, async_add_entities):
    async_add_entities([OctopusBestWindowSensor(hass, config_entry)], True)

class OctopusBestWindowSensor(SensorEntity):
    def __init__(self, hass, config_entry):
        self._hass = hass
        self._config = config_entry.data
        self._name = self._config[CONF_NAME]
        # This creates "sensor.dishwasher_best_window"
        self._attr_name = f"{self._name} Best Window"
        self._attr_unique_id = f"{config_entry.entry_id}_window"
        self._state = None
        self._attributes = {}

    @property
    def state(self): return self._state

    @property
    def extra_state_attributes(self): return self._attributes

    def update(self):
        # Fetching logic remains the same
        current_state = self._hass.states.get(self._config[CONF_CURRENT_ENTITY])
        future_state = self._hass.states.get(self._config[CONF_FUTURE_ENTITY])
        
        current_rates = current_state.attributes.get("rates", []) if current_state else []
        future_rates = future_state.attributes.get("rates", []) if future_state else []
        all_rates = current_rates + future_rates

        slots_needed = math.ceil(self._config[CONF_RUN_HOURS] * 2)
        now = dt_util.now()
        
        best_sum = float('inf')
        best_start = None

        min_t = time.fromisoformat(self._config[CONF_MIN_START]) if self._config.get(CONF_MIN_START) else None
        max_t = time.fromisoformat(self._config[CONF_MAX_END]) if self._config.get(CONF_MAX_END) else None

        for i in range(len(all_rates) - slots_needed + 1):
            window = all_rates[i : i + slots_needed]
            start_dt = dt_util.parse_datetime(window[0]["start"])
            end_dt = dt_util.parse_datetime(window[-1]["end"])

            if start_dt <= now: continue
            if min_t and start_dt.time() < min_t: continue
            if max_t and end_dt.time() > max_t: continue

            current_sum = sum(slot["value_inc_vat"] for slot in window)
            if current_sum < best_sum:
                best_sum = current_sum
                best_start = start_dt

        if best_start:
            self._state = best_start.strftime("%I:%M %p").lower()
            total_cost = (best_sum / slots_needed) * self._config[CONF_TOTAL_KWH]
            self._attributes = {
                "start_time": best_start.isoformat(),
                "estimated_cost_pence": round(total_cost * 100, 2),
                "slots_used": slots_needed
            }
