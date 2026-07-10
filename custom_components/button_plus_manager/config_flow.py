"""Config- und Options-Flow für Button Plus Manager (komplett per GUI)."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BUTTONS,
    CONF_DASHBOARD_TITLE,
    CONF_NUM_BUTTONS,
    CONF_NUM_SWITCHES,
    CONF_SWITCHES,
    DEFAULT_BUTTON_ICON,
    DEFAULT_NUM_BUTTONS,
    DEFAULT_NUM_SWITCHES,
    DEFAULT_SWITCH_ICON,
    DOMAIN,
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
    """Options-Flow: hier werden Tasten/Schalter per GUI Entities zugeordnet.

    Hinweis: self.config_entry wird seit HA 2024.12 automatisch von
    Home Assistant bereitgestellt und darf nicht mehr manuell im
    __init__ gesetzt werden (führt sonst zu einem 500-Fehler).
    """

    async def async_step_init(self, user_input=None):
        data = self.config_entry.data
        options = self.config_entry.options
        num_buttons = data.get(CONF_NUM_BUTTONS, DEFAULT_NUM_BUTTONS)
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

            buttons = []
            for i in range(num_buttons):
                entity_id = user_input.get(f"button_{i}_entity")
                if not entity_id:
                    continue
                buttons.append(
                    {
                        "entity_id": entity_id,
                        "label": user_input.get(f"button_{i}_label") or f"Taste {i + 1}",
                        "icon": user_input.get(f"button_{i}_icon") or DEFAULT_BUTTON_ICON,
                    }
                )

            return self.async_create_entry(
                title="", data={CONF_SWITCHES: switches, CONF_BUTTONS: buttons}
            )

        existing_switches = options.get(CONF_SWITCHES, [])
        existing_buttons = options.get(CONF_BUTTONS, [])

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

        for i in range(num_buttons):
            existing = existing_buttons[i] if i < len(existing_buttons) else {}
            fields[
                vol.Optional(f"button_{i}_entity", default=existing.get("entity_id", ""))
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor", "binary_sensor", "event"])
            )
            fields[
                vol.Optional(f"button_{i}_label", default=existing.get("label", f"Taste {i + 1}"))
            ] = str
            fields[
                vol.Optional(f"button_{i}_icon", default=existing.get("icon", DEFAULT_BUTTON_ICON))
            ] = selector.IconSelector()

        return self.async_show_form(step_id="init", data_schema=vol.Schema(fields))
