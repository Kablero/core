# nmap_tracker Mutation Check (M1-M3)

Each mutation was applied to `homeassistant/components/nmap_tracker/__init__.py` on its own, tested, and then restored with `git checkout`
before the next one. The goal is to show that the 10 characterization tests in `tests/components/nmap_tracker/test_scanner.py` detect each change.

- Commit: `162089a8740ec541cbacfb4930cb25fc5fcd5136` (branch `test_nmap`), `__init__.py` unmodified before each mutation
- Environment: WSL2 Ubuntu, Python 3.14.4, pytest 9.0.3, ruff 0.16.6, venv `~/ha-venv`, run from the repo root
- Mutations were applied with an exact text replacement (it errors unless the target appears exactly once).
  The `git diff` below shows exactly what changed.

## Summary

| Mutation | Change | Result | Failing tests | Caught? |
|---|---|---|---|---|
| M1 | In `_build_options`, delete the line `self._last_results = last_results`. | 1 failed, 9 passed | `test_build_options_keeps_recent_results` | Yes |
| M2 | In `_async_run_nmap_scan`, swap `signal_device_new` and `signal_device_update` in the `if new: ... else: ...` dispatch. | 3 failed, 7 passed | `test_host_up_with_mac`<br>`test_new_vs_existing_device_signals`<br>`test_device_offline_consider_home` | Yes |
| M3 | In `_async_run_nmap_scan`, remove the `continue` after the MAC-exclusion check. | 1 failed, 9 passed | `test_mac_excluded` | Yes |

All three mutations were caught by at least one test, and `__init__.py` was clean after each restore.
M1 and M3 are each caught by a single test, so those tests are the only guard for that behaviour.

## M1

In `_build_options`, delete the line `self._last_results = last_results`.

**Result:** 1 failed, 9 passed. Failing tests:

- `test_build_options_keeps_recent_results`

Without the assignment, stale and boundary devices stay in `_last_results`, so the test that checks `_last_results` after filtering fails.

### a) Diff of the mutation

```text
$ git diff homeassistant/components/nmap_tracker/__init__.py
diff --git a/homeassistant/components/nmap_tracker/__init__.py b/homeassistant/components/nmap_tracker/__init__.py
index 54a79105aa6..997296c40ee 100644
--- a/homeassistant/components/nmap_tracker/__init__.py
+++ b/homeassistant/components/nmap_tracker/__init__.py
@@ -276,7 +276,6 @@ class NmapDeviceScanner:
         # Report down hosts
         if "-v" not in options:
             options += " -v"
-        self._last_results = last_results
         return options
 
     async def _async_scan_devices(self, *_):
```

### b) Tests against the mutated code

```text
$ pytest tests/components/nmap_tracker/test_scanner.py -q -p no:cacheprovider
.F........                                                               [100%]
=================================== FAILURES ===================================
___________________ test_build_options_keeps_recent_results ____________________

hass = <HomeAssistant RUNNING>
freezer = <freezegun.api.FrozenDateTimeFactory object at 0x77ee5bf9e0d0>

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
>       assert scanner._last_results == [recent]
E       AssertionError: assert [NmapDevice(m...offline=None)] == [NmapDevice(m...offline=None)]
E         
E         Left contains 2 more items, first extra item: NmapDevice(mac_address='aa:bb:cc:dd:ee:ff', hostname='', name='', ipv4='192.168.1.11', manufacturer='', reason='', last_update=HAFakeDatetime(2026, 10, 11, 17, 1, 50, 344042, tzinfo=zoneinfo.ZoneInfo(key='US/Pacific')), first_offline=None)
E         Use -v to get more diff

tests/components/nmap_tracker/test_scanner.py:170: AssertionError
----------------------------- Captured stderr call -----------------------------
INFO:homeassistant.loader:Loaded nmap_tracker from homeassistant.components.nmap_tracker
INFO:homeassistant.loader:Loaded network from homeassistant.components.network
INFO:homeassistant.setup:Setting up network
INFO:homeassistant.setup:Setting up nmap_tracker
INFO:homeassistant.loader:Loaded device_tracker from homeassistant.components.device_tracker
INFO:homeassistant.loader:Loaded zone from homeassistant.components.zone
INFO:homeassistant.setup:Setting up zone
INFO:homeassistant.setup:Setting up device_tracker
INFO:homeassistant.components.device_tracker:Setting up nmap_tracker.device_tracker
------------------------------ Captured log call -------------------------------
2026-10-12 02:04:50.344 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded nmap_tracker from homeassistant.components.nmap_tracker
2026-10-12 02:04:50.344 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded network from homeassistant.components.network
2026-10-12 02:04:50.344 INFO     MainThread homeassistant.setup:setup.py:393 Setting up network
2026-10-12 02:04:50.344 INFO     MainThread homeassistant.setup:setup.py:393 Setting up nmap_tracker
2026-10-12 02:04:50.344 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded device_tracker from homeassistant.components.device_tracker
2026-10-12 02:04:50.344 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded zone from homeassistant.components.zone
2026-10-12 02:04:50.344 INFO     MainThread homeassistant.setup:setup.py:393 Setting up zone
2026-10-12 02:04:50.344 INFO     MainThread homeassistant.setup:setup.py:393 Setting up device_tracker
2026-10-12 02:04:50.344 INFO     MainThread homeassistant.components.device_tracker:entity_platform.py:484 Setting up nmap_tracker.device_tracker
=========================== short test summary info ============================
FAILED tests/components/nmap_tracker/test_scanner.py::test_build_options_keeps_recent_results
1 failed, 9 passed in 12.24s
```

