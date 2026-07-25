"""DeliveryRestrictions core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    GetAllowedRestrictionsRequest,
    GetAllowedRestrictionsResponse,
    GetDeliveryRestrictionsRequest,
    GetDeliveryRestrictionsResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class DeliveryRestrictionsCoreMixin(_ManagerBase):
    """Core-методы DeliveryRestrictions API (оба read-only)."""

    async def get_allowed_delivery_restrictions(
        self,
        request: GetAllowedRestrictionsRequest,
    ) -> GetAllowedRestrictionsResponse:
        """Подходящие терминальные группы под адрес/сумму/дату доставки.

        Ответ: is_allowed + allowed_items (терминалы с длительностью)
        и rejected_items с кодами причин отказа.
        """

        async def api_call() -> GetAllowedRestrictionsResponse:
            api = await self.get_delivery_restrictions_api()
            return await api.get_allowed_delivery_restrictions(
                get_allowed_restrictions_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_ALLOWED_DELIVERY_RESTRICTIONS, api_call
        )

    async def get_delivery_restrictions(
        self,
        request: GetDeliveryRestrictionsRequest,
    ) -> GetDeliveryRestrictionsResponse:
        """Справочник ограничений доставки (зоны, мин. суммы, интервалы)."""

        async def api_call() -> GetDeliveryRestrictionsResponse:
            api = await self.get_delivery_restrictions_api()
            return await api.get_delivery_restrictions(
                get_delivery_restrictions_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERY_RESTRICTIONS, api_call
        )
