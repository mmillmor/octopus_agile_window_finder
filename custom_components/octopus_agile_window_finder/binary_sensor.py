from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.util import slugify
import homeassistant.util.dt as dt_util
from datetime import timedelta
from .const import DOMAIN, CONF_RUN_HOURS, CONF_NAME

SCAN_INTERVAL = timedelta(hours=24) 

async def async_setup_entry(hass, config_entry, async_add_entities):
    if config_entry.data.get("enable_binary"):
        async_add_entities([OctopusWindowActiveSensor(hass, config_entry)], True)

class OctopusWindowActiveSensor(BinarySensorEntity):
    def __init__(self, hass, config_entry):
        self._hass = hass
        self._config_entry = config_entry  
        self._name = config_entry.data[CONF_NAME]
        self._attr_name = f"{self._name} Window Active"
        self._attr_unique_id = f"{config_entry.entry_id}_active"

    @property
    def icon(self):
        return "mdi:power"

    @property
    def is_on(self):
        # Find the matching sensor (e.g. sensor.dishwasher_best_window)
        entity_id = f"sensor.{slugify(self._name)}_best_window"
        state = self._hass.states.get(entity_id)
        
        if not state or "start_time" not in state.attributes:
            return False

        start_dt = dt_util.parse_datetime(state.attributes["start_time"])
        duration = timedelta(hours=self._config_entry.data[CONF_RUN_HOURS])
        now = dt_util.now()

        return start_dt <= now <= (start_dt + duration)
