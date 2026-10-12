# nmap_tracker Baseline Results

Baseline captured before any refactoring. No production code was changed.

## Environment

All commands were run from the repository root (`/mnt/c/Users/Robel/core`) in WSL2 Ubuntu,
using the virtual environment `~/ha-venv` (Home Assistant does not run on native Windows).

```
$ python --version; pytest --version; ruff --version; uname -sr
Python 3.14.4
pytest 9.0.3
ruff 0.16.6
Linux 6.6.87.2-microsoft-standard-WSL2
```

Branch: `dev`, working tree clean at the time of the run.

## 1. Commit hash

```
$ git rev-parse HEAD
162089a8740ec541cbacfb4930cb25fc5fcd5136
```

## 2. Existing tests

**Result: 13 passed, 0 failed** (exit code 0).

```
$ pytest tests/components/nmap_tracker -v
============================= test session starts ==============================
platform linux -- Python 3.14.4, pytest-9.0.3, pluggy-1.6.0 -- /home/robely/ha-venv/bin/python3
cachedir: .pytest_cache
rootdir: /mnt/c/Users/Robel/core
configfile: pyproject.toml
plugins: asyncio-1.4.0, socket-0.8.1, github-actions-annotate-failures-0.4.2, aiohttp-1.1.1, requests-mock-1.12.1, xdist-3.8.0, syrupy-6.0.0, timeout-2.4.0, respx-0.23.1, platformdirs-4.13.0, pytest_freezer-0.4.9, unordered-0.8.0, cov-7.1.0, anyio-4.13.0, sugar-1.1.1, picked-0.5.1
asyncio: mode=Mode.AUTO, debug=True, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 13 items

tests/components/nmap_tracker/test_config_flow.py::test_form[hosts0] PASSED [  7%]
tests/components/nmap_tracker/test_config_flow.py::test_form[hosts1] PASSED [ 15%]
tests/components/nmap_tracker/test_config_flow.py::test_form[hosts2] PASSED [ 23%]
tests/components/nmap_tracker/test_config_flow.py::test_form_range PASSED [ 30%]
tests/components/nmap_tracker/test_config_flow.py::test_form_invalid_hosts PASSED [ 38%]
tests/components/nmap_tracker/test_config_flow.py::test_form_already_configured PASSED [ 46%]
tests/components/nmap_tracker/test_config_flow.py::test_form_invalid_ip_excludes PASSED [ 53%]
tests/components/nmap_tracker/test_config_flow.py::test_form_invalid_mac_excludes[mac_excludes0] PASSED [ 61%]
tests/components/nmap_tracker/test_config_flow.py::test_form_invalid_mac_excludes[mac_excludes1] PASSED [ 69%]
tests/components/nmap_tracker/test_config_flow.py::test_form_invalid_mac_excludes[mac_excludes2] PASSED [ 76%]
tests/components/nmap_tracker/test_config_flow.py::test_options_flow PASSED [ 84%]
tests/components/nmap_tracker/test_init.py::test_migrate_entry PASSED    [ 92%]
tests/components/nmap_tracker/test_init.py::test_migrate_entry_fails_on_downgrade PASSED [100%]

============================== 13 passed in 8.98s ==============================
```

## 3. Coverage

