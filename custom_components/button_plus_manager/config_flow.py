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
    CONF_DISPLAY_ROWS,
    CONF_EVENT_TYPE,
    CONF_NUM_BUTTONS,
    CONF_NUM_SWITCHES,
    CONF_SWITCHES,
    DEFAULT_BUTTON_ICON,
    DEFAULT_NUM_BUTTONS,
    DEFAULT_NUM_SWITCHES,
    DEFAULT_SWITCH_ICON,
    DOMAIN,
    NUM_DISPLAY_ROWS,
)


class ButtonPlusManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Erster Einrichtungsschritt: Name + Anzahl Tasten/Schalter."""

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
    # Schalter (Relais)
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
    # Tasten: die vom Gerät per MQTT-Discovery erzeugte event.-Entität
    # auswählen + Event-Typ + Aktion, die dabei ausgeführt wird
    # ------------------------------------------------------------------
    async def async_step_buttons(self, user_input=None):
        data = self.config_entry.data
        options = self.config_entry.options
        num_buttons = data.get(CONF_NUM_BUTTONS, DEFAULT_NUM_BUTTONS)

        if user_input is not None:
            buttons = []
            for i in range(num_buttons):
                entity_id = user_input.get(f"button_{i}_entity")
                if not entity_id:
                    continue
                buttons.append(
                    {
                        "entity_id": entity_id,
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
                vol.Optional(f"button_{i}_entity", default=existing.get("entity_id", ""))
            ] = selector.EntitySelector(selector.EntitySelectorConfig(domain="event"))
            fields[
                vol.Optional(
                    f"button_{i}_event", default=existing.get(CONF_EVENT_TYPE, "click")
                )
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=BUTTON_EVENT_TYPES, mode="dropdown", custom_value=True
                )
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
    # Display-Zeilen: Ziel-Text-Entität (z.B. text.btn_..._displayitem_0_value)
    # + Quell-Entität, deren Zustand dort automatisch hineingeschrieben wird
    # ------------------------------------------------------------------
    async def async_step_display(self, user_input=None):
        options = self.config_entry.options

        if user_input is not None:
            rows = []
            for i in range(NUM_DISPLAY_ROWS):
                target_entity = user_input.get(f"row_{i}_target")
                if not target_entity:
                    continue
                rows.append(
                    {
                        "target_entity_id": target_entity,
                        "source_entity_id": user_input.get(f"row_{i}_source"),
                        "template": user_input.get(f"row_{i}_template") or "",
                        "label_target_entity_id": user_input.get(f"row_{i}_label_target") or "",
                        "label_text": user_input.get(f"row_{i}_label_text") or "",
                        "unit_target_entity_id": user_input.get(f"row_{i}_unit_target") or "",
                        "unit_text": user_input.get(f"row_{i}_unit_text") or "",
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
                vol.Optional(f"row_{i}_target", default=existing.get("target_entity_id", ""))
            ] = selector.EntitySelector(selector.EntitySelectorConfig(domain="text"))
            fields[
                vol.Optional(f"row_{i}_source", default=existing.get("source_entity_id", ""))
            ] = selector.EntitySelector(selector.EntitySelectorConfig())
            fields[
                vol.Optional(f"row_{i}_template", default=existing.get("template", ""))
            ] = selector.TemplateSelector()
            fields[
                vol.Optional(
                    f"row_{i}_label_target", default=existing.get("label_target_entity_id", "")
                )
            ] = selector.EntitySelector(selector.EntitySelectorConfig(domain="text"))
            fields[
                vol.Optional(f"row_{i}_label_text", default=existing.get("label_text", ""))
            ] = str
            fields[
                vol.Optional(
                    f"row_{i}_unit_target", default=existing.get("unit_target_entity_id", "")
                )
            ] = selector.EntitySelector(selector.EntitySelectorConfig(domain="text"))
            fields[
                vol.Optional(f"row_{i}_unit_text", default=existing.get("unit_text", ""))
            ] = str

        return self.async_show_form(step_id="display", data_schema=vol.Schema(fields))
