"""Erzeugt automatisch ein Lovelace-Dashboard aus der Button/Schalter-Zuordnung."""
from __future__ import annotations

from pathlib import Path

import yaml
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import slugify

from .const import (
    CONF_BUTTONS,
    CONF_DASHBOARD_TITLE,
    CONF_DISPLAY_ROWS,
    CONF_EVENT_TYPE,
    CONF_SWITCHES,
    DASHBOARD_SUBDIR,
    DEFAULT_BUTTON_ICON,
    DEFAULT_SWITCH_ICON,
)


def _dashboard_filename(entry: ConfigEntry) -> str:
    title = entry.data.get(CONF_DASHBOARD_TITLE, "button_plus")
    return f"button_plus_{slugify(title)}.yaml"


def build_dashboard_config(entry: ConfigEntry) -> dict:
    """Baut das Lovelace-Dashboard (als Python-Dict) aus den gespeicherten Optionen."""
    title = entry.data.get(CONF_DASHBOARD_TITLE, "Button Plus")
    switches = entry.options.get(CONF_SWITCHES, [])
    buttons = entry.options.get(CONF_BUTTONS, [])

    switch_cards = [
        {
            "type": "tile",
            "entity": s["entity_id"],
            "name": s.get("label") or s["entity_id"],
            "icon": s.get("icon") or DEFAULT_SWITCH_ICON,
            "features": [{"type": "toggle"}],
        }
        for s in switches
        if s.get("entity_id")
    ]

    button_cards = []
    for b in buttons:
        entity_id = b.get("entity_id")
        if not entity_id:
            continue
        card = {
            "type": "tile",
            "entity": entity_id,
            "name": f"{b.get('label') or entity_id} ({b.get(CONF_EVENT_TYPE, 'click')})",
            "icon": b.get("icon") or DEFAULT_BUTTON_ICON,
            "state_content": "last-changed",
        }
        action = b.get("action") or {}
        service = action.get("action") or action.get("service")
        if service:
            card["tap_action"] = {
                "action": "perform-action",
                "perform_action": service,
                "target": action.get("target", {}),
                "data": action.get("data", {}),
            }
        button_cards.append(card)

    display_rows = entry.options.get(CONF_DISPLAY_ROWS, [])
    display_entities = [
        {"entity": r["target_entity_id"], "name": r.get("label_text") or r["target_entity_id"]}
        for r in display_rows
        if r.get("target_entity_id")
    ]

    cards = [
        {
            "type": "markdown",
            "content": f"## {title}\nAutomatisch erzeugt von Button Plus Manager.",
        },
        {"type": "grid", "columns": 2, "square": False, "cards": switch_cards},
        {"type": "markdown", "content": "### Tasten"},
        {"type": "grid", "columns": 3, "square": False, "cards": button_cards},
    ]

    if display_entities:
        cards.append({"type": "markdown", "content": "### Display-Zeilen (aktueller Inhalt)"})
        cards.append(
            {"type": "entities", "show_header_toggle": False, "entities": display_entities}
        )

    return {
        "title": title,
        "views": [
            {
                "title": title,
                "path": f"button-plus-{slugify(title)}",
                "icon": "mdi:gesture-tap-button",
                "cards": cards,
            }
        ],
    }


async def async_regenerate_dashboard(hass: HomeAssistant, entry: ConfigEntry) -> str:
    """Schreibt die Dashboard-YAML-Datei neu und gibt den vollen Pfad zurück."""
    config = build_dashboard_config(entry)
    filename = _dashboard_filename(entry)
    dashboards_dir = Path(hass.config.path(DASHBOARD_SUBDIR))

    def _write() -> str:
        dashboards_dir.mkdir(parents=True, exist_ok=True)
        file_path = dashboards_dir / filename
        with open(file_path, "w", encoding="utf-8") as handle:
            yaml.dump(config, handle, allow_unicode=True, sort_keys=False)
        return str(file_path)

    return await hass.async_add_executor_job(_write)


def lovelace_yaml_snippet(entry: ConfigEntry) -> str:
    """Der configuration.yaml Schnipsel, den der Nutzer EINMALIG einfügen muss."""
    title = entry.data.get(CONF_DASHBOARD_TITLE, "Button Plus")
    url_path = f"button-plus-{slugify(title)}"
    filename = _dashboard_filename(entry)
    return (
        "lovelace:\n"
        "  dashboards:\n"
        f"    {url_path}:\n"
        f"      mode: yaml\n"
        f"      title: {title}\n"
        f"      icon: mdi:gesture-tap-button\n"
        f"      show_in_sidebar: true\n"
        f"      filename: {DASHBOARD_SUBDIR}/{filename}\n"
    )
