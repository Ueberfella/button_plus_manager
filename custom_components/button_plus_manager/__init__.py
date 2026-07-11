"""Button Plus Manager – hört direkt auf die MQTT-Tasten-Topics deines Geräts,
löst konfigurierte Aktionen aus, schreibt Infos auf das Display und baut
automatisch ein Lovelace-Dashboard."""
from __future__ import annotations

import json
import logging

from homeassistant.components import mqtt, persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import template as template_helper
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.service import async_call_from_config

from .const import (
    CONF_ACTION,
    CONF_BUTTONS,
    CONF_DEVICE_ID,
    CONF_DISPLAY_ITEM_INDEX,
    CONF_DISPLAY_ROWS,
    CONF_EVENT_TYPE,
    CONF_PAGE,
    CONF_POSITION,
    DOMAIN,
    SERVICE_REGENERATE,
    TOPIC_BUTTON_EVENT,
    TOPIC_DISPLAY_LABEL_SET,
    TOPIC_DISPLAY_VALUE_SET,
)
from .dashboard import async_regenerate_dashboard, lovelace_yaml_snippet

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = []  # diese Integration erzeugt keine eigenen Entities


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"unsubscribers": []}

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    file_path = await async_regenerate_dashboard(hass, entry)
    _notify_setup_info(hass, entry, file_path)

    await _setup_button_mqtt_listeners(hass, entry)
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

    await _setup_button_mqtt_listeners(hass, entry)
    await _setup_display_listeners(hass, entry)


# ----------------------------------------------------------------------
# Tasten: direkt das MQTT-Topic des physischen Buttons abonnieren
# (buttonplus/<device_id>/button/<position>-<page>/pushbutton)
# ----------------------------------------------------------------------
async def _setup_button_mqtt_listeners(hass: HomeAssistant, entry: ConfigEntry) -> None:
    device_id = entry.data.get(CONF_DEVICE_ID)
    buttons = entry.options.get(CONF_BUTTONS, [])
    entry_data = hass.data[DOMAIN][entry.entry_id]

    if not device_id:
        return

    for button in buttons:
        position = button.get(CONF_POSITION)
        page = button.get(CONF_PAGE, 1)
        wanted_event = button.get(CONF_EVENT_TYPE, "click")
        action = button.get(CONF_ACTION)
        if position is None or not action:
            continue

        topic = TOPIC_BUTTON_EVENT.format(device_id=device_id, position=position, page=page)

        @callback
        def _make_message_handler(action_config: dict, expected_event: str, topic_: str):
            async def _handle_message(msg) -> None:
                try:
                    payload = json.loads(msg.payload)
                except (ValueError, TypeError):
                    _LOGGER.debug("Button Plus: ungültiges Payload auf %s: %s", topic_, msg.payload)
                    return

                if payload.get("event_type") != expected_event:
                    return

                _LOGGER.debug("Button Plus: %s (%s) ausgelöst", topic_, expected_event)
                try:
                    await async_call_from_config(
                        hass, action_config, blocking=False, validate_config=True
                    )
                except Exception:  # noqa: BLE001
                    _LOGGER.exception(
                        "Button Plus: Aktion für %s konnte nicht ausgeführt werden", topic_
                    )

            return _handle_message

        unsub = await mqtt.async_subscribe(
            hass, topic, _make_message_handler(action, wanted_event, topic)
        )
        entry_data["unsubscribers"].append(unsub)


# ----------------------------------------------------------------------
# Display: Wert automatisch an buttonplus/<device_id>/displayitem/<i>/value/set
# senden, sobald sich die Quell-Entität ändert. Label wird einmalig gesetzt.
# ----------------------------------------------------------------------
async def _setup_display_listeners(hass: HomeAssistant, entry: ConfigEntry) -> None:
    device_id = entry.data.get(CONF_DEVICE_ID)
    rows = entry.options.get(CONF_DISPLAY_ROWS, [])
    entry_data = hass.data[DOMAIN][entry.entry_id]

    if not device_id:
        return

    for row in rows:
        entity_id = row.get("entity_id")
        index = row.get(CONF_DISPLAY_ITEM_INDEX)
        tmpl = row.get("template")
        label = row.get("label")
        if not entity_id or index is None:
            continue

        value_topic = TOPIC_DISPLAY_VALUE_SET.format(device_id=device_id, index=index)
        label_topic = TOPIC_DISPLAY_LABEL_SET.format(device_id=device_id, index=index)

        async def _publish_value(entity: str, topic_: str, tmpl_: str) -> None:
            if tmpl_:
                rendered = template_helper.Template(tmpl_, hass).async_render(
                    {"state": hass.states.get(entity)}, parse_result=False
                )
            else:
                state = hass.states.get(entity)
                rendered = state.state if state else ""
            await mqtt.async_publish(hass, topic_, rendered)

        @callback
        def _make_listener(entity: str, topic_: str, tmpl_: str):
            async def _on_state_change(event: Event[EventStateChangedData]) -> None:
                await _publish_value(entity, topic_, tmpl_)

            return _on_state_change

        unsub = async_track_state_change_event(
            hass, [entity_id], _make_listener(entity_id, value_topic, tmpl)
        )
        entry_data["unsubscribers"].append(unsub)

        # Label einmalig setzen und aktuellen Wert direkt initial senden.
        if label:
            await mqtt.async_publish(hass, label_topic, label)
        await _publish_value(entity_id, value_topic, tmpl)


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
