"""Tests for the nmap_tracker component."""

from unittest.mock import patch

from homeassistant.components.nmap_tracker.const import (
    CONF_HOME_INTERVAL,
    CONF_HOSTS_EXCLUDE,
    CONF_HOSTS_LIST,
    CONF_MAC_EXCLUDE,
    CONF_OPTIONS,
    DEFAULT_OPTIONS,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_EXCLUDE, CONF_HOSTS
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry


async def test_migrate_entry(hass: HomeAssistant) -> None:
    """Test migrating a config entry from version 1 to version 2."""
    mock_entry = MockConfigEntry(
        unique_id="test_nmap_tracker",
        domain=DOMAIN,
        version=1,
        options={
            CONF_HOSTS: "192.168.1.0/24,192.168.2.0/24",
            CONF_HOME_INTERVAL: 3,
            CONF_OPTIONS: DEFAULT_OPTIONS,
            CONF_EXCLUDE: "192.168.1.1,192.168.2.2",
        },
        title="Nmap Test Tracker",
    )

    mock_entry.add_to_hass(hass)
    # Prevent the scanner from starting
    with patch(
        "homeassistant.components.nmap_tracker.NmapDeviceScanner._async_start_scanner",
        return_value=None,
    ):
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

    # Check that it has a source_id now
    updated_entry = hass.config_entries.async_get_entry(mock_entry.entry_id)

    assert updated_entry
    assert updated_entry.version == 1
    assert updated_entry.minor_version == 2
    assert updated_entry.options == {
        CONF_EXCLUDE: "192.168.1.1,192.168.2.2",
        CONF_HOME_INTERVAL: 3,
        CONF_HOSTS: "192.168.1.0/24,192.168.2.0/24",
        CONF_HOSTS_EXCLUDE: ["192.168.1.1", "192.168.2.2"],
        CONF_HOSTS_LIST: ["192.168.1.0/24", "192.168.2.0/24"],
        CONF_MAC_EXCLUDE: [],
        CONF_OPTIONS: DEFAULT_OPTIONS,
    }
    assert updated_entry.state is ConfigEntryState.LOADED


async def test_migrate_entry_fails_on_downgrade(hass: HomeAssistant) -> None:
    """Test that migration fails when user downgrades from a future version."""
    mock_entry = MockConfigEntry(
        unique_id="test_nmap_tracker",
        domain=DOMAIN,
        version=2,
        options={
            CONF_HOSTS: ["192.168.1.0/24"],
            CONF_HOME_INTERVAL: 3,
            CONF_OPTIONS: DEFAULT_OPTIONS,
            CONF_EXCLUDE: ["192.168.1.1"],
        },
        title="Nmap Test Tracker",
    )

    mock_entry.add_to_hass(hass)

    # Prevent the scanner from starting
    with patch(
        "homeassistant.components.nmap_tracker.NmapDeviceScanner._async_start_scanner",
        return_value=None,
    ):
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

    # Check that entry is in migration error state
    updated_entry = hass.config_entries.async_get_entry(mock_entry.entry_id)
    assert updated_entry
    assert updated_entry.version == 2
    assert updated_entry.state is ConfigEntryState.MIGRATION_ERROR


async def test_scan_creates_entity(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test that a host found by a scan becomes a device_tracker entity."""
    mac = "aa:bb:cc:dd:ee:ff"
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=2,
        options={
            CONF_HOSTS_LIST: ["192.168.1.0/24"],
            CONF_HOSTS_EXCLUDE: [],
            CONF_MAC_EXCLUDE: [],
            CONF_HOME_INTERVAL: 0,
            CONF_OPTIONS: DEFAULT_OPTIONS,
        },
    )
    mock_entry.add_to_hass(hass)
    hass.set_state(CoreState.not_running)

    # Mock only the nmap binary; the scanner, dispatcher and entity platform run for real
    with patch("homeassistant.components.nmap_tracker.PortScanner") as mock_scanner_cls:
        mock_scanner_cls.return_value.scan.return_value = {
            "scan": {
                "192.168.1.10": {
                    "status": {"state": "up", "reason": "arp-response"},
                    "addresses": {"ipv4": "192.168.1.10", "mac": mac.upper()},
                    "hostnames": [{"name": "printer.local", "type": "PTR"}],
                    "vendor": {},
                }
            }
        }
        assert await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()
        hass.bus.async_fire("homeassistant_started")
        await hass.async_block_till_done()

    entity_id = entity_registry.async_get_entity_id("device_tracker", DOMAIN, mac)
    assert entity_id is not None
