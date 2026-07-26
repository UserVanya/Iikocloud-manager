"""Unit tests for Banquets & Reserves domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    AddOrderItemsToBanquetRequest,
    AddOrderPaymentsToBanquetRequest,
    CancelReserveRequest,
    ChangeBanquetOrderItemsRequest,
    ChangeReserveEstimatedStartTimeRequest,
    ChangeReserveTablesRequest,
    CorrelationIdResponse,
    CreateReserveRequest,
    DeliveryOrderCreateRegularCustomer,
    GetOrganizationsRequest,
    GetOrganizationsResponse,
    GetRestaurantSectionsRequest,
    GetRestaurantSectionsResponse,
    GetRestaurantSectionsWorkloadRequest,
    GetRestaurantSectionsWorkloadResponse,
    GetTerminalGroupsByOrganizationsRequest,
    ReserveCancelReason,
    ReserveResponse,
    ReservesByIdRequest,
    ReservesResponse,
    TerminalGroupsResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_banquets_reserves_api"

METHODS: list[tuple[str, object, str, type]] = [
    (
        "get_reserve_available_organizations",
        GetOrganizationsRequest(),
        "get_organizations_request",
        GetOrganizationsResponse,
    ),
    (
        "get_reserve_terminal_groups",
        GetTerminalGroupsByOrganizationsRequest(organization_ids=[ORG_ID]),
        "get_terminal_groups_by_organizations_request",
        TerminalGroupsResponse,
    ),
    (
        "get_reserve_restaurant_sections",
        GetRestaurantSectionsRequest(terminal_group_ids=[ORG_ID]),
        "get_restaurant_sections_request",
        GetRestaurantSectionsResponse,
    ),
    (
        "get_reserve_statuses_by_id",
        ReservesByIdRequest(organization_id=ORG_ID, reserve_ids=[ORG_ID]),
        "reserves_by_id_request",
        ReservesResponse,
    ),
    (
        "get_restaurant_sections_workload",
        GetRestaurantSectionsWorkloadRequest(
            restaurant_section_ids=[ORG_ID], date_from="2026-07-25 00:00:00.000"
        ),
        "get_restaurant_sections_workload_request",
        GetRestaurantSectionsWorkloadResponse,
    ),
    (
        "create_reserve",
        CreateReserveRequest(
            organization_id=ORG_ID,
            phone="+79990001122",
            customer=DeliveryOrderCreateRegularCustomer(type="regular", name="Test"),
            estimated_start_time="2026-07-26 12:00:00.000",
            duration_in_minutes=60,
            should_remind=False,
            table_ids=[ORG_ID],
        ),
        "create_reserve_request",
        ReserveResponse,
    ),
    (
        "add_banquet_order_items",
        AddOrderItemsToBanquetRequest(
            organization_id=ORG_ID, reserve_id=ORG_ID, items=[]
        ),
        "add_order_items_to_banquet_request",
        CorrelationIdResponse,
    ),
    (
        "add_banquet_order_payments",
        AddOrderPaymentsToBanquetRequest(
            organization_id=ORG_ID, reserve_id=ORG_ID, payments=[]
        ),
        "add_order_payments_to_banquet_request",
        CorrelationIdResponse,
    ),
    (
        "cancel_reserve",
        CancelReserveRequest(
            organization_id=ORG_ID,
            reserve_id=ORG_ID,
            cancel_reason=ReserveCancelReason.CLIENTREFUSED,
        ),
        "cancel_reserve_request",
        CorrelationIdResponse,
    ),
    (
        "change_banquet_order_items",
        ChangeBanquetOrderItemsRequest(organization_id=ORG_ID, reserve_id=ORG_ID),
        "change_banquet_order_items_request",
        CorrelationIdResponse,
    ),
    (
        "change_reserve_estimated_start_time",
        ChangeReserveEstimatedStartTimeRequest(
            organization_id=ORG_ID,
            reserve_id=ORG_ID,
            new_estimated_start_time="2026-07-26 12:00:00.000",
        ),
        "change_reserve_estimated_start_time_request",
        CorrelationIdResponse,
    ),
    (
        "change_reserve_tables",
        ChangeReserveTablesRequest(
            organization_id=ORG_ID, reserve_id=ORG_ID, table_ids=[ORG_ID]
        ),
        "change_reserve_tables_request",
        CorrelationIdResponse,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), METHODS
)
async def test_banquets_methods_delegate(
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
