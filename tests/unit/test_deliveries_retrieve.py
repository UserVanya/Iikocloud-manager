"""Unit tests for DeliveriesRetrieve domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    OrderInfo,
    OrdersByDeliveryDateAndFilterRequest,
    OrdersByDeliveryDateAndPhoneRequest,
    OrdersByDeliveryDateAndStatusRequest,
    OrdersByIdRequest,
    OrdersByRevisionRequest,
    OrdersHistoryByDeliveryDateAndPhoneRequest,
    OrdersResponse,
    OrdersWithRevisionResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_deliveries_retrieve_api"

REVISION_METHODS = [
    (
        "get_deliveries_by_delivery_date_and_phone",
        OrdersByDeliveryDateAndPhoneRequest(
            organization_ids=[ORG_ID], phone=None
        ),
        "orders_by_delivery_date_and_phone_request",
    ),
    (
        "get_deliveries_by_delivery_date_and_status",
        OrdersByDeliveryDateAndStatusRequest(
            organization_ids=[ORG_ID],
            delivery_date_from="2026-07-25 00:00:00.000",
        ),
        "orders_by_delivery_date_and_status_request",
    ),
    (
        "get_deliveries_by_revision",
        OrdersByRevisionRequest(organization_ids=[ORG_ID], start_revision=0),
        "orders_by_revision_request",
    ),
    (
        "get_delivery_history_by_delivery_date_and_phone",
        OrdersHistoryByDeliveryDateAndPhoneRequest(
            organization_ids=[ORG_ID], phone="+7999", rows_count=10
        ),
        "orders_history_by_delivery_date_and_phone_request",
    ),
    (
        "search_deliveries",
        OrdersByDeliveryDateAndFilterRequest(organization_ids=[ORG_ID]),
        "orders_by_delivery_date_and_filter_request",
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg"), REVISION_METHODS
)
async def test_revision_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str
) -> None:
    """Методы -> OrdersWithRevisionResponse проксируются с request-моделью."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=OrdersWithRevisionResponse)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


async def test_get_deliveries_by_id_returns_orders_response() -> None:
    """get_deliveries_by_id проксирует плоский OrdersResponse."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=OrdersResponse)
    mock_api.get_deliveries_by_id = AsyncMock(return_value=mock_response)

    request = OrdersByIdRequest(organization_id=ORG_ID, order_ids=[ORG_ID])
    result = await manager.get_deliveries_by_id(request)

    assert result is mock_response
    mock_api.get_deliveries_by_id.assert_awaited_once_with(
        orders_by_id_request=request
    )


async def test_get_deliveries_by_id_rejects_both_id_lists() -> None:
    """XOR: order_ids + pos_order_ids одновременно -> ValueError."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)

    request = OrdersByIdRequest(
        organization_id=ORG_ID, order_ids=[ORG_ID], pos_order_ids=[ORG_ID]
    )
    with pytest.raises(ValueError, match="order_ids"):
        await manager.get_deliveries_by_id(request)
    mock_api.get_deliveries_by_id.assert_not_called()


async def test_get_deliveries_by_id_rejects_empty() -> None:
    """Оба списка пусты/None -> ValueError."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)

    request = OrdersByIdRequest(organization_id=ORG_ID)
    with pytest.raises(ValueError, match="order_ids"):
        await manager.get_deliveries_by_id(request)
    mock_api.get_deliveries_by_id.assert_not_called()


async def test_get_deliveries_by_id_rejects_over_200() -> None:
    """> 200 id за запрос -> ValueError."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)

    request = OrdersByIdRequest(
        organization_id=ORG_ID, order_ids=[ORG_ID] * 201
    )
    with pytest.raises(ValueError, match="200"):
        await manager.get_deliveries_by_id(request)
    mock_api.get_deliveries_by_id.assert_not_called()


@pytest.mark.parametrize("rows_count", [0, 201])
async def test_history_rejects_bad_rows_count(rows_count: int) -> None:
    """rows_count вне 1..200 -> ValueError."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)

    request = OrdersHistoryByDeliveryDateAndPhoneRequest(
        organization_ids=[ORG_ID], phone="+7999", rows_count=rows_count
    )
    with pytest.raises(ValueError, match="rows_count"):
        await manager.get_delivery_history_by_delivery_date_and_phone(request)
    mock_api.get_delivery_history_by_delivery_date_and_phone.assert_not_called()


async def test_get_delivery_by_id_returns_first_order() -> None:
    """get_delivery_by_id возвращает единственный заказ из плоского ответа."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    order_info = MagicMock(spec=OrderInfo)
    mock_response = MagicMock(spec=OrdersResponse)
    mock_response.orders = [order_info]
    mock_api.get_deliveries_by_id = AsyncMock(return_value=mock_response)

    result = await manager.get_delivery_by_id(str(ORG_ID), ORG_ID)

    assert result is order_info
    call_kwargs = mock_api.get_deliveries_by_id.await_args.kwargs
    request = call_kwargs["orders_by_id_request"]
    assert isinstance(request, OrdersByIdRequest)
    assert request.organization_id == ORG_ID
    assert request.order_ids == [ORG_ID]


async def test_get_delivery_by_id_returns_none_when_missing() -> None:
    """get_delivery_by_id -> None, если заказ не найден."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=OrdersResponse)
    mock_response.orders = []
    mock_api.get_deliveries_by_id = AsyncMock(return_value=mock_response)

    result = await manager.get_delivery_by_id(ORG_ID, ORG_ID)

    assert result is None


async def test_get_customer_deliveries_builds_date_window() -> None:
    """get_customer_deliveries собирает период и выравнивает ответ."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    order_info = MagicMock(spec=OrderInfo)
    org_orders = MagicMock()
    org_orders.orders = [order_info]
    mock_response = MagicMock(spec=OrdersWithRevisionResponse)
    mock_response.orders_by_organizations = [org_orders]
    mock_api.get_deliveries_by_delivery_date_and_phone = AsyncMock(
        return_value=mock_response
    )

    result = await manager.get_customer_deliveries(
        [str(ORG_ID)], phone="+79990001122", days=3
    )

    assert result == [order_info]
    call_kwargs = (
        mock_api.get_deliveries_by_delivery_date_and_phone.await_args.kwargs
    )
    request = call_kwargs["orders_by_delivery_date_and_phone_request"]
    assert isinstance(request, OrdersByDeliveryDateAndPhoneRequest)
    assert request.organization_ids == [ORG_ID]
    assert request.phone == "+79990001122"
    # delivery_date_from заполнен и раньше delivery_date_to
    assert request.delivery_date_from is not None
    assert request.delivery_date_to is not None
    assert request.delivery_date_from < request.delivery_date_to