### d) Restore

```text
$ git checkout -- homeassistant/components/nmap_tracker/__init__.py
(no output)
```

### e) Confirm clean (no output = clean)

```text
$ git status --short homeassistant/components/nmap_tracker/__init__.py
(no output)
```

## M2

In `_async_run_nmap_scan`, swap `signal_device_new` and `signal_device_update` in the `if new: ... else: ...` dispatch.

**Result:** 3 failed, 7 passed. Failing tests:

- `test_host_up_with_mac`
- `test_new_vs_existing_device_signals`
- `test_device_offline_consider_home`

A new device now sends `device_update` (True) instead of `device_new`, and a known device sends `device_new`. The `consider_home` test also fails because it expects no `device_update` signal after the first scan.

### a) Diff of the mutation

```text
$ git diff homeassistant/components/nmap_tracker/__init__.py
diff --git a/homeassistant/components/nmap_tracker/__init__.py b/homeassistant/components/nmap_tracker/__init__.py
index 54a79105aa6..570dc50d4f2 100644
--- a/homeassistant/components/nmap_tracker/__init__.py
+++ b/homeassistant/components/nmap_tracker/__init__.py
@@ -438,8 +438,8 @@ class NmapDeviceScanner:
             self._last_results.append(device)
 
             if new:
-                async_dispatcher_send(self._hass, self.signal_device_new, formatted_mac)
-            else:
                 async_dispatcher_send(
                     self._hass, signal_device_update(formatted_mac), True
                 )
+            else:
+                async_dispatcher_send(self._hass, self.signal_device_new, formatted_mac)
```

### b) Tests against the mutated code

