# nmap_tracker Mutation Check

This check shows the characterization tests in `tests/components/nmap_tracker/test_scanner.py`
detect a behaviour change in `NmapDeviceScanner._async_device_offline`.

- Commit: `162089a8740ec541cbacfb4930cb25fc5fcd5136` (branch `test_nmap`)
- Environment: WSL2 Ubuntu, Python 3.14.4, pytest 9.0.3, ruff 0.16.6, venv `~/ha-venv`, run from the repo root
- Mutation: the `consider_home` boundary check `first_offline + consider_home > now` was changed to `>=`.
  With `>=`, a device that has been offline for exactly `consider_home` is still treated as home.

## Result

| Run | Code | Result |
|---|---|---|
| With the break | `>=` | **1 failed, 9 passed** |
| After `git checkout` | original `>` | **10 passed** |

The failure comes from `test_device_offline_consider_home`.
At exactly `consider_home` (60 s in the test) the test expects a `device_update` signal with `False`,
but the broken code sent none (`assert [] == [(False,)]`).

The `took ... seconds` asyncio warning in the output is not a real delay.
It appears because the test moves frozen time forward with `freezer.tick`.

## Commands and output
### a) Diff of the mutation

```text
$ git diff homeassistant/components/nmap_tracker/__init__.py
diff --git a/homeassistant/components/nmap_tracker/__init__.py b/homeassistant/components/nmap_tracker/__init__.py
index 54a79105aa6..5223bb88302 100644
--- a/homeassistant/components/nmap_tracker/__init__.py
+++ b/homeassistant/components/nmap_tracker/__init__.py
@@ -361,7 +361,7 @@ class NmapDeviceScanner:
             )
             device.first_offline = now
             return
-        if device.first_offline + self.consider_home > now:
+        if device.first_offline + self.consider_home >= now:
             _LOGGER.debug(
                 (
                     "Device %s (%s) has NOT been offline (first offline at: %s) long"
```

### b) Tests against the mutated code

```text
$ pytest tests/components/nmap_tracker/test_scanner.py -q -p no:cacheprovider
........F.                                                               [100%]
=================================== FAILURES ===================================
______________________ test_device_offline_consider_home _______________________

hass = <HomeAssistant RUNNING>
freezer = <freezegun.api.FrozenDateTimeFactory object at 0x7f7f410f0c30>
mock_scan = <MagicMock name='PortScanner().scan' id='140184527193488'>
mock_vendor = <MagicMock name='get_vendor' id='140184567773712'>

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
>       assert update_calls == [(False,)]
E       assert [] == [(False,)]
E         
E         Right contains one more item: (False,)
E         Use -v to get more diff

tests/components/nmap_tracker/test_scanner.py:366: AssertionError
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
INFO:homeassistant.helpers.entity_registry:Registered new device_tracker.nmap_tracker entity: device_tracker.192
WARNING:asyncio:Executing <Task pending name='Task-150' coro=<test_device_offline_consider_home() running at /mnt/c/Users/Robel/core/tests/components/nmap_tracker/test_scanner.py:365> cb=[_run_until_complete_cb() at /usr/lib/python3.14/asyncio/base_events.py:181] created at /usr/lib/python3.14/asyncio/runners.py:109> took 65.000 seconds
------------------------------ Captured log call -------------------------------
2026-10-12 02:05:45.704 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded nmap_tracker from homeassistant.components.nmap_tracker
2026-10-12 02:05:45.704 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded network from homeassistant.components.network
2026-10-12 02:05:45.704 INFO     MainThread homeassistant.setup:setup.py:393 Setting up network
2026-10-12 02:05:45.704 INFO     MainThread homeassistant.setup:setup.py:393 Setting up nmap_tracker
2026-10-12 02:05:45.704 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded device_tracker from homeassistant.components.device_tracker
2026-10-12 02:05:45.704 INFO     SyncWorker_0 homeassistant.loader:loader.py:796 Loaded zone from homeassistant.components.zone
2026-10-12 02:05:45.704 INFO     MainThread homeassistant.setup:setup.py:393 Setting up zone
2026-10-12 02:05:45.704 INFO     MainThread homeassistant.setup:setup.py:393 Setting up device_tracker
2026-10-12 02:05:45.704 INFO     MainThread homeassistant.components.device_tracker:entity_platform.py:484 Setting up nmap_tracker.device_tracker
2026-10-12 02:05:45.704 INFO     MainThread homeassistant.helpers.entity_registry:entity_registry.py:1638 Registered new device_tracker.nmap_tracker entity: device_tracker.192
2026-10-12 02:06:50.704 WARNING  MainThread asyncio:base_events.py:2052 Executing <Task pending name='Task-150' coro=<test_device_offline_consider_home() running at /mnt/c/Users/Robel/core/tests/components/nmap_tracker/test_scanner.py:365> cb=[_run_until_complete_cb() at /usr/lib/python3.14/asyncio/base_events.py:181] created at /usr/lib/python3.14/asyncio/runners.py:109> took 65.000 seconds
=========================== short test summary info ============================
FAILED tests/components/nmap_tracker/test_scanner.py::test_device_offline_consider_home
1 failed, 9 passed in 11.83s
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

### f) Rerun the tests against the restored code: 10 passed

```text
$ pytest tests/components/nmap_tracker/test_scanner.py -q -p no:cacheprovider
..........                                                               [100%]
10 passed in 9.96s
```
