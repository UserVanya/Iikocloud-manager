"""Unit tests for Organizations domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    GetOrganizationsRequest,
    GetOrganizationsResponse,
    OrganizationsSettingsRequest,
    OrganizationsSettingsResponse,
)

from iikocloud.api_client_manager import IikoCloudApiClientManager
from iikocloud.config_reader import MethodRateLimitsSettings
from iikocloud.mixins._base import ApiCredentials, ApiMethod, MethodRateLimits
from iikocloud.rate_limiter import GlobalRateLimiter
from iikocloud.token_manager import TokenManager

pytestmark = pytest.mark.unit

APP_ID = "00000000-0000-0000-0000-000000000001"


def _credentials() -> ApiCredentials:
    """Build v2 ApiCredentials for organization tests."""
    return ApiCredentials(
        api_key="test-api-key",
        app_id=APP_ID,
        client_secret="test-client-secret",
    )


def _limits() -> MethodRateLimits:
    """Default MethodRateLimits from settings defaults."""
    return MethodRateLimits.from_settings(MethodRateLimitsSettings())


@pytest.fixture(autouse=True)
async def cleanup_singletons() -> None:
    """Reset Multitone registries between tests."""
    await IikoCloudApiClientManager.close_all()
    yield
    await IikoCloudApiClientManager.close_all()
    GlobalRateLimiter.reset_instance()
    await TokenManager.close_all()


async def _manager_with_mock_orgs_api() -> tuple[
    IikoCloudApiClientManager, MagicMock
]:
    """Create manager with mocked TokenManager and OrganizationsApi."""
    manager = await IikoCloudApiClientManager.get_instance(
        _credentials(), _limits()
    )

    mock_token_manager = MagicMock()
    mock_token_manager.token_version = 1
    manager._token_manager = mock_token_manager

    mock_api = MagicMock()
    manager._organizations_api = mock_api
    return manager, mock_api


async def test_get_organizations_calls_api_with_request() -> None:
    """get_organizations delegates to SDK with the given request."""
    manager, mock_api = await _manager_with_mock_orgs_api()

    mock_response = MagicMock(spec=GetOrganizationsResponse)
    mock_api.get_organizations = AsyncMock(return_value=mock_response)

    request = GetOrganizationsRequest(
        organization_ids=[UUID("12345678-1234-1234-1234-123456789abc")]
    )
    result = await manager.get_organizations(request)

    assert result is mock_response
    mock_api.get_organizations.assert_awaited_once_with(
        get_organizations_request=request
    )


async def test_get_organizations_defaults_empty_request() -> None:
    """get_organizations() without request builds empty GetOrganizationsRequest."""
    manager, mock_api = await _manager_with_mock_orgs_api()

    mock_response = MagicMock(spec=GetOrganizationsResponse)
    mock_api.get_organizations = AsyncMock(return_value=mock_response)

    result = await manager.get_organizations()

    assert result is mock_response
    mock_api.get_organizations.assert_awaited_once()
    call_kwargs = mock_api.get_organizations.await_args.kwargs
    assert isinstance(call_kwargs["get_organizations_request"], GetOrganizationsRequest)


async def test_get_organization_settings_calls_api_with_request() -> None:
    """get_organization_settings delegates to SDK with the given request."""
    manager, mock_api = await _manager_with_mock_orgs_api()

    mock_response = MagicMock(spec=OrganizationsSettingsResponse)
    mock_api.get_organization_settings = AsyncMock(return_value=mock_response)

    request = OrganizationsSettingsRequest(
        organization_ids=[UUID("12345678-1234-1234-1234-123456789abc")]
    )
    result = await manager.get_organization_settings(request)

    assert result is mock_response
    mock_api.get_organization_settings.assert_awaited_once_with(
        organizations_settings_request=request
    )


async def test_get_organization_settings_defaults_empty_request() -> None:
    """get_organization_settings() without request builds empty request."""
    manager, mock_api = await _manager_with_mock_orgs_api()

    mock_response = MagicMock(spec=OrganizationsSettingsResponse)
    mock_api.get_organization_settings = AsyncMock(return_value=mock_response)

    result = await manager.get_organization_settings()

    assert result is mock_response
    mock_api.get_organization_settings.assert_awaited_once()
    call_kwargs = mock_api.get_organization_settings.await_args.kwargs
    assert isinstance(
        call_kwargs["organizations_settings_request"],
        OrganizationsSettingsRequest,
    )


async def test_get_organizations_uses_execute_with_retry() -> None:
    """get_organizations routes through execute_with_retry with GET_ORGANIZATIONS."""
    manager, mock_api = await _manager_with_mock_orgs_api()
    mock_api.get_organizations = AsyncMock(return_value=MagicMock())

    async def _passthrough(method, api_call):  # noqa: ANN001
        return await api_call()

    manager.execute_with_retry = AsyncMock(side_effect=_passthrough)

    await manager.get_organizations()

    manager.execute_with_retry.assert_awaited_once()
    method_arg = manager.execute_with_retry.await_args.args[0]
    assert method_arg is ApiMethod.GET_ORGANIZATIONS
