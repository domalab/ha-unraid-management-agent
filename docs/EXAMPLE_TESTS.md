# Example Test Files
## Unraid Management Agent Integration

This document provides complete, production-ready example test files demonstrating best practices for testing Home Assistant custom components.

---

## 1. `tests/conftest.py` - Shared Fixtures

```python
"""Fixtures for Unraid Management Agent tests."""
from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.unraid_management_agent.const import DOMAIN

from .const import MOCK_CONFIG, MOCK_SYSTEM_DATA, MOCK_ARRAY_DATA, MOCK_DISKS_DATA


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.unraid_management_agent.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_api_client() -> Generator[MagicMock, None, None]:
    """Mock UnraidAPIClient."""
    with patch(
        "custom_components.unraid_management_agent.api_client.UnraidAPIClient",
        autospec=True,
    ) as mock_client:
        client = mock_client.return_value
        client.get_system_info = AsyncMock(return_value=MOCK_SYSTEM_DATA)
        client.get_array_status = AsyncMock(return_value=MOCK_ARRAY_DATA)
        client.get_disks = AsyncMock(return_value=MOCK_DISKS_DATA)
        client.get_containers = AsyncMock(return_value=[])
        client.get_vms = AsyncMock(return_value=[])
        client.get_ups_status = AsyncMock(return_value={})
        client.get_gpu_metrics = AsyncMock(return_value=[])
        client.get_network_interfaces = AsyncMock(return_value=[])
        client.close = AsyncMock()
        yield client


@pytest.fixture
def mock_websocket_client() -> Generator[MagicMock, None, None]:
    """Mock UnraidWebSocketClient."""
    with patch(
        "custom_components.unraid_management_agent.websocket_client.UnraidWebSocketClient",
        autospec=True,
    ) as mock_ws:
        ws_client = mock_ws.return_value
        ws_client.connect = AsyncMock()
        ws_client.disconnect = AsyncMock()
        ws_client.is_connected = False
        yield ws_client


@pytest.fixture
async def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock config entry."""
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.const import CONF_HOST, CONF_PORT

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 8043,
        },
        options={
            "update_interval": 30,
            "enable_websocket": True,
        },
        unique_id="192.168.1.100:8043",
    )
    entry.add_to_hass(hass)
    return entry


class MockConfigEntry:
    """Mock ConfigEntry for testing."""

    def __init__(self, domain, data, options=None, unique_id=None):
        self.domain = domain
        self.data = data
        self.options = options or {}
        self.unique_id = unique_id
        self.entry_id = "test_entry_id"
        self.title = "Test Unraid"
        self.state = "loaded"

    def add_to_hass(self, hass):
        """Add entry to hass."""
        hass.config_entries._entries[self.entry_id] = self
```

---

## 2. `tests/const.py` - Test Constants

```python
"""Constants for Unraid Management Agent tests."""
from homeassistant.const import CONF_HOST, CONF_PORT

# Mock configuration
MOCK_CONFIG = {
    CONF_HOST: "192.168.1.100",
    CONF_PORT: 8043,
}

# Mock API responses
MOCK_SYSTEM_DATA = {
    "hostname": "unraid-test",
    "cpu_usage_percent": 25.5,
    "ram_usage_percent": 45.2,
    "cpu_temp_celsius": 55.0,
    "motherboard_temp_celsius": 42.0,
    "cpu_model": "Intel Core i7-9700K",
    "ram_total_bytes": 34359738368,  # 32 GB
    "uptime_seconds": 86400,  # 1 day
    "fans": [
        {"name": "CPU Fan", "rpm": 1200},
        {"name": "System Fan", "rpm": 800},
    ],
}

MOCK_ARRAY_DATA = {
    "state": "STARTED",
    "size_bytes": 16000000000000,
    "used_bytes": 8000000000000,
    "free_bytes": 8000000000000,
    "num_disks": 4,
    "num_data_disks": 3,
    "num_parity_disks": 1,
    "parity_check_status": "idle",
}

MOCK_DISKS_DATA = [
    {
        "id": "WDC_WD80EFAX_12345",
        "device": "sdb",
        "name": "disk1",
        "role": "data",
        "size_bytes": 8000000000000,
        "used_bytes": 4000000000000,
        "free_bytes": 4000000000000,
        "temperature_celsius": 35,
        "spin_state": "active",
        "status": "DISK_OK",
        "filesystem": "xfs",
        "mount_point": "/mnt/disk1",
    },
]

MOCK_UPS_DATA = {
    "status": "ONLINE",
    "battery_charge_percent": 100,
    "runtime_left_seconds": 3600,
    "power_watts": 150.5,
    "load_percent": 25,
    "model": "APC Back-UPS 1500",
}
```

