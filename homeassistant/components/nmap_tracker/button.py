"""Button to scan the network on demand."""

from typing import override

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NmapDeviceScanner, NmapTrackerConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NmapTrackerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Nmap Tracker scan button."""
    async_add_entities([NmapScanButton(entry.runtime_data, entry.entry_id)])


class NmapScanButton(ButtonEntity):
    """Button that starts a scan for one Nmap Tracker entry."""

    _attr_translation_key = "scan"
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, scanner: NmapDeviceScanner, entry_id: str) -> None:
        """Initialize the button."""
        self._scanner = scanner
        self._attr_unique_id = f"{entry_id}_scan"
        self._attr_device_info = scanner.device_info

    @override
    async def async_press(self) -> None:
        """Start a scan."""
        await self._scanner.async_scan()