```
$ pytest tests/components/nmap_tracker --cov=homeassistant.components.nmap_tracker --cov-report=term-missing
============================= test session starts ==============================
platform linux -- Python 3.14.4, pytest-9.0.3, pluggy-1.6.0
rootdir: /mnt/c/Users/Robel/core
configfile: pyproject.toml
plugins: asyncio-1.4.0, socket-0.8.1, github-actions-annotate-failures-0.4.2, aiohttp-1.1.1, requests-mock-1.12.1, xdist-3.8.0, syrupy-6.0.0, timeout-2.4.0, respx-0.23.1, platformdirs-4.13.0, pytest_freezer-0.4.9, unordered-0.8.0, cov-7.1.0, anyio-4.13.0, sugar-1.1.1, picked-0.5.1
asyncio: mode=Mode.AUTO, debug=True, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 13 items

tests/components/nmap_tracker/test_config_flow.py ...........            [ 84%]
tests/components/nmap_tracker/test_init.py ..                            [100%]

================================ tests coverage ================================
_______________ coverage: platform linux, python 3.14.4-final-0 ________________

Name                                                      Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------------
homeassistant/components/nmap_tracker/__init__.py           229    116    49%   51, 56-60, 153-155, 160, 206, 240, 244-254, 258-280, 284-299, 305-320, 324-348, 353-388, 392-443
homeassistant/components/nmap_tracker/config_flow.py        126      0   100%
homeassistant/components/nmap_tracker/const.py               13      0   100%
homeassistant/components/nmap_tracker/device_tracker.py      69     20    71%   33, 38, 60-63, 68, 74, 80, 86, 92, 98, 104-106, 111, 117, 127-128, 133
---------------------------------------------------------------------------------------
TOTAL                                                       437    136    69%
============================== 13 passed in 8.64s ==============================
```

### Uncovered code in `__init__.py` (49%)

| Lines | Function | What is not covered |
|---|---|---|
| 51 | `short_hostname` | Whole body |
| 56-60 | `human_readable_name` | Whole body (hostname / vendor / fallback branches) |
| 153-155 | `_async_untrack_devices` | Loop body that removes tracked devices (the function is called, but no devices were tracked) |
| 160 | `signal_device_update` | Whole body |
| 206 | `NmapDeviceScanner.async_setup` | `consider_home` branch, taken only when `CONF_CONSIDER_HOME` is set |
| 240 | `NmapDeviceScanner._async_stop` | Whole body |
| 244-254 | `NmapDeviceScanner._async_start_scanner` | Whole body |
| 258-280 | `NmapDeviceScanner._build_options` | Whole body |
| 284-299 | `NmapDeviceScanner._async_scan_devices` | Whole body |
| 305-320 | `NmapDeviceScanner._async_mark_missing_devices_as_not_home` | Whole body |
| 324-348 | `NmapDeviceScanner._run_nmap_scan` | Whole body |
| 353-388 | `NmapDeviceScanner._async_device_offline` | Whole body |
| 392-443 | `NmapDeviceScanner._async_run_nmap_scan` | Whole body |

Covered: `async_setup_entry`, `async_unload_entry`, `async_migrate_entry`, `NmapDeviceScanner.__init__`,
most of `async_setup`, and the `signal_device_new` / `signal_device_missing` properties.
So the existing tests set the scanner up but never run a scan.

### Uncovered code in `device_tracker.py` (71%)

| Lines | Function | What is not covered |
|---|---|---|
| 33 | `async_setup_entry` → inner `device_new` | Callback body |
| 38 | `async_setup_entry` → inner `device_missing` | Callback body |
| 60-63 | `NmapTrackerEntity.__init__` | Whole body |
| 68 | `NmapTrackerEntity._device` | Property body |
| 74 | `NmapTrackerEntity.is_connected` | Property body |
| 80 | `NmapTrackerEntity.name` | Property body |
| 86 | `NmapTrackerEntity.unique_id` | Property body |
| 92 | `NmapTrackerEntity.ip_address` | Property body |
| 98 | `NmapTrackerEntity.mac_address` | Property body |
| 104-106 | `NmapTrackerEntity.hostname` | Property body |
| 111 | `NmapTrackerEntity.async_process_update` | Whole body |
| 117 | `NmapTrackerEntity.extra_state_attributes` | Property body |
| 127-128 | `NmapTrackerEntity.async_on_demand_update` | Whole body |
| 133 | `NmapTrackerEntity.async_added_to_hass` | Whole body |

Covered: platform `async_setup_entry` (connecting the dispatcher signals) plus the module-level and class definitions.
No `NmapTrackerEntity` is ever created during the tests.

## 4. Lint

**Result: no issues** (exit code 0).

```
$ ruff check homeassistant/components/nmap_tracker tests/components/nmap_tracker
All checks passed!
```