```text
$ pytest tests/components/nmap_tracker/test_scanner.py -q -p no:cacheprovider
..F....FF.                                                               [100%]
=================================== FAILURES ===================================
____________________________ test_host_up_with_mac _____________________________

hass = <HomeAssistant RUNNING>
freezer = <freezegun.api.FrozenDateTimeFactory object at 0x787ffdd11bd0>
mock_scan = <MagicMock name='PortScanner().scan' id='132491111408576'>
mock_get_mac = <MagicMock name='get_mac_address' id='132491114799056'>
mock_vendor = <MagicMock name='get_vendor' id='132491114794688'>

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
>       assert new_calls == [(MAC,)]
E       AssertionError: assert [] == [('aa:bb:cc:dd:ee:ff',)]
E         
E         Right contains one more item: ('aa:bb:cc:dd:ee:ff',)
E         Use -v to get more diff

tests/components/nmap_tracker/test_scanner.py:214: AssertionError
----------------------------- Captured stderr call -----------------------------
INFO:homeassistant.loader:Loaded nmap_tracker from homeassistant.components.nmap_tracker
INFO:homeassistant.loader:Loaded network from homeassistant.components.network
INFO:homeassistant.setup:Setting up network
INFO:homeassistant.setup:Setting up nmap_tracker
INFO:homeassistant.loader:Loaded device_tracker from homeassistant.components.device_tracker
INFO:homeassistant.loader:Loaded zone from homeassistant.components.zone
INFO:homeassistant.setup:Setting up zone
INFO:homeassistant.setup:Setting up device_tracker
INFO:homeassistant.components.device_tracker:Setting up nmap_tracker.device_tracker
------------------------------ Captured log call -------------------------------
2026-10-12 02:05:08.365 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded nmap_tracker from homeassistant.components.nmap_tracker
2026-10-12 02:05:08.365 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded network from homeassistant.components.network
2026-10-12 02:05:08.365 INFO     MainThread homeassistant.setup:setup.py:393 Setting up network
2026-10-12 02:05:08.365 INFO     MainThread homeassistant.setup:setup.py:393 Setting up nmap_tracker
2026-10-12 02:05:08.365 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded device_tracker from homeassistant.components.device_tracker
2026-10-12 02:05:08.365 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded zone from homeassistant.components.zone
2026-10-12 02:05:08.365 INFO     MainThread homeassistant.setup:setup.py:393 Setting up zone
2026-10-12 02:05:08.365 INFO     MainThread homeassistant.setup:setup.py:393 Setting up device_tracker
2026-10-12 02:05:08.365 INFO     MainThread homeassistant.components.device_tracker:entity_platform.py:484 Setting up nmap_tracker.device_tracker
_____________________ test_new_vs_existing_device_signals ______________________

hass = <HomeAssistant RUNNING>
freezer = <freezegun.api.FrozenDateTimeFactory object at 0x787fef6f0510>
mock_scan = <MagicMock name='PortScanner().scan' id='132491114804432'>
mock_vendor = <MagicMock name='get_vendor' id='132491114795024'>

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
>       assert new_calls == [(MAC,)]
E       AssertionError: assert [] == [('aa:bb:cc:dd:ee:ff',)]
E         
E         Right contains one more item: ('aa:bb:cc:dd:ee:ff',)
E         Use -v to get more diff

tests/components/nmap_tracker/test_scanner.py:306: AssertionError
----------------------------- Captured stderr call -----------------------------
INFO:homeassistant.loader:Loaded nmap_tracker from homeassistant.components.nmap_tracker
INFO:homeassistant.loader:Loaded network from homeassistant.components.network
INFO:homeassistant.setup:Setting up network
INFO:homeassistant.setup:Setting up nmap_tracker
INFO:homeassistant.loader:Loaded device_tracker from homeassistant.components.device_tracker
INFO:homeassistant.loader:Loaded zone from homeassistant.components.zone
INFO:homeassistant.setup:Setting up zone
INFO:homeassistant.setup:Setting up device_tracker
INFO:homeassistant.components.device_tracker:Setting up nmap_tracker.device_tracker
------------------------------ Captured log call -------------------------------
2026-10-12 02:05:12.528 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded nmap_tracker from homeassistant.components.nmap_tracker
2026-10-12 02:05:12.528 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded network from homeassistant.components.network
2026-10-12 02:05:12.528 INFO     MainThread homeassistant.setup:setup.py:393 Setting up network
2026-10-12 02:05:12.528 INFO     MainThread homeassistant.setup:setup.py:393 Setting up nmap_tracker
2026-10-12 02:05:12.528 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded device_tracker from homeassistant.components.device_tracker
2026-10-12 02:05:12.528 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded zone from homeassistant.components.zone
2026-10-12 02:05:12.528 INFO     MainThread homeassistant.setup:setup.py:393 Setting up zone
2026-10-12 02:05:12.528 INFO     MainThread homeassistant.setup:setup.py:393 Setting up device_tracker
2026-10-12 02:05:12.528 INFO     MainThread homeassistant.components.device_tracker:entity_platform.py:484 Setting up nmap_tracker.device_tracker
______________________ test_device_offline_consider_home _______________________

hass = <HomeAssistant RUNNING>
freezer = <freezegun.api.FrozenDateTimeFactory object at 0x787ffda52190>
mock_scan = <MagicMock name='PortScanner().scan' id='132491114799056'>
mock_vendor = <MagicMock name='get_vendor' id='132491114804768'>

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
>       assert update_calls == []
E       assert [(True,)] == []
E         
E         Left contains one more item: (True,)
E         Use -v to get more diff

tests/components/nmap_tracker/test_scanner.py:354: AssertionError
----------------------------- Captured stderr call -----------------------------
INFO:homeassistant.loader:Loaded nmap_tracker from homeassistant.components.nmap_tracker
INFO:homeassistant.loader:Loaded network from homeassistant.components.network
INFO:homeassistant.setup:Setting up network
INFO:homeassistant.setup:Setting up nmap_tracker
INFO:homeassistant.loader:Loaded device_tracker from homeassistant.components.device_tracker
INFO:homeassistant.loader:Loaded zone from homeassistant.components.zone
INFO:homeassistant.setup:Setting up zone
INFO:homeassistant.setup:Setting up device_tracker
INFO:homeassistant.components.device_tracker:Setting up nmap_tracker.device_tracker
WARNING:asyncio:Executing <Task finished name='Task-147' coro=<test_device_offline_consider_home() done, defined at /mnt/c/Users/Robel/core/tests/components/nmap_tracker/test_scanner.py:330> exception=AssertionError('assert [(True,)] == []\n  \n  Left contains one more item: (True,)\n  Use -v to get more diff') created at /usr/lib/python3.14/asyncio/runners.py:109> took 5.000 seconds
------------------------------ Captured log call -------------------------------
2026-10-12 02:05:12.927 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded nmap_tracker from homeassistant.components.nmap_tracker
2026-10-12 02:05:12.927 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded network from homeassistant.components.network
2026-10-12 02:05:12.927 INFO     MainThread homeassistant.setup:setup.py:393 Setting up network
2026-10-12 02:05:12.927 INFO     MainThread homeassistant.setup:setup.py:393 Setting up nmap_tracker
2026-10-12 02:05:12.927 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded device_tracker from homeassistant.components.device_tracker
2026-10-12 02:05:12.927 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded zone from homeassistant.components.zone
2026-10-12 02:05:12.927 INFO     MainThread homeassistant.setup:setup.py:393 Setting up zone
2026-10-12 02:05:12.927 INFO     MainThread homeassistant.setup:setup.py:393 Setting up device_tracker
2026-10-12 02:05:12.927 INFO     MainThread homeassistant.components.device_tracker:entity_platform.py:484 Setting up nmap_tracker.device_tracker
2026-10-12 02:05:17.927 WARNING  MainThread asyncio:base_events.py:2052 Executing <Task finished name='Task-147' coro=<test_device_offline_consider_home() done, defined at /mnt/c/Users/Robel/core/tests/components/nmap_tracker/test_scanner.py:330> exception=AssertionError('assert [(True,)] == []\n  \n  Left contains one more item: (True,)\n  Use -v to get more diff') created at /usr/lib/python3.14/asyncio/runners.py:109> took 5.000 seconds
=========================== short test summary info ============================
FAILED tests/components/nmap_tracker/test_scanner.py::test_host_up_with_mac
FAILED tests/components/nmap_tracker/test_scanner.py::test_new_vs_existing_device_signals
FAILED tests/components/nmap_tracker/test_scanner.py::test_device_offline_consider_home
3 failed, 7 passed in 11.69s
```

