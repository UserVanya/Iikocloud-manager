"""Unit tests for Dictionaries domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    CancelCausesRequest,
    CancelCausesResponse,
    DiscountsRequest,
    DiscountsResponse,
    OrderTypesRequest,
    OrderTypesResponse,
    PaymentTypesRequest,
    PaymentTypesResponse,
    RemovalTypesRequest,
    RemovalTypesResponse,
    TipsTypesResponse,
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
    """Build v2 ApiCredentials for dictionaries tests."""
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


async def _manager_with_mock_dictionaries_api() -> tuple[
    IikoCloudApiClientManager, MagicMock
]:
    """Create manager with mocked TokenManager and DictionariesApi."""
    manager = await IikoCloudApiClientManager.get_instance(
        _credentials(), _limits()
    )

    mock_token_manager = MagicMock()
    mock_token_manager.token_version = 1
    manager._token_manager = mock_token_manager

    mock_api = MagicMock()
    manager._dictionaries_api = mock_api
    return manager, mock_api


async def test_get_cancel_causes_calls_api_with_request() -> None:
    """get_cancel_causes delegates to SDK with CancelCausesRequest."""
    manager, mock_api = await _manager_with_mock_dictionaries_api()

    mock_response = MagicMock(spec=CancelCausesResponse)
    mock_api.get_cancel_causes = AsyncMock(return_value=mock_response)

    request = CancelCausesRequest(organization_ids=[ORG_ID])
    result = await manager.get_cancel_causes(request)

    assert result is mock_response
    mock_api.get_cancel_causes.assert_awaited_once_with(
        cancel_causes_request=request
    )


async def test_get_delivery_order_types_calls_api_with_request() -> None:
    """get_delivery_order_types delegates to SDK with OrderTypesRequest."""
    manager, mock_api = await _manager_with_mock_dictionaries_api()

    mock_response = MagicMock(spec=OrderTypesResponse)
    mock_api.get_delivery_order_types = AsyncMock(return_value=mock_response)

    request = OrderTypesRequest(organization_ids=[ORG_ID])
    result = await manager.get_delivery_order_types(request)

    assert result is mock_response
    mock_api.get_delivery_order_types.assert_awaited_once_with(
        order_types_request=request
    )


async def test_get_payment_types_calls_api_with_request() -> None:
    """get_payment_types delegates to SDK with PaymentTypesRequest."""
    manager, mock_api = await _manager_with_mock_dictionaries_api()

    mock_response = MagicMock(spec=PaymentTypesResponse)
    mock_api.get_payment_types = AsyncMock(return_value=mock_response)

    request = PaymentTypesRequest(organization_ids=[ORG_ID])
    result = await manager.get_payment_types(request)

    assert result is mock_response
    mock_api.get_payment_types.assert_awaited_once_with(
        payment_types_request=request
    )


async def test_get_discounts_calls_api_with_request() -> None:
    """get_discounts delegates to SDK with DiscountsRequest."""
    manager, mock_api = await _manager_with_mock_dictionaries_api()

    mock_response = MagicMock(spec=DiscountsResponse)
    mock_api.get_discounts = AsyncMock(return_value=mock_response)

    request = DiscountsRequest(organization_ids=[ORG_ID])
    result = await manager.get_discounts(request)

    assert result is mock_response
    mock_api.get_discounts.assert_awaited_once_with(
        discounts_request=request
    )


async def test_get_removal_types_calls_api_with_request() -> None:
    """get_removal_types delegates to SDK with RemovalTypesRequest."""
    manager, mock_api = await _manager_with_mock_dictionaries_api()

    mock_response = MagicMock(spec=RemovalTypesResponse)
    mock_api.get_removal_types = AsyncMock(return_value=mock_response)

    request = RemovalTypesRequest(organization_ids=[ORG_ID])
    result = await manager.get_removal_types(request)

    assert result is mock_response
    mock_api.get_removal_types.assert_awaited_once_with(
        removal_types_request=request
    )


async def test_get_tips_types_calls_api_without_request() -> None:
    """get_tips_types delegates to SDK without a request body."""
    manager, mock_api = await _manager_with_mock_dictionaries_api()

    mock_response = MagicMock(spec=TipsTypesResponse)
    mock_api.get_tips_types = AsyncMock(return_value=mock_response)

    result = await manager.get_tips_types()

    assert result is mock_response
    mock_api.get_tips_types.assert_awaited_once_with()


async def test_get_cancel_causes_by_organization_builds_request() -> None:
    """get_cancel_causes_by_organization builds CancelCausesRequest."""
    manager, mock_api = await _manager_with_mock_dictionaries_api()

    mock_response = MagicMock(spec=CancelCausesResponse)
    mock_api.get_cancel_causes = AsyncMock(return_value=mock_response)

    result = await manager.get_cancel_causes_by_organization(ORG_ID)

    assert result is mock_response
    mock_api.get_cancel_causes.assert_awaited_once()
    call_kwargs = mock_api.get_cancel_causes.await_args.kwargs
    request = call_kwargs["cancel_causes_request"]
    assert isinstance(request, CancelCausesRequest)
    assert request.organization_ids == [ORG_ID]


async def test_get_delivery_order_types_by_organization_builds_request() -> None:
    """get_delivery_order_types_by_organization builds OrderTypesRequest."""
    manager, mock_api = await _manager_with_mock_dictionaries_api()

    mock_response = MagicMock(spec=OrderTypesResponse)
    mock_api.get_delivery_order_types = AsyncMock(return_value=mock_response)

    result = await manager.get_delivery_order_types_by_organization(ORG_ID)

    assert result is mock_response
    mock_api.get_delivery_order_types.assert_awaited_once()
    call_kwargs = mock_api.get_delivery_order_types.await_args.kwargs
    request = call_kwargs["order_types_request"]
    assert isinstance(request, OrderTypesRequest)
    assert request.organization_ids == [ORG_ID]


async def test_get_payment_types_by_organization_accepts_str_id() -> None:
    """get_payment_types_by_organization converts string organization_id."""
    manager, mock_api = await _manager_with_mock_dictionaries_api()

    mock_api.get_payment_types = AsyncMock(return_value=MagicMock())

    await manager.get_payment_types_by_organization(str(ORG_ID))

    call_kwargs = mock_api.get_payment_types.await_args.kwargs
    request = call_kwargs["payment_types_request"]
    assert request.organization_ids == [ORG_ID]


async def test_get_discounts_by_organization_builds_request() -> None:
    """get_discounts_by_organization builds DiscountsRequest."""
    manager, mock_api = await _manager_with_mock_dictionaries_api()

    mock_api.get_discounts = AsyncMock(return_value=MagicMock())

    await manager.get_discounts_by_organization(ORG_ID)

    call_kwargs = mock_api.get_discounts.await_args.kwargs
    request = call_kwargs["discounts_request"]
    assert isinstance(request, DiscountsRequest)
    assert request.organization_ids == [ORG_ID]


async def test_get_removal_types_by_organization_builds_request() -> None:
    """get_removal_types_by_organization builds RemovalTypesRequest."""
    manager, mock_api = await _manager_with_mock_dictionaries_api()

    mock_api.get_removal_types = AsyncMock(return_value=MagicMock())

    await manager.get_removal_types_by_organization(ORG_ID)

    call_kwargs = mock_api.get_removal_types.await_args.kwargs
    request = call_kwargs["removal_types_request"]
    assert isinstance(request, RemovalTypesRequest)
    assert request.organization_ids == [ORG_ID]


async def test_get_tips_types_uses_execute_with_retry() -> None:
    """get_tips_types routes through execute_with_retry."""
    manager, mock_api = await _manager_with_mock_dictionaries_api()
    mock_api.get_tips_types = AsyncMock(return_value=MagicMock())

    async def _passthrough(method, api_call):  # noqa: ANN001
        return await api_call()

    manager.execute_with_retry = AsyncMock(side_effect=_passthrough)

    await manager.get_tips_types()

    manager.execute_with_retry.assert_awaited_once()
    method_arg = manager.execute_with_retry.await_args.args[0]
    assert method_arg is ApiMethod.GET_TIPS_TYPES
