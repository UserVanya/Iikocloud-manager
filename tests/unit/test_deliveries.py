"""Unit tests for Deliveries domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    AddOrderItemsRequest,
    AddOrderPaymentsRequest,
    CancelDeliveryConfirmationRequest,
    CancelOrderRequest,
    ChangeCompleteBeforeRequest,
    ChangeDeliveryCommentRequest,
    ChangeDeliveryOperatorRequest,
    ChangeDeliveryPointRequest,
    ChangeDriverInfoRequest,
    ChangeExternalDataRequest,
    ChangePaymentsRequest,
    ChangeServiceTypeRequest,
    CloseDeliveryOrderRequest,
    ConfirmDeliveryRequest,
    CorrelationIdResponse,
    CreateOrderRequest,
    DeliveryOrder,
    DeliveryOrderCreateCompoundItem,
    DeliveryOrderCreateCompoundItemComponent,
    DeliveryOrderCreatePoint,
    DeliveryOrderCreateProductItem,
    DeliveryStatusForUpdate,
    Modifier,
    OrderResponse,
    PrintBillRequest,
    PrintDeliveryBillRequest,
    UpdateDeliveryStatusRequest,
    UpdateOrderProblemRequest,
    UpdateTrackingLinkRequest,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_deliveries_create_and_update_api"

CORRELATION_METHODS = [
    (
        "add_delivery_order_items",
        AddOrderItemsRequest(organization_id=ORG_ID, order_id=ORG_ID, items=[]),
        "add_order_items_request",
    ),
    (
        "add_delivery_order_payments",
        AddOrderPaymentsRequest(
            organization_id=ORG_ID, order_id=ORG_ID, payments=[]
        ),
        "add_order_payments_request",
    ),
    (
        "cancel_delivery_order",
        CancelOrderRequest(organization_id=ORG_ID, order_id=ORG_ID),
        "cancel_order_request",
    ),
    (
        "cancel_delivery_confirmation",
        CancelDeliveryConfirmationRequest(
            organization_id=ORG_ID, order_id=ORG_ID
        ),
        "cancel_delivery_confirmation_request",
    ),
    (
        "confirm_delivery",
        ConfirmDeliveryRequest(organization_id=ORG_ID, order_id=ORG_ID),
        "confirm_delivery_request",
    ),
    (
        "change_delivery_comment",
        ChangeDeliveryCommentRequest(
            organization_id=ORG_ID, order_id=ORG_ID, comment="c"
        ),
        "change_delivery_comment_request",
    ),
    (
        "change_delivery_complete_before",
        ChangeCompleteBeforeRequest(
            organization_id=ORG_ID,
            order_id=ORG_ID,
            new_complete_before="2026-07-26 12:00:00.000",
        ),
        "change_complete_before_request",
    ),
    (
        "change_delivery_driver_info",
        ChangeDriverInfoRequest(organization_id=ORG_ID, order_id=ORG_ID),
        "change_driver_info_request",
    ),
    (
        "change_delivery_external_data",
        ChangeExternalDataRequest(
            organization_id=ORG_ID, order_id=ORG_ID, external_data=[]
        ),
        "change_external_data_request",
    ),
    (
        "change_delivery_operator",
        ChangeDeliveryOperatorRequest(
            organization_id=ORG_ID, order_id=ORG_ID, operator_id=ORG_ID
        ),
        "change_delivery_operator_request",
    ),
    (
        "change_delivery_payments",
        ChangePaymentsRequest(organization_id=ORG_ID, order_id=ORG_ID, payments=[]),
        "change_payments_request",
    ),
    (
        "change_delivery_point",
        ChangeDeliveryPointRequest(
            organization_id=ORG_ID,
            order_id=ORG_ID,
            new_delivery_point=DeliveryOrderCreatePoint(),
        ),
        "change_delivery_point_request",
    ),
    (
        "change_delivery_service_type",
        ChangeServiceTypeRequest(
            organization_id=ORG_ID,
            order_id=ORG_ID,
            new_service_type="DeliveryByCourier",
        ),
        "change_service_type_request",
    ),
    (
        "close_delivery_order",
        CloseDeliveryOrderRequest(organization_id=ORG_ID, order_id=ORG_ID),
        "close_delivery_order_request",
    ),
    (
        "print_delivery_bill",
        PrintDeliveryBillRequest(organization_id=ORG_ID, order_id=ORG_ID),
        "print_delivery_bill_request",
    ),
    (
        "print_table_order_bill",
        PrintBillRequest(organization_id=ORG_ID, order_id=ORG_ID),
        "print_bill_request",
    ),
    (
        "update_delivery_order_problem",
        UpdateOrderProblemRequest(
            organization_id=ORG_ID, order_id=ORG_ID, has_problem=True, problem=None
        ),
        "update_order_problem_request",
    ),
    (
        "update_delivery_order_status",
        UpdateDeliveryStatusRequest(
            organization_id=ORG_ID,
            order_id=ORG_ID,
            delivery_status=DeliveryStatusForUpdate.WAITING,
        ),
        "update_delivery_status_request",
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg"), CORRELATION_METHODS
)
async def test_correlation_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str
) -> None:
    """Команды -> CorrelationIdResponse проксируются с request-моделью."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=CorrelationIdResponse)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


