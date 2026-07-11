"""Config- und Options-Flow für Button Plus Manager (komplett per GUI)."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    BUTTON_EVENT_TYPES,
    CONF_ACTION,
    CONF_BUTTONS,
    CONF_DASHBOARD_TITLE,
    CONF_DEVICE_ID,
    CONF_DISPLAY_ITEM_INDEX,
    CONF_DISPLAY_ROWS,
    CONF_EVENT_TYPE,
    CONF_NUM_BUTTONS,
    CONF_NUM_SWITCHES,
    CONF_PAGE,
    CONF_POSITION,
    CONF_SWITCHES,
    DEFAULT_BUTTON_ICON,
    DEFAULT_NUM_BUTTONS,
    DEFAULT_NUM_SWITCHES,
    DEFAULT_PAGE,
    DEFAULT_SWITCH_ICON,
    DOMAIN,
    NUM_DISPLAY_ROWS,
)


class ButtonPlusManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Erster Einrichtungsschritt: Name, Geräte-ID + Anzahl Tasten/Schalter."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_DASHBOARD_TITLE], data=user_input
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_DASHBOARD_TITLE, default="Button Plus"): str,
                vol.Required(CONF_DEVICE_ID, default="btn_03a45c"): str,
                vol.Required(CONF_NUM_BUTTONS, default=DEFAULT_NUM_BUTTONS): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=12)
                ),
                vol.Required(CONF_NUM_SWITCHES, default=DEFAULT_NUM_SWITCHES): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=12)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ButtonPlusManagerOptionsFlow()


class ButtonPlusManagerOptionsFlow(config_entries.OptionsFlow):
    """Options-Flow mit Menü: Schalter / Tasten & Aktionen / Display.

    Hinweis: self.config_entry wird seit HA 2024.12 automatisch von
    Home Assistant bereitgestellt und darf nicht mehr manuell im
    __init__ gesetzt werden (führt sonst zu einem 500-Fehler).
    """

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(
            step_id="init",
            menu_options=["switches", "buttons", "display"],
        )

    # ------------------------------------------------------------------
    # Schalter (Relais) - bleiben normale HA switch-Entities
    # ------------------------------------------------------------------
    async def async_step_switches(self, user_input=None):
        data = self.config_entry.data
        options = self.config_entry.options
        num_switches = data.get(CONF_NUM_SWITCHES, DEFAULT_NUM_SWITCHES)

        if user_input is not None:
            switches = []
            for i in range(num_switches):
                entity_id = user_input.get(f"switch_{i}_entity")
                if not entity_id:
                    continue
                switches.append(
                    {
                        "entity_id": entity_id,
                        "label": user_input.get(f"switch_{i}_label") or f"Relais {i + 1}",
                        "icon": user_input.get(f"switch_{i}_icon") or DEFAULT_SWITCH_ICON,
                    }
                )
            new_options = dict(options)
            new_options[CONF_SWITCHES] = switches
            return self.async_create_entry(title="", data=new_options)

        existing_switches = options.get(CONF_SWITCHES, [])
        fields: dict = {}
        for i in range(num_switches):
            existing = existing_switches[i] if i < len(existing_switches) else {}
            fields[
                vol.Optional(f"switch_{i}_entity", default=existing.get("entity_id", ""))
            ] = selector.EntitySelector(selector.EntitySelectorConfig(domain="switch"))
            fields[
                vol.Optional(f"switch_{i}_label", default=existing.get("label", f"Relais {i + 1}"))
            ] = str
            fields[
                vol.Optional(f"switch_{i}_icon", default=existing.get("icon", DEFAULT_SWITCH_ICON))
            ] = selector.IconSelector()

        return self.async_show_form(step_id="switches", data_schema=vol.Schema(fields))

    # ------------------------------------------------------------------
    # Tasten: Position/Seite/Event (direkt vom physischen Button-MQTT-Topic)
    # + Aktion, die beim Drücken ausgeführt wird
    # ------------------------------------------------------------------
    async def async_step_buttons(self, user_input=None):
        data = self.config_entry.data
        options = self.config_entry.options
        num_buttons = data.get(CONF_NUM_BUTTONS, DEFAULT_NUM_BUTTONS)

        if user_input is not None:
            buttons = []
            for i in range(num_buttons):
                position = user_input.get(f"button_{i}_position")
                if not position:
                    continue
                buttons.append(
                    {
                        CONF_POSITION: int(position),
                        CONF_PAGE: int(user_input.get(f"button_{i}_page") or DEFAULT_PAGE),
                        CONF_EVENT_TYPE: user_input.get(f"button_{i}_event") or "click",
                        "label": user_input.get(f"button_{i}_label") or f"Taste {i + 1}",
                        "icon": user_input.get(f"button_{i}_icon") or DEFAULT_BUTTON_ICON,
                        CONF_ACTION: user_input.get(f"button_{i}_action") or {},
                    }
                )
            new_options = dict(options)
            new_options[CONF_BUTTONS] = buttons
            return self.async_create_entry(title="", data=new_options)

        existing_buttons = options.get(CONF_BUTTONS, [])
        fields: dict = {}
        for i in range(num_buttons):
            existing = existing_buttons[i] if i < len(existing_buttons) else {}
            fields[
                vol.Optional(
                    f"button_{i}_position", default=existing.get(CONF_POSITION, i + 1)
                )
            ] = vol.All(vol.Coerce(int), vol.Range(min=1, max=8))
            fields[
                vol.Optional(f"button_{i}_page", default=existing.get(CONF_PAGE, DEFAULT_PAGE))
            ] = vol.All(vol.Coerce(int), vol.Range(min=0, max=10))
            fields[
                vol.Optional(
                    f"button_{i}_event", default=existing.get(CONF_EVENT_TYPE, "click")
                )
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=BUTTON_EVENT_TYPES, mode="dropdown")
            )
            fields[
                vol.Optional(f"button_{i}_label", default=existing.get("label", f"Taste {i + 1}"))
            ] = str
            fields[
                vol.Optional(f"button_{i}_icon", default=existing.get("icon", DEFAULT_BUTTON_ICON))
            ] = selector.IconSelector()
            fields[
                vol.Optional(
                    f"button_{i}_action", default=existing.get(CONF_ACTION, {})
                )
            ] = selector.ActionSelector()

        return self.async_show_form(step_id="buttons", data_schema=vol.Schema(fields))

    # ------------------------------------------------------------------
    # Display-Zeilen: Item-Index (buttonplus/<id>/displayitem/<index>/...)
    # ------------------------------------------------------------------
    async def async_step_display(self, user_input=None):
        options = self.config_entry.options

        if user_input is not None:
            rows = []
            for i in range(NUM_DISPLAY_ROWS):
                rows.append(
                    {
                        CONF_DISPLAY_ITEM_INDEX: int(
                            user_input.get(f"row_{i}_index", i)
                        ),
                        "label": user_input.get(f"row_{i}_label") or f"Zeile {i + 1}",
                        "entity_id": user_input.get(f"row_{i}_entity"),
                        "template": user_input.get(f"row_{i}_template") or "",
                    }
                )
            new_options = dict(options)
            new_options[CONF_DISPLAY_ROWS] = rows
            return self.async_create_entry(title="", data=new_options)

        existing_rows = options.get(CONF_DISPLAY_ROWS, [])
        fields: dict = {}
        for i in range(NUM_DISPLAY_ROWS):
            existing = existing_rows[i] if i < len(existing_rows) else {}
            fields[
                vol.Optional(
                    f"row_{i}_index", default=existing.get(CONF_DISPLAY_ITEM_INDEX, i)
                )
            ] = vol.All(vol.Coerce(int), vol.Range(min=0, max=20))
            fields[
                vol.Optional(f"row_{i}_label", default=existing.get("label", f"Zeile {i + 1}"))
            ] = str
            fields[
                vol.Optional(f"row_{i}_entity", default=existing.get("entity_id", ""))
            ] = selector.EntitySelector(selector.EntitySelectorConfig())
            fields[
                vol.Optional(f"row_{i}_template", default=existing.get("template", ""))
            ] = selector.TemplateSelector()

        return self.async_show_form(step_id="display", data_schema=vol.Schema(fields))
