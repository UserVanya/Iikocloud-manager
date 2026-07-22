"""Dictionaries core mixin — прямые обёртки SDK через execute_with_retry."""

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

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class DictionariesCoreMixin(_ManagerBase):
    """Core-методы Dictionaries API."""

    async def get_cancel_causes(
        self,
        cancel_causes_request: CancelCausesRequest,
    ) -> CancelCausesResponse:
        """Получить причины отмены доставки.

        Args:
            cancel_causes_request: Параметры запроса CancelCausesRequest

        Returns:
            Ответ со списком причин отмены
        """

        async def api_call() -> CancelCausesResponse:
            api = await self.get_dictionaries_api()
            return await api.get_cancel_causes(
                cancel_causes_request=cancel_causes_request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_CANCEL_CAUSES, api_call
        )

    async def get_delivery_order_types(
        self,
        order_types_request: OrderTypesRequest,
    ) -> OrderTypesResponse:
        """Получить типы заказов доставки.

        Args:
            order_types_request: Параметры запроса OrderTypesRequest

        Returns:
            Ответ со списком типов заказов
        """

        async def api_call() -> OrderTypesResponse:
            api = await self.get_dictionaries_api()
            return await api.get_delivery_order_types(
                order_types_request=order_types_request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERY_ORDER_TYPES, api_call
        )

    async def get_payment_types(
        self,
        payment_types_request: PaymentTypesRequest,
    ) -> PaymentTypesResponse:
        """Получить типы оплаты.

        Args:
            payment_types_request: Параметры запроса PaymentTypesRequest

        Returns:
            Ответ со списком типов оплаты
        """

        async def api_call() -> PaymentTypesResponse:
            api = await self.get_dictionaries_api()
            return await api.get_payment_types(
                payment_types_request=payment_types_request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_PAYMENT_TYPES, api_call
        )

    async def get_discounts(
        self,
        discounts_request: DiscountsRequest,
    ) -> DiscountsResponse:
        """Получить скидки.

        Args:
            discounts_request: Параметры запроса DiscountsRequest

        Returns:
            Ответ со списком скидок
        """

        async def api_call() -> DiscountsResponse:
            api = await self.get_dictionaries_api()
            return await api.get_discounts(discounts_request=discounts_request)

        return await self.execute_with_retry(
            ApiMethod.GET_DISCOUNTS, api_call
        )

    async def get_removal_types(
        self,
        removal_types_request: RemovalTypesRequest,
    ) -> RemovalTypesResponse:
        """Получить типы списания.

        Args:
            removal_types_request: Параметры запроса RemovalTypesRequest

        Returns:
            Ответ со списком типов списания
        """

        async def api_call() -> RemovalTypesResponse:
            api = await self.get_dictionaries_api()
            return await api.get_removal_types(
                removal_types_request=removal_types_request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_REMOVAL_TYPES, api_call
        )

    async def get_tips_types(self) -> TipsTypesResponse:
        """Получить типы чаевых.

        Returns:
            Ответ со списком типов чаевых
        """

        async def api_call() -> TipsTypesResponse:
            api = await self.get_dictionaries_api()
            return await api.get_tips_types()

        return await self.execute_with_retry(
            ApiMethod.GET_TIPS_TYPES, api_call
        )
