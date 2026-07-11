"""Konstanten für Button Plus Manager."""

DOMAIN = "button_plus_manager"

CONF_DASHBOARD_TITLE = "dashboard_title"
CONF_DEVICE_ID = "device_id"  # z.B. "btn_03a45c" -> buttonplus/btn_03a45c/...
CONF_NUM_BUTTONS = "num_buttons"
CONF_NUM_SWITCHES = "num_switches"
CONF_BUTTONS = "buttons"
CONF_SWITCHES = "switches"
CONF_DISPLAY_ROWS = "display_rows"
CONF_ACTION = "action"

CONF_POSITION = "position"
CONF_PAGE = "page"
CONF_EVENT_TYPE = "event_type"
CONF_DISPLAY_ITEM_INDEX = "display_item_index"

DEFAULT_NUM_BUTTONS = 6
DEFAULT_NUM_SWITCHES = 4
NUM_DISPLAY_ROWS = 3
DEFAULT_PAGE = 1

# Event-Typen, die das Button Plus Modul beim Drücken per MQTT sendet
BUTTON_EVENT_TYPES = ["click", "shortpress", "longpress", "release"]

DEFAULT_BUTTON_ICON = "mdi:gesture-tap-button"
DEFAULT_SWITCH_ICON = "mdi:toggle-switch"

SERVICE_REGENERATE = "regenerate_dashboard"

DASHBOARD_SUBDIR = "dashboards"

# Topic-Schema des Button Plus Moduls (siehe Geräte-Konfigurationsoberfläche)
TOPIC_BUTTON_EVENT = "buttonplus/{device_id}/button/{position}-{page}/pushbutton"
TOPIC_DISPLAY_VALUE_SET = "buttonplus/{device_id}/displayitem/{index}/value/set"
TOPIC_DISPLAY_LABEL_SET = "buttonplus/{device_id}/displayitem/{index}/label/set"
