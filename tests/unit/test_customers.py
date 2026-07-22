"""Unit tests for Customers domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    CreateOrUpdateCustomerRequest,
    CreateOrUpdateCustomerResponse,
    DeleteCustomersRequest,
    DeleteCustomersResponse,
    GetCustomerInfoByPhoneRequest,
    GetCustomerInfoResponse,
    RestoreCustomersRequest,
    RestoreCustomersResponse,
)

from iikocloud.api_client_manager import IikoCloudApiClientManager
from iikocloud.config_reader import MethodRateLimitsSettings
from iikocloud.mixins._base import ApiCredentials, ApiMethod, MethodRateLimits
from iikocloud.rate_limiter import GlobalRateLimiter
from iikocloud.token_manager import TokenManager

pytestmark = pytest.mark.unit

APP_ID = "00000000-0000-0000-0000-000000000001"
ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")


def _credentials() -> ApiCredentials:
    """Build v2 ApiCredentials for customer tests."""
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


async def _manager_with_mock_customers_api() -> tuple[
    IikoCloudApiClientManager, MagicMock
]:
    """Create manager with mocked TokenManager and CustomersApi."""
    manager = await IikoCloudApiClientManager.get_instance(
        _credentials(), _limits()
    )

    mock_token_manager = MagicMock()
    mock_token_manager.token_version = 1
    manager._token_manager = mock_token_manager

    mock_api = MagicMock()
    manager._customers_api = mock_api
    return manager, mock_api


async def test_create_or_update_customer_calls_api_with_request() -> None:
    """create_or_update_customer delegates to SDK with the given request."""
    manager, mock_api = await _manager_with_mock_customers_api()

    mock_response = MagicMock(spec=CreateOrUpdateCustomerResponse)
    mock_api.create_or_update_customer = AsyncMock(return_value=mock_response)

    request = CreateOrUpdateCustomerRequest(organization_id=ORG_ID)
    result = await manager.create_or_update_customer(request)

    assert result is mock_response
    mock_api.create_or_update_customer.assert_awaited_once_with(
        create_or_update_customer_request=request
    )


async def test_get_customer_info_calls_api_with_request() -> None:
    """get_customer_info delegates to SDK with the given request."""
    manager, mock_api = await _manager_with_mock_customers_api()

    mock_response = MagicMock(spec=GetCustomerInfoResponse)
    mock_api.get_customer_info = AsyncMock(return_value=mock_response)

    request = GetCustomerInfoByPhoneRequest(
        organization_id=ORG_ID,
        type="phone",
        phone="+79001234567",
    )
    result = await manager.get_customer_info(request)

    assert result is mock_response
    mock_api.get_customer_info.assert_awaited_once_with(
        get_customer_info_request=request
    )


async def test_delete_customers_calls_api_with_request() -> None:
    """delete_customers delegates to SDK with the given request."""
    manager, mock_api = await _manager_with_mock_customers_api()

    mock_response = MagicMock(spec=DeleteCustomersResponse)
    mock_api.delete_customers = AsyncMock(return_value=mock_response)

    request = DeleteCustomersRequest(
        organization_id=ORG_ID,
        customer_ids=[UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")],
    )
    result = await manager.delete_customers(request)

    assert result is mock_response
    mock_api.delete_customers.assert_awaited_once_with(
        delete_customers_request=request
    )


async def test_restore_customers_calls_api_with_request() -> None:
    """restore_customers delegates to SDK with the given request."""
    manager, mock_api = await _manager_with_mock_customers_api()

    mock_response = MagicMock(spec=RestoreCustomersResponse)
    mock_api.restore_customers = AsyncMock(return_value=mock_response)

    request = RestoreCustomersRequest(
        organization_id=ORG_ID,
        customer_ids=[UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")],
    )
    result = await manager.restore_customers(request)

    assert result is mock_response
    mock_api.restore_customers.assert_awaited_once_with(
        restore_customers_request=request
    )


async def test_get_customer_by_phone_builds_request_and_delegates() -> None:
    """get_customer_by_phone builds GetCustomerInfoByPhoneRequest and calls core."""
    manager, mock_api = await _manager_with_mock_customers_api()

    mock_response = MagicMock(spec=GetCustomerInfoResponse)
    mock_api.get_customer_info = AsyncMock(return_value=mock_response)

    result = await manager.get_customer_by_phone(ORG_ID, "+79001234567")

    assert result is mock_response
    mock_api.get_customer_info.assert_awaited_once()
    call_kwargs = mock_api.get_customer_info.await_args.kwargs
    request = call_kwargs["get_customer_info_request"]
    assert isinstance(request, GetCustomerInfoByPhoneRequest)
    assert request.organization_id == ORG_ID
    assert request.type == "phone"
    assert request.phone == "+79001234567"


async def test_get_customer_by_phone_accepts_str_organization_id() -> None:
    """get_customer_by_phone converts string organization_id to UUID."""
    manager, mock_api = await _manager_with_mock_customers_api()

    mock_api.get_customer_info = AsyncMock(return_value=MagicMock())

    await manager.get_customer_by_phone(str(ORG_ID), "+79001234567")

    call_kwargs = mock_api.get_customer_info.await_args.kwargs
    request = call_kwargs["get_customer_info_request"]
    assert request.organization_id == ORG_ID


async def test_create_or_update_customer_uses_execute_with_retry() -> None:
    """create_or_update_customer routes through execute_with_retry."""
    manager, mock_api = await _manager_with_mock_customers_api()
    mock_api.create_or_update_customer = AsyncMock(return_value=MagicMock())

    async def _passthrough(method, api_call):  # noqa: ANN001
        return await api_call()

    manager.execute_with_retry = AsyncMock(side_effect=_passthrough)

    await manager.create_or_update_customer(
        CreateOrUpdateCustomerRequest(organization_id=ORG_ID)
    )

    manager.execute_with_retry.assert_awaited_once()
    method_arg = manager.execute_with_retry.await_args.args[0]
    assert method_arg is ApiMethod.CREATE_OR_UPDATE_CUSTOMER
