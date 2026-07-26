"""Unit tests for Discounts domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    CalculateCheckinRequest,
    CalculateCheckinResponse,
    CouponInfoRequest,
    CouponInfoResponse,
    DeliveryOrderCreatePayload,
    DeliveryOrderCreateProductItem,
    GetByOrganizationIdRequest,
    GetManualConditionsResponse,
    GetProgramsRequest,
    GetProgramsResponse,
    NotActivatedCouponRequest,
    NotActivatedCouponResponse,
    SeriesWithNotActivatedCouponsRequest,
    SeriesWithNotActivatedCouponsResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_discounts_and_promotions_api"

METHODS: list[tuple[str, object, str, type]] = [
    (
        "calculate_loyalty_checkin",
        CalculateCheckinRequest(
            organization_id=ORG_ID,
            order=DeliveryOrderCreatePayload(
                phone="+79990001122",
                items=[
                    DeliveryOrderCreateProductItem(
                        type="Product", product_id=ORG_ID, amount=1.0, price=1.0
                    )
                ],
            ),
        ),
        "calculate_checkin_request",
        CalculateCheckinResponse,
    ),
    (
        "get_coupon_info",
        CouponInfoRequest(number="123", organization_id=ORG_ID),
        "coupon_info_request",
        CouponInfoResponse,
    ),
    (
        "get_coupon_series",
        SeriesWithNotActivatedCouponsRequest(organization_id=ORG_ID),
        "series_with_not_activated_coupons_request",
        SeriesWithNotActivatedCouponsResponse,
    ),
    (
        "get_loyalty_manual_conditions",
        GetByOrganizationIdRequest(organization_id=ORG_ID),
        "get_by_organization_id_request",
        GetManualConditionsResponse,
    ),
    (
        "get_loyalty_programs",
        GetProgramsRequest(organization_id=ORG_ID),
        "get_programs_request",
        GetProgramsResponse,
    ),
    (
        "get_non_activated_coupons_by_series",
        NotActivatedCouponRequest(organization_id=ORG_ID, series="S"),
        "not_activated_coupon_request",
        NotActivatedCouponResponse,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), METHODS
)
async def test_discounts_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 6 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


async def test_manual_conditions_requires_organization_id() -> None:
    """organization_id=None -> ValueError, SDK не вызывается."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)

    request = GetByOrganizationIdRequest(organization_id=None)
    with pytest.raises(ValueError, match="organization_id"):
        await manager.get_loyalty_manual_conditions(request)
    mock_api.get_loyalty_manual_conditions.assert_not_called()


async def test_calculate_order_loyalty_builds_payload() -> None:
    """Helper собирает DeliveryOrderCreatePayload с loyalty_info."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=CalculateCheckinResponse)
    mock_api.calculate_loyalty_checkin = AsyncMock(return_value=mock_response)

    item = manager.build_product_item(product_id=ORG_ID, price=150.0)
    result = await manager.calculate_order_loyalty(
        organization_id=str(ORG_ID),
        items=[item],
        phone="+79990001122",
        coupon="COUPON1",
        order_service_type="DeliveryByClient",
    )

    assert result is mock_response
    call_kwargs = mock_api.calculate_loyalty_checkin.await_args.kwargs
    request = call_kwargs["calculate_checkin_request"]
    assert isinstance(request, CalculateCheckinRequest)
    assert request.organization_id == ORG_ID
    order = request.order
    assert order.phone == "+79990001122"
    assert order.items == [item]
    assert order.loyalty_info is not None
    assert order.loyalty_info.coupon == "COUPON1"
    assert order.order_service_type is not None
