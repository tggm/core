"""Test the Rointe config flow."""
from unittest.mock import patch

from rointesdk.rointe_api import ApiResponse

from homeassistant import config_entries, data_entry_flow
from homeassistant.components.rointe.const import (
    CONF_INSTALLATION,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
)

USERNAME = "rointe@home-assistant.com"
PASSWORD = "test-password"
LOCAL_ID = "local-1234"


async def test_user_flow(hass):
    """Test the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.rointe.config_flow.RointeAPI.initialize_authentication",
        return_value=ApiResponse(True, None, None),
    ), patch(
        "homeassistant.components.rointe.config_flow.RointeAPI.is_logged_in",
        return_value=True,
    ), patch(
        "homeassistant.components.rointe.config_flow.RointeAPI.get_local_id",
        return_value=ApiResponse(True, LOCAL_ID, None),
    ), patch(
        "homeassistant.components.rointe.config_flow.RointeAPI.get_installations",
    ) as mock_get_installations:
        # Prepare mocks.
        mock_get_installations.return_value = ApiResponse(
            True, {"install-0001": "My Home", "install-0002": "Summer Place"}, None
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )
        await hass.async_block_till_done()

        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["step_id"] == "installation"
        assert result2["errors"] == {}

        data_schema = result2.get("data_schema", None)
        assert data_schema and data_schema.schema

        in_schema = data_schema.schema[CONF_INSTALLATION]

        assert in_schema.container["install-0001"] == "My Home"
        assert in_schema.container["install-0002"] == "Summer Place"

    # Move to the next step, selecting the installation.
    with patch(
        "homeassistant.components.rointe.async_setup_entry",
        return_value=True,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTALLATION: "install-0001"},
        )

        assert result3["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY


async def test_invalid_local_id(hass):
    """Test the user flow when an error retrieving the local_id occurs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.rointe.config_flow.RointeAPI.initialize_authentication",
        return_value=ApiResponse(True, None, None),
    ), patch(
        "homeassistant.components.rointe.config_flow.RointeAPI.is_logged_in",
        return_value=True,
    ), patch(
        "homeassistant.components.rointe.config_flow.RointeAPI.get_local_id",
        return_value=ApiResponse(False, None, "Network Error"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )
        await hass.async_block_till_done()

        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["step_id"] == "user"
        assert result2["errors"] == {"base": "Network Error"}


async def test_invalid_installations(hass):
    """Test the user flow when an error retrieving the installations occurs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.rointe.config_flow.RointeAPI.initialize_authentication",
        return_value=ApiResponse(True, None, None),
    ), patch(
        "homeassistant.components.rointe.config_flow.RointeAPI.is_logged_in",
        return_value=True,
    ), patch(
        "homeassistant.components.rointe.config_flow.RointeAPI.get_local_id",
        return_value=ApiResponse(True, LOCAL_ID, None),
    ), patch(
        "homeassistant.components.rointe.config_flow.RointeAPI.get_installations",
        return_value=ApiResponse(
            False, LOCAL_ID, "No response from API in get_installations()"
        ),
    ):

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )
        await hass.async_block_till_done()

        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["step_id"] == "user"
        assert result2["errors"] == {
            "base": "No response from API in get_installations()"
        }


async def test_user_flow_invalid_password(hass):
    """Test user flow with invalid password."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.rointe.config_flow.RointeAPI.initialize_authentication",
        return_value=ApiResponse(False, None, "invalid_auth"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "invalid_auth"}
