"""DeliveriesRetrieve core mixin — прямые обёртки SDK через execute_with_retry."""

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

from iikocloud.mixins._base import ApiMethod, _ManagerBase

_MAX_IDS_PER_REQUEST = 200
_MAX_HISTORY_ROWS = 200


class DeliveriesRetrieveCoreMixin(_ManagerBase):
    """Core-методы Deliveries retrieve API (все read-only).

    Серверные ограничения домена: «горячие» заказы — последние 7 дней,
    история — 90 дней, revision-окно — 3 часа.
    """

    async def get_deliveries_by_delivery_date_and_phone(
        self,
        request: OrdersByDeliveryDateAndPhoneRequest,
    ) -> OrdersWithRevisionResponse:
        """Заказы по телефону/датам/revision (гарантия — последние 7 дней)."""

        async def api_call() -> OrdersWithRevisionResponse:
            api = await self.get_deliveries_retrieve_api()
            return await api.get_deliveries_by_delivery_date_and_phone(
                orders_by_delivery_date_and_phone_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERIES_BY_DELIVERY_DATE_AND_PHONE, api_call
        )

    async def get_deliveries_by_delivery_date_and_status(
        self,
        request: OrdersByDeliveryDateAndStatusRequest,
    ) -> OrdersWithRevisionResponse:
        """Заказы по статусам/датам/курьерам (гарантия — последние 7 дней)."""

        async def api_call() -> OrdersWithRevisionResponse:
            api = await self.get_deliveries_retrieve_api()
            return await api.get_deliveries_by_delivery_date_and_status(
                orders_by_delivery_date_and_status_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERIES_BY_DELIVERY_DATE_AND_STATUS, api_call
        )

    async def get_deliveries_by_id(
        self,
        request: OrdersByIdRequest,
    ) -> OrdersResponse:
        """Заказы по id (order_ids XOR pos_order_ids, максимум 200).

        Raises:
            ValueError: оба списка заданы, оба пусты или len > 200
        """
        self._validate_orders_by_id(request)

        async def api_call() -> OrdersResponse:
            api = await self.get_deliveries_retrieve_api()
            return await api.get_deliveries_by_id(orders_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERIES_BY_ID, api_call
        )

    async def get_deliveries_by_revision(
        self,
        request: OrdersByRevisionRequest,
    ) -> OrdersWithRevisionResponse:
        """Изменённые заказы с ревизии (окно — 3 часа; инкрементальный поллинг)."""

        async def api_call() -> OrdersWithRevisionResponse:
            api = await self.get_deliveries_retrieve_api()
            return await api.get_deliveries_by_revision(
                orders_by_revision_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERIES_BY_REVISION, api_call
        )

    async def get_delivery_history_by_delivery_date_and_phone(
        self,
        request: OrdersHistoryByDeliveryDateAndPhoneRequest,
    ) -> OrdersWithRevisionResponse:
        """История заказов по телефону (хранение 90 дней, rows_count <= 200).

        Raises:
            ValueError: rows_count вне 1..200
        """
        self._validate_history_rows(request)

        async def api_call() -> OrdersWithRevisionResponse:
            api = await self.get_deliveries_retrieve_api()
            return await api.get_delivery_history_by_delivery_date_and_phone(
                orders_history_by_delivery_date_and_phone_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERY_HISTORY_BY_DELIVERY_DATE_AND_PHONE, api_call
        )

    async def search_deliveries(
        self,
        request: OrdersByDeliveryDateAndFilterRequest,
    ) -> OrdersWithRevisionResponse:
        """Поиск заказов по тексту и фильтрам (статусы, проблема, сортировка)."""

        async def api_call() -> OrdersWithRevisionResponse:
            api = await self.get_deliveries_retrieve_api()
            return await api.search_deliveries(
                orders_by_delivery_date_and_filter_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.SEARCH_DELIVERIES, api_call
        )

    @staticmethod
    def _validate_orders_by_id(request: OrdersByIdRequest) -> None:
        """XOR + непустой + <= 200 id (иначе гарантированный 400 от API)."""
        order_ids = request.order_ids or []
        pos_order_ids = request.pos_order_ids or []
        if order_ids and pos_order_ids:
            raise ValueError(
                "order_ids и pos_order_ids взаимоисключающие (XOR) — "
                "задайте только один список"
            )
        if not order_ids and not pos_order_ids:
            raise ValueError(
                "Нужен непустой order_ids или pos_order_ids"
            )
        if len(order_ids) > _MAX_IDS_PER_REQUEST or (
            len(pos_order_ids) > _MAX_IDS_PER_REQUEST
        ):
            raise ValueError(
                f"Максимум {_MAX_IDS_PER_REQUEST} id за запрос"
            )

    @staticmethod
    def _validate_history_rows(
        request: OrdersHistoryByDeliveryDateAndPhoneRequest,
    ) -> None:
        """rows_count в 1..200 (иначе гарантированный 400 от API)."""
        if not 1 <= request.rows_count <= _MAX_HISTORY_ROWS:
            raise ValueError(
                f"rows_count должен быть в диапазоне 1..{_MAX_HISTORY_ROWS}"
            )
