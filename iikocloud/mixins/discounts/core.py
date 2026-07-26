"""Discounts core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    CalculateCheckinRequest,
    CalculateCheckinResponse,
    CouponInfoRequest,
    CouponInfoResponse,
    GetByOrganizationIdRequest,
    GetManualConditionsResponse,
    GetProgramsRequest,
    GetProgramsResponse,
    NotActivatedCouponRequest,
    NotActivatedCouponResponse,
    SeriesWithNotActivatedCouponsRequest,
    SeriesWithNotActivatedCouponsResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class DiscountsCoreMixin(_ManagerBase):
    """Core-методы DiscountsAndPromotions API (все read-only)."""

    async def calculate_loyalty_checkin(
        self,
        request: CalculateCheckinRequest,
    ) -> CalculateCheckinResponse:
        """Расчёт скидок/лояльности для заказа (высокочастотный вызов).

        Верхнеуровневые coupon/manual_conditions/dynamic_discounts в
        request — obsolete; передавать через order.loyalty_info.
        """

        async def api_call() -> CalculateCheckinResponse:
            api = await self.get_discounts_and_promotions_api()
            return await api.calculate_loyalty_checkin(
                calculate_checkin_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CALCULATE_LOYALTY_CHECKIN, api_call
        )

    async def get_coupon_info(
        self,
        request: CouponInfoRequest,
    ) -> CouponInfoResponse:
        """Информация о купоне по номеру."""

        async def api_call() -> CouponInfoResponse:
            api = await self.get_discounts_and_promotions_api()
            return await api.get_coupon_info(coupon_info_request=request)

        return await self.execute_with_retry(ApiMethod.GET_COUPON_INFO, api_call)

    async def get_coupon_series(
        self,
        request: SeriesWithNotActivatedCouponsRequest,
    ) -> SeriesWithNotActivatedCouponsResponse:
        """Серии купонов с неудалёнными неактивированными купонами."""

        async def api_call() -> SeriesWithNotActivatedCouponsResponse:
            api = await self.get_discounts_and_promotions_api()
            return await api.get_coupon_series(
                series_with_not_activated_coupons_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_COUPON_SERIES, api_call
        )

    async def get_loyalty_manual_conditions(
        self,
        request: GetByOrganizationIdRequest,
    ) -> GetManualConditionsResponse:
        """Все ручные условия организации.

        Raises:
            ValueError: organization_id не задан (в модели optional)
        """
        if request.organization_id is None:
            raise ValueError("organization_id обязателен")

        async def api_call() -> GetManualConditionsResponse:
            api = await self.get_discounts_and_promotions_api()
            return await api.get_loyalty_manual_conditions(
                get_by_organization_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_LOYALTY_MANUAL_CONDITIONS, api_call
        )

    async def get_loyalty_programs(
        self,
        request: GetProgramsRequest,
    ) -> GetProgramsResponse:
        """Все программы лояльности организации."""

        async def api_call() -> GetProgramsResponse:
            api = await self.get_discounts_and_promotions_api()
            return await api.get_loyalty_programs(get_programs_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_LOYALTY_PROGRAMS, api_call
        )

    async def get_non_activated_coupons_by_series(
        self,
        request: NotActivatedCouponRequest,
    ) -> NotActivatedCouponResponse:
        """Неактивированные купоны серии (page/page_size-пагинация)."""

        async def api_call() -> NotActivatedCouponResponse:
            api = await self.get_discounts_and_promotions_api()
            return await api.get_non_activated_coupons_by_series(
                not_activated_coupon_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_NON_ACTIVATED_COUPONS_BY_SERIES, api_call
        )
