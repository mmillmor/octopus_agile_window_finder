DOMAIN = "octopus_agile_window_finder"
PLATFORMS = ["sensor", "binary_sensor"]

CONF_NAME = "name"
CONF_CURRENT_ENTITY = "current_entity"
CONF_FUTURE_ENTITY = "future_entity"
CONF_MODE = "mode"
CONF_RUN_HOURS = "run_hours"
CONF_MIN_BLOCK_HOURS = "min_block_hours"
CONF_TOTAL_KWH = "total_kwh"
CONF_MIN_START = "min_start"
CONF_MAX_END = "max_end"
CONF_ENABLE_BINARY = "enable_binary"

MODE_WINDOW = "window"
MODE_SLOTS = "slots"
DEFAULT_MODE = MODE_WINDOW

# Keys the options flow can clear; if options exist, a missing key means "unset".
OPTIONAL_KEYS = (CONF_MIN_START, CONF_MAX_END, CONF_MIN_BLOCK_HOURS)

STATUS_WAITING = "Waiting for rates"
STATUS_NO_WINDOW = "No window found"
