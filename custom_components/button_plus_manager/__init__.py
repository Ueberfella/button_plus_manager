"""Button Plus Manager – ordnet Tasten/Schalter per GUI zu und baut das Dashboard automatisch."""
from __future__ import annotations

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, SERVICE_REGENERATE
from .dashboard import async_regenerate_dashboard, lovelace_yaml_snippet

PLATFORMS: list[str] = []  # diese Integration erzeugt keine eigenen Entities


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    file_path = await async_regenerate_dashboard(hass, entry)
    _notify_setup_info(hass, entry, file_path)

    if not hass.services.has_service(DOMAIN, SERVICE_REGENERATE):

        async def _handle_regenerate(call) -> None:
            for existing_entry in hass.config_entries.async_entries(DOMAIN):
                await async_regenerate_dashboard(hass, existing_entry)

        hass.services.async_register(DOMAIN, SERVICE_REGENERATE, _handle_regenerate)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Wird aufgerufen, sobald im Options-Flow etwas geändert wurde."""
    file_path = await async_regenerate_dashboard(hass, entry)
    _notify_setup_info(hass, entry, file_path)


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
    )"""Button Plus Manager – ordnet Tasten/Schalter per GUI zu und baut das Dashboard automatisch."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, SERVICE_REGENERATE
from .dashboard import async_regenerate_dashboard, lovelace_yaml_snippet

PLATFORMS: list[str] = []  # diese Integration erzeugt keine eigenen Entities


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    file_path = await async_regenerate_dashboard(hass, entry)
    _notify_setup_info(hass, entry, file_path)

    if not hass.services.has_service(DOMAIN, SERVICE_REGENERATE):

        async def _handle_regenerate(call) -> None:
            for existing_entry in hass.config_entries.async_entries(DOMAIN):
                await async_regenerate_dashboard(hass, existing_entry)

        hass.services.async_register(DOMAIN, SERVICE_REGENERATE, _handle_regenerate)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Wird aufgerufen, sobald im Options-Flow etwas geändert wurde."""
    file_path = await async_regenerate_dashboard(hass, entry)
    _notify_setup_info(hass, entry, file_path)


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
    hass.components.persistent_notification.async_create(
        message, title="Button Plus Manager", notification_id=f"button_plus_manager_{entry.entry_id}"
    )