---

## 3. `tests/test_config_flow.py` - Config Flow Tests

```python
"""Test the Unraid Management Agent config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.unraid_management_agent.const import DOMAIN

from .const import MOCK_CONFIG, MOCK_SYSTEM_DATA


async def test_form_user_success(hass: HomeAssistant, mock_api_client) -> None:
    """Test successful user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "custom_components.unraid_management_agent.config_flow.UnraidAPIClient",
        return_value=mock_api_client,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_CONFIG,
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Unraid (unraid-test)"
    assert result2["data"] == MOCK_CONFIG


async def test_form_user_cannot_connect(hass: HomeAssistant, mock_api_client) -> None:
    """Test connection error in user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_api_client.get_system_info.side_effect = ConnectionError("Connection failed")

    with patch(
        "custom_components.unraid_management_agent.config_flow.UnraidAPIClient",
        return_value=mock_api_client,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_CONFIG,
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_user_timeout(hass: HomeAssistant, mock_api_client) -> None:
    """Test timeout error in user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_api_client.get_system_info.side_effect = TimeoutError("Timeout")

    with patch(
        "custom_components.unraid_management_agent.config_flow.UnraidAPIClient",
        return_value=mock_api_client,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_CONFIG,
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "timeout"}


async def test_form_user_already_configured(
    hass: HomeAssistant, mock_config_entry, mock_api_client
) -> None:
    """Test aborting if already configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.unraid_management_agent.config_flow.UnraidAPIClient",
        return_value=mock_api_client,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_CONFIG,
        )

    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant, mock_config_entry) -> None:
    """Test options flow."""
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "update_interval": 60,
            "enable_websocket": False,
        },
    )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == {
        "update_interval": 60,
        "enable_websocket": False,
    }
```

---

## 4. `tests/test_api_client.py` - API Client Tests

```python
"""Test the Unraid API client."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from homeassistant.core import HomeAssistant

from custom_components.unraid_management_agent.api_client import UnraidAPIClient

from .const import MOCK_SYSTEM_DATA


async def test_get_system_info_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful system info retrieval."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/system",
        json=MOCK_SYSTEM_DATA,
    )

    client = UnraidAPIClient("192.168.1.100", 8043, hass.helpers.aiohttp_client.async_get_clientsession())
    result = await client.get_system_info()

    assert result == MOCK_SYSTEM_DATA


async def test_get_system_info_timeout(hass: HomeAssistant, aioclient_mock) -> None:
    """Test timeout error."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/system",
        exc=asyncio.TimeoutError(),
    )

    client = UnraidAPIClient("192.168.1.100", 8043, hass.helpers.aiohttp_client.async_get_clientsession())

    with pytest.raises(TimeoutError):
        await client.get_system_info()


async def test_get_system_info_connection_error(hass: HomeAssistant, aioclient_mock) -> None:
    """Test connection error."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/system",
        exc=aiohttp.ClientError(),
    )

    client = UnraidAPIClient("192.168.1.100", 8043, hass.helpers.aiohttp_client.async_get_clientsession())

    with pytest.raises(ConnectionError):
        await client.get_system_info()


async def test_get_system_info_invalid_json(hass: HomeAssistant, aioclient_mock) -> None:
    """Test invalid JSON response."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/system",
        text="invalid json",
    )

    client = UnraidAPIClient("192.168.1.100", 8043, hass.helpers.aiohttp_client.async_get_clientsession())

    with pytest.raises(ValueError):
        await client.get_system_info()
```

---

## 5. `tests/test_sensor.py` - Sensor Platform Tests

