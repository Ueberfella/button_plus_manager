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

    button_cards = [
        {
            "type": "tile",
            "entity": b["entity_id"],
            "name": b.get("label") or b["entity_id"],
            "icon": b.get("icon") or DEFAULT_BUTTON_ICON,
            "state_content": "last-changed",
        }
        for b in buttons
        if b.get("entity_id")
    ]

    return {
        "title": title,
        "views": [
            {
                "title": title,
                "path": f"button-plus-{slugify(title)}",
                "icon": "mdi:gesture-tap-button",
                "cards": [
                    {
                        "type": "markdown",
                        "content": f"## {title}\nAutomatisch erzeugt von Button Plus Manager.",
                    },
                    {"type": "grid", "columns": 2, "square": False, "cards": switch_cards},
                    {"type": "markdown", "content": "### Tasten"},
                    {"type": "grid", "columns": 3, "square": False, "cards": button_cards},
                ],
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