async def test_create_delivery_order_returns_order_response() -> None:
    """create_delivery_order проксирует OrderResponse."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=OrderResponse)
    mock_api.create_delivery_order = AsyncMock(return_value=mock_response)

    request = CreateOrderRequest(
        organization_id=ORG_ID,
        order=DeliveryOrder(
            phone="+79990001122",
            items=[
                DeliveryOrderCreateProductItem(
                    type="Product", product_id=ORG_ID, amount=1.0, price=1.0
                )
            ],
        ),
    )
    result = await manager.create_delivery_order(request)

    assert result is mock_response
    mock_api.create_delivery_order.assert_awaited_once_with(
        create_order_request=request
    )


async def test_update_delivery_tracking_link_returns_none() -> None:
    """update_delivery_tracking_link: ответ без тела -> None."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.update_delivery_tracking_link = AsyncMock(return_value=object())

    request = UpdateTrackingLinkRequest(
        organization_id=ORG_ID, order_id=ORG_ID, tracking_link="https://x"
    )
    result = await manager.update_delivery_tracking_link(request)

    assert result is None
    mock_api.update_delivery_tracking_link.assert_awaited_once_with(
        update_tracking_link_request=request
    )


def test_build_product_item_fills_discriminator() -> None:
    """build_product_item собирает Product-позицию с type='Product'."""
    from iikocloud.mixins.deliveries.helpers import DeliveriesHelpersMixin

    item = DeliveriesHelpersMixin.build_product_item(
        product_id=str(ORG_ID), price=150.0, amount=2.0, comment="no onion"
    )

    assert isinstance(item, DeliveryOrderCreateProductItem)
    assert item.type == "Product"
    assert item.product_id == ORG_ID
    assert item.price == 150.0
    assert item.amount == 2.0
    assert item.comment == "no onion"


def test_build_product_item_with_modifier() -> None:
    """build_product_item прокидывает modifiers."""
    from iikocloud.mixins.deliveries.helpers import DeliveriesHelpersMixin

    modifier = Modifier(product_id=ORG_ID, amount=1.0)
    item = DeliveriesHelpersMixin.build_product_item(
        product_id=ORG_ID, price=100.0, modifiers=[modifier]
    )

    assert item.modifiers == [modifier]


def test_build_compound_item_components() -> None:
    """build_compound_item собирает Compound-позицию с компонентами."""
    from iikocloud.mixins.deliveries.helpers import DeliveriesHelpersMixin

    item = DeliveriesHelpersMixin.build_compound_item(
        primary_product_id=ORG_ID,
        secondary_product_id=str(ORG_ID),
        primary_price=200.0,
    )

    assert isinstance(item, DeliveryOrderCreateCompoundItem)
    assert item.type == "Compound"
    assert isinstance(
        item.primary_component, DeliveryOrderCreateCompoundItemComponent
    )
    assert item.primary_component.product_id == ORG_ID
    assert item.primary_component.price == 200.0
    assert item.secondary_component is not None
    assert item.secondary_component.product_id == ORG_ID


def test_build_compound_item_without_secondary() -> None:
    """build_compound_item без второго компонента -> secondary=None."""
    from iikocloud.mixins.deliveries.helpers import DeliveriesHelpersMixin

    item = DeliveriesHelpersMixin.build_compound_item(primary_product_id=ORG_ID)

    assert item.secondary_component is None


async def test_cancel_order_builds_request() -> None:
    """cancel_order собирает CancelOrderRequest и вызывает core."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=CorrelationIdResponse)
    mock_api.cancel_delivery_order = AsyncMock(return_value=mock_response)

    result = await manager.cancel_order(
        organization_id=str(ORG_ID), order_id=ORG_ID, cancel_comment="test"
    )

    assert result is mock_response
    call_kwargs = mock_api.cancel_delivery_order.await_args.kwargs
    request = call_kwargs["cancel_order_request"]
    assert isinstance(request, CancelOrderRequest)
    assert request.organization_id == ORG_ID
    assert request.order_id == ORG_ID
    assert request.cancel_comment == "test"
