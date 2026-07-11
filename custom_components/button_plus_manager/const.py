"""Konstanten für Button Plus Manager."""

DOMAIN = "button_plus_manager"

CONF_DASHBOARD_TITLE = "dashboard_title"
CONF_NUM_BUTTONS = "num_buttons"
CONF_NUM_SWITCHES = "num_switches"
CONF_BUTTONS = "buttons"
CONF_SWITCHES = "switches"
CONF_DISPLAY_ROWS = "display_rows"
CONF_ACTION = "action"
CONF_EVENT_TYPE = "event_type"

DEFAULT_NUM_BUTTONS = 6
DEFAULT_NUM_SWITCHES = 4
NUM_DISPLAY_ROWS = 3

# Event-Typen, die die "event."-Entität deines Button Plus als Attribut
# "event_type" liefert, wenn eine Taste gedrückt wird.
BUTTON_EVENT_TYPES = ["click", "shortpress", "longpress", "release"]

DEFAULT_BUTTON_ICON = "mdi:gesture-tap-button"
DEFAULT_SWITCH_ICON = "mdi:toggle-switch"

SERVICE_REGENERATE = "regenerate_dashboard"

DASHBOARD_SUBDIR = "dashboards"
