"""Test the Unraid Management Agent config flow."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.unraid_management_agent.const import (
    CONF_ENABLE_WEBSOCKET,
    CONF_UPDATE_INTERVAL,
    DEFAULT_ENABLE_WEBSOCKET,
    DEFAULT_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    ERROR_CANNOT_CONNECT,
    ERROR_TIMEOUT,
    ERROR_UNKNOWN,
)

from .const import MOCK_CONFIG


async def test_form_user_success(hass: HomeAssistant, mock_api_client) -> None:
    """Test successful user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "user"

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
    # Data should only contain host and port, not options
    assert result2["data"][CONF_HOST] == MOCK_CONFIG[CONF_HOST]
    assert result2["data"][CONF_PORT] == MOCK_CONFIG[CONF_PORT]
    assert (
        result2["result"].unique_id
        == f"{MOCK_CONFIG[CONF_HOST]}:{MOCK_CONFIG[CONF_PORT]}"
    )


async def test_form_user_with_options(hass: HomeAssistant, mock_api_client) -> None:
    """Test user config flow with custom options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    user_input = {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 8043,
        CONF_UPDATE_INTERVAL: 60,
        CONF_ENABLE_WEBSOCKET: False,
    }

    with patch(
        "custom_components.unraid_management_agent.config_flow.UnraidAPIClient",
        return_value=mock_api_client,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input,
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_HOST] == "192.168.1.100"
    assert result2["data"][CONF_PORT] == 8043


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
    assert result2["errors"] == {"base": ERROR_CANNOT_CONNECT}


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
    assert result2["errors"] == {"base": ERROR_TIMEOUT}


async def test_form_user_unknown_error(hass: HomeAssistant, mock_api_client) -> None:
    """Test unknown error in user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_api_client.get_system_info.side_effect = Exception("Unknown error")

    with patch(
        "custom_components.unraid_management_agent.config_flow.UnraidAPIClient",
        return_value=mock_api_client,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_CONFIG,
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": ERROR_UNKNOWN}


async def test_form_user_already_configured(
    hass: HomeAssistant, mock_config_entry, mock_api_client
) -> None:
    """Test aborting if already configured."""
    # First entry already exists
    assert mock_config_entry.unique_id == "192.168.1.100:8043"

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
            CONF_UPDATE_INTERVAL: 60,
            CONF_ENABLE_WEBSOCKET: False,
        },
    )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"] == {
        CONF_UPDATE_INTERVAL: 60,
        CONF_ENABLE_WEBSOCKET: False,
    }


async def test_options_flow_default_values(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Test options flow with default values."""
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    # Check default values are shown
    schema = result["data_schema"].schema
    for key in schema:
        if key == CONF_UPDATE_INTERVAL:
            assert key.default() == DEFAULT_UPDATE_INTERVAL
        elif key == CONF_ENABLE_WEBSOCKET:
            assert key.default() == DEFAULT_ENABLE_WEBSOCKET


async def test_form_user_default_port(hass: HomeAssistant, mock_api_client) -> None:
    """Test that default port is used if not specified."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that default port is in the schema
    schema = result["data_schema"].schema
    for key in schema:
        if key == CONF_PORT:
            assert key.default() == DEFAULT_PORT


async def test_validate_input_success(hass: HomeAssistant, mock_api_client) -> None:
    """Test validate_input function with successful connection."""
    from custom_components.unraid_management_agent.config_flow import validate_input

    with (
        patch(
            "custom_components.unraid_management_agent.config_flow.UnraidAPIClient",
            return_value=mock_api_client,
        ),
        patch(
            "custom_components.unraid_management_agent.config_flow.async_get_clientsession",
            return_value=None,
        ),
    ):
        result = await validate_input(hass, MOCK_CONFIG)

    assert result["title"] == "Unraid (unraid-test)"
    assert result["hostname"] == "unraid-test"


async def test_validate_input_connection_error(
    hass: HomeAssistant, mock_api_client
) -> None:
    """Test validate_input function with connection error."""
    from custom_components.unraid_management_agent.config_flow import validate_input

    mock_api_client.get_system_info.side_effect = ConnectionError("Connection failed")

    with (
        patch(
            "custom_components.unraid_management_agent.config_flow.UnraidAPIClient",
            return_value=mock_api_client,
        ),
        patch(
            "custom_components.unraid_management_agent.config_flow.async_get_clientsession",
            return_value=None,
        ),
        pytest.raises(ConnectionError),
    ):
        await validate_input(hass, MOCK_CONFIG)


async def test_validate_input_timeout(hass: HomeAssistant, mock_api_client) -> None:
    """Test validate_input function with timeout."""
    from custom_components.unraid_management_agent.config_flow import validate_input

    mock_api_client.get_system_info.side_effect = TimeoutError("Timeout")

    with (
        patch(
            "custom_components.unraid_management_agent.config_flow.UnraidAPIClient",
            return_value=mock_api_client,
        ),
        patch(
            "custom_components.unraid_management_agent.config_flow.async_get_clientsession",
            return_value=None,
        ),
        pytest.raises(TimeoutError),
    ):
        await validate_input(hass, MOCK_CONFIG)
