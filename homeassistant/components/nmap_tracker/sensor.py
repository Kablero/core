"""Sensor for the most recent completed Nmap scan."""

from datetime import datetime
from typing import override

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NmapDeviceScanner, NmapTrackerConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NmapTrackerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Nmap Tracker last scanned sensor."""
    async_add_entities([NmapLastScanSensor(entry.runtime_data, entry.entry_id)])


class NmapLastScanSensor(SensorEntity):
    """Timestamp of the last completed scan for one Nmap Tracker entry."""

    _attr_translation_key = "last_scan"
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, scanner: NmapDeviceScanner, entry_id: str) -> None:
        """Initialize the sensor."""
        self._scanner = scanner
        self._attr_unique_id = f"{entry_id}_last_scan"
        self._attr_device_info = scanner.device_info

    @property
    @override
    def native_value(self) -> datetime | None:
        """Return when the last scan finished."""
        return self._scanner.last_scan

    @callback
    def _async_update(self) -> None:
        """Write state after a scan finishes."""
        self.async_write_ha_state()

    @override
    async def async_added_to_hass(self) -> None:
        """Subscribe to completed scans."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._scanner.signal_scan, self._async_update
            )
        )