### d) Restore

```text
$ git checkout -- homeassistant/components/nmap_tracker/__init__.py
(no output)
```

### e) Confirm clean (no output = clean)

```text
$ git status --short homeassistant/components/nmap_tracker/__init__.py
(no output)
```

## M3

In `_async_run_nmap_scan`, remove the `continue` after the MAC-exclusion check.

**Result:** 1 failed, 9 passed. Failing tests:

- `test_mac_excluded`

The excluded MAC is no longer skipped, so it gets an owner, is tracked and sends `device_new`.

### a) Diff of the mutation

```text
$ git diff homeassistant/components/nmap_tracker/__init__.py
diff --git a/homeassistant/components/nmap_tracker/__init__.py b/homeassistant/components/nmap_tracker/__init__.py
index 54a79105aa6..8c7c273f272 100644
--- a/homeassistant/components/nmap_tracker/__init__.py
+++ b/homeassistant/components/nmap_tracker/__init__.py
@@ -417,7 +417,6 @@ class NmapDeviceScanner:
 
             if formatted_mac in self._mac_exclude:
                 _LOGGER.debug("MAC address %s is excluded from tracking", formatted_mac)
-                continue
 
             if (
                 devices.config_entry_owner.setdefault(formatted_mac, entry_id)
```

### b) Tests against the mutated code

