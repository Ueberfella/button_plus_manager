"""Button Plus Manager – reagiert auf die event.-Entitäten deiner Tasten,
löst konfigurierte Aktionen aus, schreibt Infos in die Display-Text-Entities
und baut automatisch ein Lovelace-Dashboard."""
from __future__ import annotations

import logging

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import template as template_helper
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.service import async_call_from_config

from .const import CONF_ACTION, CONF_BUTTONS, CONF_DISPLAY_ROWS, CONF_EVENT_TYPE, DOMAIN, SERVICE_REGENERATE
from .dashboard import async_regenerate_dashboard, lovelace_yaml_snippet

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = []  # diese Integration erzeugt keine eigenen Entities


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"unsubscribers": []}

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    file_path = await async_regenerate_dashboard(hass, entry)
    _notify_setup_info(hass, entry, file_path)

    _setup_button_listeners(hass, entry)
    await _setup_display_listeners(hass, entry)

    if not hass.services.has_service(DOMAIN, SERVICE_REGENERATE):

        async def _handle_regenerate(call) -> None:
            for existing_entry in hass.config_entries.async_entries(DOMAIN):
                await async_regenerate_dashboard(hass, existing_entry)

        hass.services.async_register(DOMAIN, SERVICE_REGENERATE, _handle_regenerate)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    entry_data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if entry_data:
        for unsub in entry_data.get("unsubscribers", []):
            unsub()
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Wird aufgerufen, sobald im Options-Flow etwas geändert wurde."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    for unsub in entry_data.get("unsubscribers", []):
        unsub()
    entry_data["unsubscribers"] = []

    file_path = await async_regenerate_dashboard(hass, entry)
    _notify_setup_info(hass, entry, file_path)

    _setup_button_listeners(hass, entry)
    await _setup_display_listeners(hass, entry)


# ----------------------------------------------------------------------
# Tasten: auf die event.-Entität hören; wenn deren Attribut "event_type"
# dem konfigurierten Wert entspricht, die zugeordnete Aktion ausführen.
# ----------------------------------------------------------------------
def _setup_button_listeners(hass: HomeAssistant, entry: ConfigEntry) -> None:
    buttons = entry.options.get(CONF_BUTTONS, [])
    entry_data = hass.data[DOMAIN][entry.entry_id]

    for button in buttons:
        entity_id = button.get("entity_id")
        wanted_event = button.get(CONF_EVENT_TYPE, "click")
        action = button.get(CONF_ACTION)
        if not entity_id or not action:
            continue

        @callback
        def _make_listener(action_config: dict, expected_event: str, source_entity: str):
            async def _on_state_change(event: Event[EventStateChangedData]) -> None:
                new_state = event.data.get("new_state")
                if new_state is None:
                    return
                # Bei event.-Entitäten steht der ausgelöste Typ im Attribut
                # "event_type" (der Zustand selbst ist nur ein Zeitstempel).
                if new_state.attributes.get("event_type") != expected_event:
                    return

                _LOGGER.debug(
                    "Button Plus: %s (%s) ausgelöst, führe Aktion aus",
                    source_entity,
                    expected_event,
                )
                try:
                    await async_call_from_config(
                        hass, action_config, blocking=False, validate_config=True
                    )
                except Exception:  # noqa: BLE001
                    _LOGGER.exception(
                        "Button Plus: Aktion für %s konnte nicht ausgeführt werden",
                        source_entity,
                    )

            return _on_state_change

        unsub = async_track_state_change_event(
            hass, [entity_id], _make_listener(action, wanted_event, entity_id)
        )
        entry_data["unsubscribers"].append(unsub)


# ----------------------------------------------------------------------
# Display: Wert der Quell-Entität per text.set_value automatisch in die
# Ziel-Text-Entität (z.B. text.btn_..._displayitem_0_value) schreiben.
# ----------------------------------------------------------------------
async def _setup_display_listeners(hass: HomeAssistant, entry: ConfigEntry) -> None:
    rows = entry.options.get(CONF_DISPLAY_ROWS, [])
    entry_data = hass.data[DOMAIN][entry.entry_id]

    for row in rows:
        target_entity = row.get("target_entity_id")
        source_entity = row.get("source_entity_id")
        tmpl = row.get("template")
        label_target = row.get("label_target_entity_id")
        label_text = row.get("label_text")
        unit_target = row.get("unit_target_entity_id")
        unit_text = row.get("unit_text")

        if not target_entity:
            continue

        # Label- und Unit-Text-Entitäten einmalig setzen (ändern sich normalerweise nicht).
        if label_target and label_text:
            await hass.services.async_call(
                "text",
                "set_value",
                {"entity_id": label_target, "value": label_text},
                blocking=False,
            )
        if unit_target and unit_text:
            await hass.services.async_call(
                "text",
                "set_value",
                {"entity_id": unit_target, "value": unit_text},
                blocking=False,
            )

        if not source_entity:
            continue

        async def _publish_value(src: str, target: str, tmpl_: str) -> None:
            if tmpl_:
                rendered = template_helper.Template(tmpl_, hass).async_render(
                    {"state": hass.states.get(src)}, parse_result=False
                )
            else:
                state = hass.states.get(src)
                rendered = state.state if state else ""
            # HA "text" Entities akzeptieren i.d.R. maximal 255 Zeichen.
            rendered = str(rendered)[:255]
            await hass.services.async_call(
                "text", "set_value", {"entity_id": target, "value": rendered}, blocking=False
            )

        @callback
        def _make_listener(src: str, target: str, tmpl_: str):
            async def _on_state_change(event: Event[EventStateChangedData]) -> None:
                await _publish_value(src, target, tmpl_)

            return _on_state_change

        unsub = async_track_state_change_event(
            hass, [source_entity], _make_listener(source_entity, target_entity, tmpl)
        )
        entry_data["unsubscribers"].append(unsub)

        # Initial einmal senden, nicht erst auf die nächste Änderung warten.
        await _publish_value(source_entity, target_entity, tmpl)


def _notify_setup_info(hass: HomeAssistant, entry: ConfigEntry, file_path: str) -> None:
    """Zeigt einmalig den configuration.yaml Schnipsel zum Einbinden des Dashboards."""
    snippet = lovelace_yaml_snippet(entry)
    message = (
        f"Dashboard-Datei wurde erzeugt/aktualisiert: `{file_path}`\n\n"
        "Falls du dieses Dashboard noch NICHT in der Seitenleiste hast, füge folgenden "
        "Block einmalig in deine `configuration.yaml` ein und starte Home Assistant neu:\n\n"
        f"```yaml\n{snippet}```\n\n"
        "Änderungen an der Zuordnung (Optionen der Integration) aktualisieren die Datei "
        "danach automatisch – ein erneuter Neustart ist dafür nicht nötig."
    )
    persistent_notification.async_create(
        hass,
        message,
        title="Button Plus Manager",
        notification_id=f"button_plus_manager_{entry.entry_id}",
    )
