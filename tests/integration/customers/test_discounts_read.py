"""Structure-only read-тесты DiscountsAndPromotions (write-секция через test_server).

Запуск:
    uv run pytest tests/integration/customers/test_discounts_read.py -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import (
    GetByOrganizationIdRequest,
    GetProgramsRequest,
    NotActivatedCouponRequest,
    SeriesWithNotActivatedCouponsRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestDiscountsRead:
    async def test_get_loyalty_programs_finds_bonus_program(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """На write-стенде есть программа лояльности («Бонусы»)."""
        response = await manager.get_loyalty_programs(
            GetProgramsRequest(organization_id=organization_id)
        )

        assert response is not None
        assert response.programs is not None
        assert len(response.programs) > 0
        program = response.programs[0]
        assert program.id is not None
        assert isinstance(program.name, str)

    async def test_get_loyalty_manual_conditions_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_loyalty_manual_conditions(
            GetByOrganizationIdRequest(organization_id=organization_id)
        )

        assert response is not None
        assert response.manual_conditions is not None

    async def test_get_coupon_series_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_coupon_series(
            SeriesWithNotActivatedCouponsRequest(
                organization_id=organization_id
            )
        )

        assert response is not None
        assert response.series_with_not_activated_coupons is not None

    async def test_coupon_info_from_series(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """coupon_info по первому купону первой серии (skip, если купонов нет)."""
        series_response = await manager.get_coupon_series(
            SeriesWithNotActivatedCouponsRequest(
                organization_id=organization_id
            )
        )
        series = series_response.series_with_not_activated_coupons or []
        if not series:
            pytest.skip("Нет серий купонов на write-стенде")

        coupons = await manager.get_non_activated_coupons_by_series(
            NotActivatedCouponRequest(
                organization_id=organization_id,
                series=series[0].number,
                page_size=1,
            )
        )
        coupon_list = coupons.not_activated_coupon or []
        if not coupon_list:
            pytest.skip("Нет неактивированных купонов в серии")

        from iikocloud_client import CouponInfoRequest

        info = await manager.get_coupon_info(
            CouponInfoRequest(
                number=coupon_list[0].number, organization_id=organization_id
            )
        )
        assert info is not None
        assert info.coupon_info is not None

    async def test_calculate_order_loyalty_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        product: tuple[UUID, float],
    ) -> None:
        """Расчёт лояльности по минимальному заказу (helper)."""
        from tests.conftest import generate_random_phone

        product_id, price = product
        item = manager.build_product_item(product_id=product_id, price=price)

        response = await manager.calculate_order_loyalty(
            organization_id=organization_id,
            items=[item],
            phone=generate_random_phone(),
            order_service_type="DeliveryByClient",
        )

        assert response is not None
        # Расчёт всегда возвращает структуру, даже без применимых программ
        assert response.loyalty_program_results is not None or (
            response.warnings is not None
        )