```text
$ pytest tests/components/nmap_tracker/test_scanner.py -q -p no:cacheprovider
.....F....                                                               [100%]
=================================== FAILURES ===================================
______________________________ test_mac_excluded _______________________________

hass = <HomeAssistant RUNNING>
mock_scan = <MagicMock name='PortScanner().scan' id='128995340464016'>
mock_vendor = <MagicMock name='get_vendor' id='128995340464352'>

    async def test_mac_excluded(
        hass: HomeAssistant, mock_scan: MagicMock, mock_vendor: MagicMock
    ) -> None:
        """Test an excluded MAC is skipped before ownership is claimed."""
        _, scanner = await _setup_scanner(hass, **{CONF_MAC_EXCLUDE: [MAC]})
        new_calls = _capture_signal(hass, scanner.signal_device_new)
        mock_scan.return_value = _result({IP: _host()})
    
        await scanner._async_run_nmap_scan()
    
>       assert scanner.devices.tracked == {}
E       AssertionError: assert {'aa:bb:cc:dd...offline=None)} == {}
E         
E         Left contains 1 more item:
E         {'aa:bb:cc:dd:ee:ff': NmapDevice(mac_address='aa:bb:cc:dd:ee:ff',
E                                          hostname='192.168.1.5',
E                                          name='192',
E                                          ipv4='192.168.1.5',
E                                          manufacturer=None,...
E         
E         ...Full output truncated (4 lines hidden), use '-vv' to show

tests/components/nmap_tracker/test_scanner.py:270: AssertionError
----------------------------- Captured stderr call -----------------------------
INFO:homeassistant.loader:Loaded nmap_tracker from homeassistant.components.nmap_tracker
INFO:homeassistant.loader:Loaded network from homeassistant.components.network
INFO:homeassistant.setup:Setting up network
INFO:homeassistant.setup:Setting up nmap_tracker
INFO:homeassistant.loader:Loaded device_tracker from homeassistant.components.device_tracker
INFO:homeassistant.loader:Loaded zone from homeassistant.components.zone
INFO:homeassistant.setup:Setting up zone
INFO:homeassistant.setup:Setting up device_tracker
INFO:homeassistant.components.device_tracker:Setting up nmap_tracker.device_tracker
WARNING:asyncio:Executing <Task pending name='Task-98' coro=<test_mac_excluded() running at /mnt/c/Users/Robel/core/tests/components/nmap_tracker/test_scanner.py:264> cb=[_run_until_complete_cb() at /usr/lib/python3.14/asyncio/base_events.py:181] created at /usr/lib/python3.14/asyncio/runners.py:109> took 0.286 seconds
INFO:homeassistant.helpers.entity_registry:Registered new device_tracker.nmap_tracker entity: device_tracker.192
------------------------------ Captured log call -------------------------------
2026-10-12 02:05:27.017 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded nmap_tracker from homeassistant.components.nmap_tracker
2026-10-12 02:05:27.031 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded network from homeassistant.components.network
2026-10-12 02:05:27.050 INFO     MainThread homeassistant.setup:setup.py:393 Setting up network
2026-10-12 02:05:27.088 INFO     MainThread homeassistant.setup:setup.py:393 Setting up nmap_tracker
2026-10-12 02:05:27.121 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded device_tracker from homeassistant.components.device_tracker
2026-10-12 02:05:27.145 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded zone from homeassistant.components.zone
2026-10-12 02:05:27.170 INFO     MainThread homeassistant.setup:setup.py:393 Setting up zone
2026-10-12 02:05:27.238 INFO     MainThread homeassistant.setup:setup.py:393 Setting up device_tracker
2026-10-12 02:05:27.280 INFO     MainThread homeassistant.components.device_tracker:entity_platform.py:484 Setting up nmap_tracker.device_tracker
2026-10-12 02:05:27.303 WARNING  MainThread asyncio:base_events.py:2052 Executing <Task pending name='Task-98' coro=<test_mac_excluded() running at /mnt/c/Users/Robel/core/tests/components/nmap_tracker/test_scanner.py:264> cb=[_run_until_complete_cb() at /usr/lib/python3.14/asyncio/base_events.py:181] created at /usr/lib/python3.14/asyncio/runners.py:109> took 0.286 seconds
2026-10-12 02:05:27.324 INFO     MainThread homeassistant.helpers.entity_registry:entity_registry.py:1638 Registered new device_tracker.nmap_tracker entity: device_tracker.192
=========================== short test summary info ============================
FAILED tests/components/nmap_tracker/test_scanner.py::test_mac_excluded - Ass...
1 failed, 9 passed in 12.09s
```

### d) Restore

```text
$ git checkout -- homeassistant/components/nmap_tracker/__init__.py
(no output)
```

### e) Confirm clean (no output = clean)

```text
$ git status --short homeassistant/components/nmap_tracker/__init__.py
(no output)
```

## Full suite after all three mutations

**Result:** 23 passed (13 original + 10 characterization tests).

```text
$ pytest tests/components/nmap_tracker -q -p no:cacheprovider
.......................                                                  [100%]
23 passed in 12.33s
```
