"""Characterization tests for the Nmap Tracker scan path.

These capture the current behaviour of NmapDeviceScanner._build_options,
_run_nmap_scan, _async_run_nmap_scan and _async_device_offline so it can be
refactored safely. The nmap library is always mocked; no real scan is run.
"""

from collections.abc import Generator
from datetime import timedelta
from typing import Any
from unittest.mock import MagicMock, patch

from freezegun.api import FrozenDateTimeFactory
from nmap import PortScannerError
import pytest

from homeassistant.components.device_tracker import CONF_CONSIDER_HOME
from homeassistant.components.nmap_tracker import (
    NMAP_TRANSIENT_FAILURE,
    NmapDevice,
    NmapDeviceScanner,
    signal_device_update,
)
from homeassistant.components.nmap_tracker.const import (
    CONF_HOME_INTERVAL,
    CONF_HOSTS_EXCLUDE,
    CONF_HOSTS_LIST,
    CONF_MAC_EXCLUDE,
    CONF_OPTIONS,
    DEFAULT_OPTIONS,
    DOMAIN,
    TRACKER_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt as dt_util

from tests.common import MockConfigEntry

IP = "192.168.1.5"
RAW_MAC = "AA:BB:CC:DD:EE:FF"
MAC = "aa:bb:cc:dd:ee:ff"
OTHER_IP = "192.168.1.6"
OTHER_MAC = "aa:bb:cc:dd:ee:01"

BASE_OPTIONS = {
    CONF_HOSTS_LIST: ["192.168.1.0/24"],
    CONF_HOME_INTERVAL: 3,
    CONF_OPTIONS: DEFAULT_OPTIONS,
    CONF_HOSTS_EXCLUDE: ["192.168.1.1"],
    CONF_MAC_EXCLUDE: [],
}


def _host(
    state: str = "up",
    reason: str = "arp-response",
    mac: str | None = RAW_MAC,
    hostnames: list[dict[str, str]] | None = None,
    vendor: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return one host entry shaped like PortScanner.scan()["scan"][ip]."""
    addresses = {"mac": mac} if mac else {}
    return {
        "status": {"state": state, "reason": reason},
        "addresses": addresses,
        "hostnames": [] if hostnames is None else hostnames,
        "vendor": vendor or {},
    }


def _result(hosts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Return a PortScanner.scan() result."""
    return {"nmap": {}, "scan": hosts}


def _capture_signal(hass: HomeAssistant, signal: str) -> list[tuple[Any, ...]]:
    """Record every dispatch of a signal."""
    calls: list[tuple[Any, ...]] = []

    @callback
    def _record(*args: Any) -> None:
        calls.append(args)

    async_dispatcher_connect(hass, signal, _record)
    return calls


@pytest.fixture
def mock_scan() -> Generator[MagicMock]:
    """Mock PortScanner so scan() never runs nmap."""
    with patch("homeassistant.components.nmap_tracker.PortScanner") as scanner_cls:
        yield scanner_cls.return_value.scan


@pytest.fixture
def mock_get_mac() -> Generator[MagicMock]:
    """Mock the getmac ARP lookup."""
    with patch(
        "homeassistant.components.nmap_tracker.get_mac_address", return_value=None
    ) as get_mac:
        yield get_mac


@pytest.fixture
def mock_vendor() -> Generator[MagicMock]:
    """Mock the OUI vendor lookup."""
    with patch(
        "homeassistant.components.nmap_tracker.aiooui.get_vendor", return_value=None
    ) as get_vendor:
        yield get_vendor


async def _setup_scanner(
    hass: HomeAssistant, **options: Any
) -> tuple[MockConfigEntry, NmapDeviceScanner]:
    """Set up a config entry without starting the periodic scanner."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=2,
        options={**BASE_OPTIONS, **options},
        title="Nmap Test Tracker",
    )
    entry.add_to_hass(hass)
    # Prevent the scanner from starting; tests drive scans directly
    with patch(
        "homeassistant.components.nmap_tracker.NmapDeviceScanner._async_start_scanner",
        return_value=None,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, entry.runtime_data


# --- _build_options ---------------------------------------------------------


async def test_build_options_first_scan(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test the first scan uses configured excludes plus --reason and -v."""
    _, scanner = await _setup_scanner(hass)

    assert scanner._build_options() == (
        f"{DEFAULT_OPTIONS} --exclude 192.168.1.1 --reason -v"
    )
    assert scanner._last_results == []


async def test_build_options_keeps_recent_results(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test only devices seen within home_interval are kept and excluded."""
    _, scanner = await _setup_scanner(hass)
    now = dt_util.now()

    def _device(ipv4: str, age: timedelta) -> NmapDevice:
        return NmapDevice(MAC, "", "", ipv4, "", "", now - age, None)

    recent = _device("192.168.1.10", timedelta(minutes=1))
    on_boundary = _device("192.168.1.11", timedelta(minutes=3))
    stale = _device("192.168.1.12", timedelta(minutes=4))
    scanner._last_results = [recent, on_boundary, stale]

    assert scanner._build_options() == (
        f"{DEFAULT_OPTIONS} --exclude 192.168.1.1,192.168.1.10 --reason -v"
    )
    # Only devices strictly newer than now - home_interval survive
    assert scanner._last_results == [recent]
    # The configured exclude list is not mutated
    assert scanner._exclude == ["192.168.1.1"]


# --- _async_run_nmap_scan ---------------------------------------------------


async def test_host_up_with_mac(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_scan: MagicMock,
    mock_get_mac: MagicMock,
    mock_vendor: MagicMock,
) -> None:
    """Test an up host with a MAC from nmap is tracked as a new device."""
    entry, scanner = await _setup_scanner(hass)
    new_calls = _capture_signal(hass, scanner.signal_device_new)
    mock_scan.return_value = _result(
        {
            IP: _host(
                hostnames=[{"name": "laptop.lan", "type": "PTR"}],
                vendor={RAW_MAC: "Apple"},
            )
        }
    )

    await scanner._async_run_nmap_scan()
    await hass.async_block_till_done()

    mock_scan.assert_called_once_with(
        hosts="192.168.1.0/24",
        arguments=f"{DEFAULT_OPTIONS} --exclude 192.168.1.1 --reason -v",
        timeout=TRACKER_SCAN_INTERVAL * 10,
    )
    mock_get_mac.assert_not_called()
    mock_vendor.assert_not_called()
    device = NmapDevice(
        MAC, "laptop.lan", "laptop", IP, "Apple", "arp-response", dt_util.now(), None
    )
    assert scanner.devices.tracked == {MAC: device}
    assert scanner.devices.ipv4_last_mac == {IP: MAC}
    assert scanner.devices.config_entry_owner == {MAC: entry.entry_id}
    assert scanner._last_results == [device]
    assert new_calls == [(MAC,)]


async def test_host_up_without_mac(
    hass: HomeAssistant,
    mock_scan: MagicMock,
    mock_get_mac: MagicMock,
    mock_vendor: MagicMock,
) -> None:
    """Test an up host without a MAC falls back to getmac and the OUI vendor."""
    _, scanner = await _setup_scanner(hass)
    mock_get_mac.return_value = OTHER_MAC
    mock_vendor.return_value = "Acme"
    # nmap run with -n reports an empty hostname rather than no hostnames
    mock_scan.return_value = _result(
        {OTHER_IP: _host(mac=None, hostnames=[{"name": "", "type": ""}])}
    )

    await scanner._async_run_nmap_scan()
    await hass.async_block_till_done()

    mock_get_mac.assert_called_once_with(ip=OTHER_IP)
    mock_vendor.assert_called_once_with(OTHER_MAC)
    device = scanner.devices.tracked[OTHER_MAC]
    assert device.hostname == ""
    # Without a hostname the name is the vendor plus the last 8 MAC characters
    assert device.name == "Acme dd:ee:01"
    assert device.manufacturer == "Acme"


async def test_host_down_unknown_ip(
    hass: HomeAssistant, mock_scan: MagicMock, mock_get_mac: MagicMock
) -> None:
    """Test a down host that was never seen is ignored."""
    _, scanner = await _setup_scanner(hass)
    new_calls = _capture_signal(hass, scanner.signal_device_new)
    mock_scan.return_value = _result({IP: _host(state="down", reason="no-response")})

    await scanner._async_run_nmap_scan()

    mock_get_mac.assert_not_called()
    assert scanner.devices.tracked == {}
    assert scanner.devices.ipv4_last_mac == {}
    assert new_calls == []


async def test_mac_excluded(
    hass: HomeAssistant, mock_scan: MagicMock, mock_vendor: MagicMock
) -> None:
    """Test an excluded MAC is skipped before ownership is claimed."""
    _, scanner = await _setup_scanner(hass, **{CONF_MAC_EXCLUDE: [MAC]})
    new_calls = _capture_signal(hass, scanner.signal_device_new)
    mock_scan.return_value = _result({IP: _host()})

    await scanner._async_run_nmap_scan()

    assert scanner.devices.tracked == {}
    assert scanner.devices.config_entry_owner == {}
    assert scanner._last_results == []
    assert new_calls == []


async def test_device_owned_by_other_entry(
    hass: HomeAssistant, mock_scan: MagicMock, mock_vendor: MagicMock
) -> None:
    """Test a MAC owned by another config entry is skipped."""
    _, scanner = await _setup_scanner(hass)
    scanner.devices.config_entry_owner[MAC] = "other_entry_id"
    new_calls = _capture_signal(hass, scanner.signal_device_new)
    mock_scan.return_value = _result({IP: _host()})

    await scanner._async_run_nmap_scan()

    assert scanner.devices.tracked == {}
    assert scanner.devices.config_entry_owner == {MAC: "other_entry_id"}
    assert new_calls == []


async def test_new_vs_existing_device_signals(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_scan: MagicMock,
    mock_vendor: MagicMock,
) -> None:
    """Test a new device sends device_new and a known one sends device_update True."""
    _, scanner = await _setup_scanner(hass)
    new_calls = _capture_signal(hass, scanner.signal_device_new)
    update_calls = _capture_signal(hass, signal_device_update(MAC))
    mock_scan.return_value = _result({IP: _host()})

    await scanner._async_run_nmap_scan()
    await hass.async_block_till_done()
    assert new_calls == [(MAC,)]
    assert update_calls == []
    first = scanner.devices.tracked[MAC]

    freezer.tick(timedelta(seconds=30))
    await scanner._async_run_nmap_scan()
    await hass.async_block_till_done()

    assert new_calls == [(MAC,)]
    assert update_calls == [(True,)]
    # The recently seen IP is added to the excludes of the next scan
    assert mock_scan.call_args.kwargs["arguments"] == (
        f"{DEFAULT_OPTIONS} --exclude 192.168.1.1,{IP} --reason -v"
    )
    # The device is replaced, and _last_results now holds both the kept and new copy
    second = scanner.devices.tracked[MAC]
    assert second is not first
    assert second.last_update == dt_util.now()
    assert scanner._last_results == [first, second]


# --- _async_device_offline (consider_home) ---------------------------------


async def test_device_offline_consider_home(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_scan: MagicMock,
    mock_vendor: MagicMock,
) -> None:
    """Test a device is only marked away after being offline for consider_home."""
    _, scanner = await _setup_scanner(hass, **{CONF_CONSIDER_HOME: 60})
    consider_home = timedelta(seconds=60)
    assert scanner.consider_home == consider_home
    update_calls = _capture_signal(hass, signal_device_update(MAC))

    mock_scan.return_value = _result({IP: _host()})
    await scanner._async_run_nmap_scan()
    await hass.async_block_till_done()
    device = scanner.devices.tracked[MAC]

    # First time down: only the offline timestamp is recorded
    mock_scan.return_value = _result({IP: _host(state="down", reason="no-response")})
    freezer.tick(timedelta(seconds=5))
    first_offline = dt_util.now()
    await scanner._async_run_nmap_scan()
    assert device.first_offline == first_offline
    assert device.reason == "arp-response"
    assert update_calls == []

    # Just under consider_home: still home
    freezer.tick(consider_home - timedelta(seconds=1))
    await scanner._async_run_nmap_scan()
    assert update_calls == []
    assert scanner.devices.ipv4_last_mac == {IP: MAC}

    # Exactly consider_home: marked away and the IP mapping is dropped
    freezer.tick(timedelta(seconds=1))
    await scanner._async_run_nmap_scan()
    await hass.async_block_till_done()
    assert update_calls == [(False,)]
    assert device.reason == "no-response"
    assert device.first_offline == first_offline
    assert scanner.devices.ipv4_last_mac == {}
    assert scanner.devices.tracked[MAC] is device

    # Further down scans no longer resolve the IP, so nothing is sent
    freezer.tick(timedelta(seconds=60))
    await scanner._async_run_nmap_scan()
    assert update_calls == [(False,)]


# --- _run_nmap_scan retries -------------------------------------------------


async def test_transient_error_is_retried(
    hass: HomeAssistant, mock_scan: MagicMock, mock_vendor: MagicMock
) -> None:
    """Test a transient nmap error is retried and the next result is used."""
    _, scanner = await _setup_scanner(hass)
    mock_scan.side_effect = [
        PortScannerError(f"{NMAP_TRANSIENT_FAILURE} (Target.cc: 503)"),
        _result({IP: _host()}),
    ]

    await scanner._async_run_nmap_scan()
    await hass.async_block_till_done()

    assert mock_scan.call_count == 2
    assert MAC in scanner.devices.tracked
