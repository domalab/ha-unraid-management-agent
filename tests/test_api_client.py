"""Test the Unraid API client."""

from __future__ import annotations

import aiohttp
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.unraid_management_agent.api_client import \
    UnraidAPIClient

from .const import (MOCK_ARRAY_DATA, MOCK_CONTAINERS_DATA, MOCK_DISKS_DATA,
                    MOCK_GPU_DATA, MOCK_HEALTH_CHECK, MOCK_NETWORK_DATA,
                    MOCK_SYSTEM_DATA, MOCK_UPS_DATA, MOCK_VMS_DATA)


@pytest.fixture
def api_client(hass: HomeAssistant) -> UnraidAPIClient:
    """Create API client instance."""
    session = async_get_clientsession(hass)
    return UnraidAPIClient("192.168.1.100", 8043, session)


async def test_health_check_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful health check."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/health",
        json=MOCK_HEALTH_CHECK,
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.health_check()

    assert result == MOCK_HEALTH_CHECK


async def test_get_system_info_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful system info retrieval."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/system",
        json=MOCK_SYSTEM_DATA,
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.get_system_info()

    assert result == MOCK_SYSTEM_DATA
    assert result["hostname"] == "unraid-test"
    assert result["cpu_usage_percent"] == 25.5


async def test_get_array_status_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful array status retrieval."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/array",
        json=MOCK_ARRAY_DATA,
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.get_array_status()

    assert result == MOCK_ARRAY_DATA
    assert result["state"] == "STARTED"


async def test_get_disks_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful disks retrieval."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/disks",
        json=MOCK_DISKS_DATA,
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.get_disks()

    assert result == MOCK_DISKS_DATA
    assert len(result) == 2
    assert result[0]["device"] == "sdb"


async def test_get_containers_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful containers retrieval."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/docker",
        json=MOCK_CONTAINERS_DATA,
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.get_containers()

    assert result == MOCK_CONTAINERS_DATA
    assert len(result) == 2


async def test_get_vms_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful VMs retrieval."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/vm",
        json=MOCK_VMS_DATA,
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.get_vms()

    assert result == MOCK_VMS_DATA
    assert len(result) == 2


async def test_get_ups_status_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful UPS status retrieval."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/ups",
        json=MOCK_UPS_DATA,
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.get_ups_status()

    assert result == MOCK_UPS_DATA
    assert result["battery_charge_percent"] == 100


async def test_get_gpu_metrics_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful GPU metrics retrieval."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/gpu",
        json=MOCK_GPU_DATA,
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.get_gpu_metrics()

    assert result == MOCK_GPU_DATA
    assert len(result) == 1


async def test_get_network_interfaces_success(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """Test successful network interfaces retrieval."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/network",
        json=MOCK_NETWORK_DATA,
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.get_network_interfaces()

    assert result == MOCK_NETWORK_DATA
    assert len(result) == 2


async def test_timeout_error(hass: HomeAssistant, aioclient_mock) -> None:
    """Test timeout error."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/system",
        exc=TimeoutError(),
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))

    with pytest.raises(TimeoutError):
        await client.get_system_info()


async def test_connection_error(hass: HomeAssistant, aioclient_mock) -> None:
    """Test connection error."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/system",
        exc=aiohttp.ClientError(),
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))

    with pytest.raises(ConnectionError):
        await client.get_system_info()


async def test_invalid_json(hass: HomeAssistant, aioclient_mock) -> None:
    """Test invalid JSON response."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/system",
        text="invalid json",
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))

    with pytest.raises(ValueError):
        await client.get_system_info()


async def test_empty_response(hass: HomeAssistant, aioclient_mock) -> None:
    """Test empty response."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/system",
        text="",
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))

    with pytest.raises(ValueError):
        await client.get_system_info()


async def test_http_error_404(hass: HomeAssistant, aioclient_mock) -> None:
    """Test HTTP 404 error."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/system",
        status=404,
        json={"error": "Not found"},
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))

    with pytest.raises(ConnectionError):
        await client.get_system_info()


async def test_http_error_500(hass: HomeAssistant, aioclient_mock) -> None:
    """Test HTTP 500 error."""
    aioclient_mock.get(
        "http://192.168.1.100:8043/api/v1/system",
        status=500,
        json={"error": "Server error"},
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))

    with pytest.raises(ConnectionError):
        await client.get_system_info()


async def test_start_array_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful array start."""
    aioclient_mock.post(
        "http://192.168.1.100:8043/api/v1/array/start",
        json={"success": True},
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.start_array()

    assert result == {"success": True}


async def test_stop_array_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful array stop."""
    aioclient_mock.post(
        "http://192.168.1.100:8043/api/v1/array/stop",
        json={"success": True},
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.stop_array()

    assert result == {"success": True}


async def test_start_container_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful container start."""
    aioclient_mock.post(
        "http://192.168.1.100:8043/api/v1/docker/plex/start",
        json={"success": True},
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.start_container("plex")

    assert result == {"success": True}


async def test_stop_container_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful container stop."""
    aioclient_mock.post(
        "http://192.168.1.100:8043/api/v1/docker/plex/stop",
        json={"success": True},
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.stop_container("plex")

    assert result == {"success": True}


async def test_start_vm_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful VM start."""
    aioclient_mock.post(
        "http://192.168.1.100:8043/api/v1/vm/windows-10/start",
        json={"success": True},
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.start_vm("windows-10")

    assert result == {"success": True}


async def test_stop_vm_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test successful VM stop."""
    aioclient_mock.post(
        "http://192.168.1.100:8043/api/v1/vm/windows-10/stop",
        json={"success": True},
    )

    client = UnraidAPIClient("192.168.1.100", 8043, async_get_clientsession(hass))
    result = await client.stop_vm("windows-10")

    assert result == {"success": True}
