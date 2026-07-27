"""Unit tests for Orders domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    AddCustomerToTableOrderRequest,
    AddItemsToTableOrderRequest,
    AddOrderPaymentsRequest,
    CancelTableOrderRequest,
    ChangeExternalDataRequest,
    ChangePaymentsRequest,
    CloseTableOrderRequest,
    CorrelationIdResponse,
    CreateTableOrderRequest,
    DeliveryOrderCreateProductItem,
    GetTableOrdersByIdRequest,
    GetTableOrdersByTableRequest,
    InitTableOrderByPosOrderRequest,
    InitTableOrderRequest,
    TableOrderCustomer,
    TableOrderRequest,
    TableOrderResponse,
    TableOrdersResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_orders_api"

ITEM = DeliveryOrderCreateProductItem(
    type="Product", product_id=ORG_ID, amount=1.0, price=1.0
)

METHODS: list[tuple[str, object, str, type]] = [
    (
        "create_table_order",
        CreateTableOrderRequest(
            organization_id=ORG_ID,
            terminal_group_id=ORG_ID,
            order=TableOrderRequest(items=[ITEM]),
        ),
        "create_table_order_request",
        TableOrderResponse,
    ),
    (
        "add_customer_to_table_order",
        AddCustomerToTableOrderRequest(
            organization_id=ORG_ID,
            order_id=ORG_ID,
            customer=TableOrderCustomer(name="T", phone="+79990001122"),
        ),
        "add_customer_to_table_order_request",
        CorrelationIdResponse,
    ),
    (
        "add_items_to_table_order",
        AddItemsToTableOrderRequest(
            organization_id=ORG_ID, order_id=ORG_ID, items=[ITEM]
        ),
        "add_items_to_table_order_request",
        CorrelationIdResponse,
    ),
    (
        "add_table_order_payments",
        AddOrderPaymentsRequest(
            organization_id=ORG_ID, order_id=ORG_ID, payments=[]
        ),
        "add_order_payments_request",
        CorrelationIdResponse,
    ),
    (
        "change_table_order_payments",
        ChangePaymentsRequest(
            organization_id=ORG_ID, order_id=ORG_ID, payments=[]
        ),
        "change_payments_request",
        CorrelationIdResponse,
    ),
    (
        "change_table_order_external_data",
        ChangeExternalDataRequest(
            organization_id=ORG_ID, order_id=ORG_ID, external_data=[]
        ),
        "change_external_data_request",
        CorrelationIdResponse,
    ),
    (
        "close_table_order",
        CloseTableOrderRequest(organization_id=ORG_ID, order_id=ORG_ID),
        "close_table_order_request",
        CorrelationIdResponse,
    ),
    (
        "cancel_table_order",
        CancelTableOrderRequest(organization_id=ORG_ID, order_id=ORG_ID),
        "cancel_table_order_request",
        CorrelationIdResponse,
    ),
    (
        "initialize_table_orders_by_pos_orders",
        InitTableOrderByPosOrderRequest(
            organization_id=ORG_ID,
            terminal_group_id=ORG_ID,
            pos_order_ids=[ORG_ID],
        ),
        "init_table_order_by_pos_order_request",
        CorrelationIdResponse,
    ),
    (
        "initialize_table_orders_by_tables",
        InitTableOrderRequest(
            organization_id=ORG_ID,
            terminal_group_id=ORG_ID,
            table_ids=[ORG_ID],
        ),
        "init_table_order_request",
        CorrelationIdResponse,
    ),
    (
        "get_table_orders_by_id",
        GetTableOrdersByIdRequest(
            organization_ids=[ORG_ID], order_ids=[ORG_ID]
        ),
        "get_table_orders_by_id_request",
        TableOrdersResponse,
    ),
    (
        "get_table_orders_by_table",
        GetTableOrdersByTableRequest(
            organization_ids=[ORG_ID], table_ids=[ORG_ID]
        ),
        "get_table_orders_by_table_request",
        TableOrdersResponse,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), METHODS
)
async def test_orders_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 12 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})
