"""Fixtures for Unraid Management Agent tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.unraid_management_agent.const import DOMAIN

from .const import (MOCK_ARRAY_DATA, MOCK_CONFIG, MOCK_CONTAINERS_DATA,
                    MOCK_DISKS_DATA, MOCK_GPU_DATA, MOCK_HEALTH_CHECK,
                    MOCK_NETWORK_DATA, MOCK_OPTIONS, MOCK_SYSTEM_DATA,
                    MOCK_UPS_DATA, MOCK_VMS_DATA)

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.unraid_management_agent.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_api_client() -> Generator[MagicMock]:
    """Mock UnraidAPIClient."""
    with patch(
        "custom_components.unraid_management_agent.api_client.UnraidAPIClient",
        autospec=True,
    ) as mock_client_class:
        client = mock_client_class.return_value

        # Mock all API methods
        client.health_check = AsyncMock(return_value=MOCK_HEALTH_CHECK)
        client.get_system_info = AsyncMock(return_value=MOCK_SYSTEM_DATA)
        client.get_array_status = AsyncMock(return_value=MOCK_ARRAY_DATA)
        client.get_disks = AsyncMock(return_value=MOCK_DISKS_DATA)
        client.get_containers = AsyncMock(return_value=MOCK_CONTAINERS_DATA)
        client.get_vms = AsyncMock(return_value=MOCK_VMS_DATA)
        client.get_ups_status = AsyncMock(return_value=MOCK_UPS_DATA)
        client.get_gpu_metrics = AsyncMock(return_value=MOCK_GPU_DATA)
        client.get_network_interfaces = AsyncMock(return_value=MOCK_NETWORK_DATA)

        # Mock control methods
        client.start_array = AsyncMock(return_value=True)
        client.stop_array = AsyncMock(return_value=True)
        client.start_parity_check = AsyncMock(return_value=True)
        client.stop_parity_check = AsyncMock(return_value=True)
        client.start_container = AsyncMock(return_value=True)
        client.stop_container = AsyncMock(return_value=True)
        client.restart_container = AsyncMock(return_value=True)
        client.start_vm = AsyncMock(return_value=True)
        client.stop_vm = AsyncMock(return_value=True)
        client.restart_vm = AsyncMock(return_value=True)

        # Mock cleanup
        client.close = AsyncMock()

        yield client


@pytest.fixture
def mock_websocket_client() -> Generator[MagicMock]:
    """Mock UnraidWebSocketClient."""
    with patch(
        "custom_components.unraid_management_agent.websocket_client.UnraidWebSocketClient",
        autospec=True,
    ) as mock_ws_class:
        ws_client = mock_ws_class.return_value
        ws_client.connect = AsyncMock()
        ws_client.disconnect = AsyncMock()
        ws_client.is_connected = False
        ws_client.start = AsyncMock()
        ws_client.stop = AsyncMock()
        yield ws_client


@pytest.fixture
async def mock_config_entry(hass: HomeAssistant) -> ConfigEntry:
    """Create a mock config entry."""
    entry = (
        hass.config_entries.async_entries(DOMAIN)[0]
        if hass.config_entries.async_entries(DOMAIN)
        else None
    )

    if not entry:
        # Use MockConfigEntry from pytest-homeassistant-custom-component
        from pytest_homeassistant_custom_component.common import \
            MockConfigEntry

        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Unraid (unraid-test)",
            data=MOCK_CONFIG,
            options=MOCK_OPTIONS,
            unique_id=f"{MOCK_CONFIG[CONF_HOST]}:{MOCK_CONFIG[CONF_PORT]}",
            entry_id="test_entry_id",
        )
        entry.add_to_hass(hass)

    return entry


@pytest.fixture
def mock_coordinator(hass: HomeAssistant, mock_api_client) -> Generator[MagicMock]:
    """Mock UnraidDataUpdateCoordinator."""
    with patch(
        "custom_components.unraid_management_agent.UnraidDataUpdateCoordinator",
        autospec=True,
    ) as mock_coordinator_class:
        coordinator = mock_coordinator_class.return_value
        coordinator.hass = hass
        coordinator.client = mock_api_client
        coordinator.data = {
            "system": MOCK_SYSTEM_DATA,
            "array": MOCK_ARRAY_DATA,
            "disks": MOCK_DISKS_DATA,
            "containers": MOCK_CONTAINERS_DATA,
            "vms": MOCK_VMS_DATA,
            "ups": MOCK_UPS_DATA,
            "gpu": MOCK_GPU_DATA,
            "network": MOCK_NETWORK_DATA,
        }
        coordinator.last_update_success = True
        coordinator.async_config_entry_first_refresh = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.async_start_websocket = AsyncMock()
        coordinator.async_stop_websocket = AsyncMock()
        yield coordinator


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    return