```python
"""Test the Unraid Management Agent sensor platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.unraid_management_agent.const import DOMAIN

from .const import MOCK_CONFIG, MOCK_SYSTEM_DATA


async def test_cpu_usage_sensor(
    hass: HomeAssistant, mock_config_entry, mock_api_client
) -> None:
    """Test CPU usage sensor."""
    with patch(
        "custom_components.unraid_management_agent.api_client.UnraidAPIClient",
        return_value=mock_api_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "sensor.unraid_test_cpu_usage"
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.state == "25.5"
    assert state.attributes["unit_of_measurement"] == PERCENTAGE
    assert state.attributes["device_class"] == SensorDeviceClass.POWER_FACTOR
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT


async def test_cpu_temperature_sensor(
    hass: HomeAssistant, mock_config_entry, mock_api_client
) -> None:
    """Test CPU temperature sensor."""
    with patch(
        "custom_components.unraid_management_agent.api_client.UnraidAPIClient",
        return_value=mock_api_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "sensor.unraid_test_cpu_temperature"
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.state == "55.0"
    assert state.attributes["unit_of_measurement"] == UnitOfTemperature.CELSIUS
    assert state.attributes["device_class"] == SensorDeviceClass.TEMPERATURE


async def test_sensor_unique_ids(
    hass: HomeAssistant, mock_config_entry, mock_api_client
) -> None:
    """Test that all sensors have unique IDs."""
    with patch(
        "custom_components.unraid_management_agent.api_client.UnraidAPIClient",
        return_value=mock_api_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, mock_config_entry.entry_id)

    unique_ids = [entry.unique_id for entry in entries if entry.domain == "sensor"]

    # Check no duplicates
    assert len(unique_ids) == len(set(unique_ids))

    # Check format
    for unique_id in unique_ids:
        assert unique_id.startswith(f"{mock_config_entry.entry_id}_")


async def test_sensor_device_info(
    hass: HomeAssistant, mock_config_entry, mock_api_client
) -> None:
    """Test that sensors have correct device info."""
    with patch(
        "custom_components.unraid_management_agent.api_client.UnraidAPIClient",
        return_value=mock_api_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "sensor.unraid_test_cpu_usage"
    entity_registry = er.async_get(hass)
    entry = entity_registry.async_get(entity_id)

    assert entry is not None
    assert entry.device_id is not None

    device_registry = dr.async_get(hass)
    device = device_registry.async_get(entry.device_id)

    assert device is not None
    assert device.name == "Unraid (unraid-test)"
    assert device.manufacturer == "Lime Technology"
    assert device.model == "Unraid Server"
```

---

## 6. `tests/test_init.py` - Integration Setup Tests

```python
"""Test the Unraid Management Agent integration setup."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.unraid_management_agent.const import DOMAIN

from .const import MOCK_CONFIG


async def test_setup_entry_success(
    hass: HomeAssistant, mock_config_entry, mock_api_client
) -> None:
    """Test successful setup of config entry."""
    with patch(
        "custom_components.unraid_management_agent.api_client.UnraidAPIClient",
        return_value=mock_api_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]


async def test_setup_entry_connection_error(
    hass: HomeAssistant, mock_config_entry, mock_api_client
) -> None:
    """Test setup failure due to connection error."""
    mock_api_client.health_check.side_effect = ConnectionError("Connection failed")

    with patch(
        "custom_components.unraid_management_agent.api_client.UnraidAPIClient",
        return_value=mock_api_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant, mock_config_entry, mock_api_client
) -> None:
    """Test unloading a config entry."""
    with patch(
        "custom_components.unraid_management_agent.api_client.UnraidAPIClient",
        return_value=mock_api_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_reload_entry(
    hass: HomeAssistant, mock_config_entry, mock_api_client
) -> None:
    """Test reloading a config entry."""
    with patch(
        "custom_components.unraid_management_agent.api_client.UnraidAPIClient",
        return_value=mock_api_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED

    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
```

---

## 7. Running the Tests

### Install Dependencies

```bash
pip install -r requirements_test.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_config_flow.py
```

### Run with Coverage Report

```bash
pytest --cov --cov-report=html
```

Then open `htmlcov/index.html` in your browser.

### Run Specific Test

```bash
pytest tests/test_config_flow.py::test_form_user_success -v
```

### Run Tests in Parallel (faster)

```bash
pytest -n auto
```

---

## 8. Coverage Goals

### Minimum Coverage Targets

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| `config_flow.py` | ≥95% | High |
| `api_client.py` | ≥90% | High |
| `__init__.py` | ≥90% | High |
| `sensor.py` | ≥85% | Medium |
| `binary_sensor.py` | ≥85% | Medium |
| `switch.py` | ≥85% | Medium |
| `button.py` | ≥85% | Medium |
| `websocket_client.py` | ≥80% | Medium |
| `repairs.py` | ≥80% | Low |
| **Overall** | **≥90%** | **Required** |

---

## 9. Continuous Integration

Once tests are implemented, add this to your PR workflow:

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements_test.txt
      - run: pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
```

This ensures all PRs are tested automatically and coverage is tracked over time.

---

## Summary

These example test files demonstrate:

✅ **Proper test structure** with fixtures and constants
✅ **Mocking external dependencies** (API, WebSocket)
✅ **Testing success and failure paths**
✅ **Testing entity properties** (unique IDs, device info)
✅ **Testing config flows** (user flow, options flow, errors)
✅ **Testing API client** (success, timeout, connection errors)
✅ **Testing integration setup** (load, unload, reload)

Implement these tests to achieve **≥90% coverage** and qualify for **Silver tier** quality rating!


