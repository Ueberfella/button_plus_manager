"""Button Plus Manager – ordnet Tasten/Schalter per GUI zu, löst Aktionen aus
und schreibt Infos auf das Display, plus automatische Dashboard-Erzeugung."""
from __future__ import annotations

import logging

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import template as template_helper
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.service import async_call_from_config

from .const import CONF_ACTION, CONF_BUTTONS, CONF_DISPLAY_ROWS, CONF_MQTT_TOPIC, DOMAIN, SERVICE_REGENERATE
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
    # Alte Listener abmelden, bevor wir mit den neuen Optionen neu registrieren.
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    for unsub in entry_data.get("unsubscribers", []):
        unsub()
    entry_data["unsubscribers"] = []

    file_path = await async_regenerate_dashboard(hass, entry)
    _notify_setup_info(hass, entry, file_path)

    _setup_button_listeners(hass, entry)
    await _setup_display_listeners(hass, entry)


# ----------------------------------------------------------------------
# Tasten: bei Zustandsänderung die konfigurierte Aktion (Service) ausführen
# ----------------------------------------------------------------------
def _setup_button_listeners(hass: HomeAssistant, entry: ConfigEntry) -> None:
    buttons = entry.options.get(CONF_BUTTONS, [])
    entry_data = hass.data[DOMAIN][entry.entry_id]

    for button in buttons:
        entity_id = button.get("entity_id")
        action = button.get(CONF_ACTION)
        if not entity_id or not action:
            continue

        @callback
        def _make_listener(action_config: dict, source_entity: str):
            async def _on_state_change(event: Event[EventStateChangedData]) -> None:
                new_state = event.data.get("new_state")
                old_state = event.data.get("old_state")
                if new_state is None or old_state is None:
                    return
                if new_state.state == old_state.state:
                    return
                _LOGGER.debug(
                    "Button Plus: %s ausgelöst, führe Aktion aus", source_entity
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
            hass, [entity_id], _make_listener(action, entity_id)
        )
        entry_data["unsubscribers"].append(unsub)


# ----------------------------------------------------------------------
# Display: bei Zustandsänderung der Quell-Entität den Text per MQTT senden
# ----------------------------------------------------------------------
async def _setup_display_listeners(hass: HomeAssistant, entry: ConfigEntry) -> None:
    rows = entry.options.get(CONF_DISPLAY_ROWS, [])
    entry_data = hass.data[DOMAIN][entry.entry_id]

    for row in rows:
        entity_id = row.get("entity_id")
        topic = row.get(CONF_MQTT_TOPIC)
        tmpl = row.get("template")
        if not entity_id or not topic:
            continue

        async def _publish(entity: str, topic_: str, tmpl_: str) -> None:
            if tmpl_:
                rendered = template_helper.Template(tmpl_, hass).async_render(
                    {"state": hass.states.get(entity)}, parse_result=False
                )
            else:
                state = hass.states.get(entity)
                rendered = state.state if state else ""
            await hass.services.async_call(
                "mqtt", "publish", {"topic": topic_, "payload": rendered}, blocking=False
            )

        @callback
        def _make_listener(entity: str, topic_: str, tmpl_: str):
            async def _on_state_change(event: Event[EventStateChangedData]) -> None:
                await _publish(entity, topic_, tmpl_)

            return _on_state_change

        unsub = async_track_state_change_event(
            hass, [entity_id], _make_listener(entity_id, topic, tmpl)
        )
        entry_data["unsubscribers"].append(unsub)

        # Einmal initial senden, nicht erst auf die nächste Änderung warten.
        await _publish(entity_id, topic, tmpl)


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
