# nmap_tracker Coverage and Lint After Characterization Tests

Run after adding `tests/components/nmap_tracker/test_scanner.py` (10 tests), with no production code changes.

- Commit: `162089a8740ec541cbacfb4930cb25fc5fcd5136` (branch `test_nmap`)
- Environment: WSL2 Ubuntu, Python 3.14.4, pytest 9.0.3, ruff 0.16.6, venv `~/ha-venv`, run from the repo root
- "Before" numbers come from `baseline_results.md` (13 tests, before `test_scanner.py` existed)

## Before / after coverage

| File | Stmts | Before: Miss | Before: Cover | After: Miss | After: Cover | Change |
|---|---|---|---|---|---|---|
| `__init__.py` | 229 | 116 | 49% | 33 | 86% | **+37 pts** |
| `config_flow.py` | 126 | 0 | 100% | 0 | 100% | none |
| `const.py` | 13 | 0 | 100% | 0 | 100% | none |
| `device_tracker.py` | 69 | 20 | 71% | 6 | 91% | **+20 pts** |
| **Total** | **437** | **136** | **69%** | **39** | **91%** | **+22 pts** |

Tests: 13 before, 23 after (all passing).

### Still uncovered

| File | Lines | Function | Why |
|---|---|---|---|
| `__init__.py` | 60 | `human_readable_name` | fallback name when there is no hostname and no vendor |
| `__init__.py` | 240 | `NmapDeviceScanner._async_stop` | out of scope |
| `__init__.py` | 244-254 | `NmapDeviceScanner._async_start_scanner` | out of scope |
| `__init__.py` | 269-270 | `NmapDeviceScanner._build_options` | branch for `home_interval` = 0 |
| `__init__.py` | 284-299 | `NmapDeviceScanner._async_scan_devices` | out of scope |
| `__init__.py` | 305-320 | `NmapDeviceScanner._async_mark_missing_devices_as_not_home` | out of scope |
| `__init__.py` | 342 | `NmapDeviceScanner._run_nmap_scan` | re-raise of a non-transient error, or after 16 transient errors |
| `__init__.py` | 357 | `NmapDeviceScanner._async_device_offline` | early return when the device was unloaded |
| `__init__.py` | 394 | `NmapDeviceScanner._async_run_nmap_scan` | early return while the scanner is stopping |
| `__init__.py` | 412-414 | `NmapDeviceScanner._async_run_nmap_scan` | up host with no MAC address found at all |
| `device_tracker.py` | 38 | `async_setup_entry` inner `device_missing` callback | out of scope |
| `device_tracker.py` | 111, 127-128 | `NmapTrackerEntity.async_process_update` / `async_on_demand_update` | out of scope |
| `device_tracker.py` | 117 | `NmapTrackerEntity.extra_state_attributes` | out of scope |
| `device_tracker.py` | 133 | `NmapTrackerEntity.async_added_to_hass` | out of scope |

"Out of scope" means the function is not part of the scan path the characterization tests target.
The other uncovered lines in `__init__.py` are edge cases of the scan path that the 10 tests deliberately
leave out. Part of `device_tracker.py` is covered indirectly, because the scans create real `NmapTrackerEntity` objects.

## Coverage
```text
$ pytest tests/components/nmap_tracker --cov=homeassistant.components.nmap_tracker --cov-report=term-missing
============================= test session starts ==============================
platform linux -- Python 3.14.4, pytest-9.0.3, pluggy-1.6.0
rootdir: /mnt/c/Users/Robel/core
configfile: pyproject.toml
plugins: asyncio-1.4.0, socket-0.8.1, github-actions-annotate-failures-0.4.2, aiohttp-1.1.1, requests-mock-1.12.1, xdist-3.8.0, syrupy-6.0.0, timeout-2.4.0, respx-0.23.1, platformdirs-4.13.0, pytest_freezer-0.4.9, unordered-0.8.0, cov-7.1.0, anyio-4.13.0, sugar-1.1.1, picked-0.5.1
asyncio: mode=Mode.AUTO, debug=True, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 23 items

tests/components/nmap_tracker/test_config_flow.py ...........            [ 47%]
tests/components/nmap_tracker/test_init.py ..                            [ 56%]
tests/components/nmap_tracker/test_scanner.py ..........                 [100%]

================================ tests coverage ================================
_______________ coverage: platform linux, python 3.14.4-final-0 ________________

Name                                                      Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------------
homeassistant/components/nmap_tracker/__init__.py           229     33    86%   60, 240, 244-254, 269-270, 284-299, 305-320, 342, 357, 394, 412-414
homeassistant/components/nmap_tracker/config_flow.py        126      0   100%
homeassistant/components/nmap_tracker/const.py               13      0   100%
homeassistant/components/nmap_tracker/device_tracker.py      69      6    91%   38, 111, 117, 127-128, 133
---------------------------------------------------------------------------------------
TOTAL                                                       437     39    91%
============================= 23 passed in 12.95s ==============================
```

## Lint

**Result:** no issues (exit code 0).

```text
$ ruff check homeassistant/components/nmap_tracker tests/components/nmap_tracker
All checks passed!
```
