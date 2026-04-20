from datetime import datetime, time, timedelta
import math
import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import SensorEntity
from .const import *
import logging

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(hours=24) 

async def async_setup_entry(hass, config_entry, async_add_entities):
    sensor = OctopusBestWindowSensor(hass, config_entry)
    
    # Initialize the data storage for this entry
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = [sensor]
    
    async_add_entities([sensor], True)

def parse_time(time_str):
    try:
        return time.fromisoformat(time_str)
    except (ValueError, TypeError):
        return None

def is_in_time_window(check_time, min_t, max_t):
    if min_t is None or max_t is None:
        return True

    # Standard window (e.g., 09:00 to 17:00)
    if min_t <= max_t:
        return min_t <= check_time <= max_t
    
    # Midnight spanning window (e.g., 22:00 to 05:00)
    return check_time >= min_t or check_time <= max_t


class OctopusBestWindowSensor(SensorEntity):
    def __init__(self, hass, config_entry):
        self._hass = hass
        self._config_entry = config_entry 
        self._name = config_entry.data[CONF_NAME]
        # This creates "sensor.dishwasher_best_window"
        self._attr_name = f"{self._name} Best Window"
        self._attr_unique_id = f"{config_entry.entry_id}_window"
        self._state = None
        self._attributes = {}

    @property
    def state(self): return self._state

    @property
    def extra_state_attributes(self): return self._attributes

    @property
    def icon(self):
        return "mdi:clock-outline"

    def update(self):

        conf = {**self._config_entry.data, **self._config_entry.options}
        
        current_entity = conf.get(CONF_CURRENT_ENTITY)
        future_entity = conf.get(CONF_FUTURE_ENTITY)
        run_hours = conf.get(CONF_RUN_HOURS)
        total_kwh = conf.get(CONF_TOTAL_KWH)

        _LOGGER.debug("Starting update for %s", self._name)
        current_state = self._hass.states.get(current_entity)
        _LOGGER.debug("Current state fetched: %s", current_state)
        future_state = self._hass.states.get(future_entity)
        
        current_rates = []
        if current_state and current_state.attributes.get("rates"):
            current_rates = current_state.attributes.get("rates")
            _LOGGER.debug("Found %s rate slots", len(current_rates))
            # Log the first rate to see the structure
            _LOGGER.debug("First rate entry: %s", current_rates[0])
        else:
            _LOGGER.warning("No rates found in current_state for %s", self._name)

        future_rates = []
        if future_state and future_state.attributes.get("rates"):
            future_rates = future_state.attributes.get("rates")

        all_rates = current_rates + future_rates

        slots_needed = math.ceil(run_hours * 2)
        if len(all_rates) < slots_needed:
            _LOGGER.debug("Not enough rates available: %s needed, %s available", slots_needed, len(all_rates))
            self._state = "Waiting for rates"
            return

        now = dt_util.now()
        best_sum, best_start = float('inf'), None

        min_val = conf.get(CONF_MIN_START)
        max_val = conf.get(CONF_MAX_END)

        min_t = time.fromisoformat(min_val) if min_val else None
        max_t = time.fromisoformat(max_val) if max_val else None


        for i in range(len(all_rates) - slots_needed + 1):
            window = all_rates[i : i + slots_needed]
            
            raw_start = window[0].get("start")

            if isinstance(raw_start, datetime):
                start_dt = raw_start
            elif isinstance(raw_start, str):
                start_dt = dt_util.parse_datetime(raw_start)
            else:
                continue

            if start_dt is None:
                continue

            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)

            # 1. Future only
            if start_dt <= now:
                continue
                
            if not is_in_time_window(start_dt.time(), min_t, max_t):
                continue

            try:
                current_sum = sum(slot.get("value_inc_vat", 999) for slot in window)
            except (TypeError, ValueError):
                continue

            if current_sum < best_sum:
                best_sum = current_sum
                best_start = start_dt

        if best_start:
            self._state = best_start.strftime("%I:%M %p").lower()
            # Calculate run cost
            total_cost = (best_sum / slots_needed) * total_kwh
            self._attributes = {
                "start_time": best_start.isoformat(),
                "estimated_cost_pence": round(total_cost * 100, 2),
            }
