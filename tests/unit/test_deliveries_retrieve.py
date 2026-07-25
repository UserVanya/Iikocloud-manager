"""Unit tests for DeliveriesRetrieve domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
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
