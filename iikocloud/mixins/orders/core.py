"""Orders core mixin — прямые обёртки SDK через execute_with_retry."""

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
    GetTableOrdersByIdRequest,
    GetTableOrdersByTableRequest,
    InitTableOrderByPosOrderRequest,
    InitTableOrderRequest,
    TableOrderResponse,
    TableOrdersResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class OrdersCoreMixin(_ManagerBase):
    """Core-методы Orders API (столовые заказы)."""

    async def create_table_order(
        self, request: CreateTableOrderRequest
    ) -> TableOrderResponse:
        """Создать столовый заказ (синхронно, возвращает creation_status).

        Обязательные поля заказа: organization_id, terminal_group_id,
        order.items (непустой список).
        """

        async def api_call() -> TableOrderResponse:
            api = await self.get_orders_api()
            return await api.create_table_order(create_table_order_request=request)

        return await self.execute_with_retry(ApiMethod.CREATE_TABLE_ORDER, api_call)

    async def add_customer_to_table_order(
        self, request: AddCustomerToTableOrderRequest
    ) -> CorrelationIdResponse:
        """Привязать клиента к столовому заказу (команда)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_orders_api()
            return await api.add_customer_to_table_order(
                add_customer_to_table_order_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_CUSTOMER_TO_TABLE_ORDER, api_call
        )

    async def add_items_to_table_order(
        self, request: AddItemsToTableOrderRequest
    ) -> CorrelationIdResponse:
        """Добавить позиции в столовый заказ (команда)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_orders_api()
            return await api.add_items_to_table_order(
                add_items_to_table_order_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_ITEMS_TO_TABLE_ORDER, api_call
        )

    async def add_table_order_payments(
        self, request: AddOrderPaymentsRequest
    ) -> CorrelationIdResponse:
        """Добавить оплаты в столовый заказ (команда)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_orders_api()
            return await api.add_table_order_payments(
                add_order_payments_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_TABLE_ORDER_PAYMENTS, api_call
        )

    async def change_table_order_payments(
        self, request: ChangePaymentsRequest
    ) -> CorrelationIdResponse:
        """Изменить оплаты столового заказа (команда).

        Падает, если заказ уже processed (оплата проведена).
        """

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_orders_api()
            return await api.change_table_order_payments(
                change_payments_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_TABLE_ORDER_PAYMENTS, api_call
        )

    async def change_table_order_external_data(
        self, request: ChangeExternalDataRequest
    ) -> CorrelationIdResponse:
        """Изменить внешние данные столового заказа (команда)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_orders_api()
            return await api.change_table_order_external_data(
                change_external_data_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_TABLE_ORDER_EXTERNAL_DATA, api_call
        )

    async def close_table_order(
        self, request: CloseTableOrderRequest
    ) -> CorrelationIdResponse:
        """Закрыть столовый заказ (команда)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_orders_api()
            return await api.close_table_order(close_table_order_request=request)

        return await self.execute_with_retry(ApiMethod.CLOSE_TABLE_ORDER, api_call)

    async def cancel_table_order(
        self, request: CancelTableOrderRequest
    ) -> CorrelationIdResponse:
        """Отменить столовый заказ (команда; доступна только с API 9.0.5+)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_orders_api()
            return await api.cancel_table_order(cancel_table_order_request=request)

        return await self.execute_with_retry(ApiMethod.CANCEL_TABLE_ORDER, api_call)

    async def initialize_table_orders_by_pos_orders(
        self, request: InitTableOrderByPosOrderRequest
    ) -> CorrelationIdResponse:
        """Инициализировать столовые заказы по POS-заказам (команда)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_orders_api()
            return await api.initialize_table_orders_by_pos_orders(
                init_table_order_by_pos_order_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.INITIALIZE_TABLE_ORDERS_BY_POS_ORDERS, api_call
        )

    async def initialize_table_orders_by_tables(
        self, request: InitTableOrderRequest
    ) -> CorrelationIdResponse:
        """Инициализировать столовые заказы по столам (команда)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_orders_api()
            return await api.initialize_table_orders_by_tables(
                init_table_order_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.INITIALIZE_TABLE_ORDERS_BY_TABLES, api_call
        )

    async def get_table_orders_by_id(
        self, request: GetTableOrdersByIdRequest
    ) -> TableOrdersResponse:
        """Столовые заказы организаций по идентификаторам."""

        async def api_call() -> TableOrdersResponse:
            api = await self.get_orders_api()
            return await api.get_table_orders_by_id(
                get_table_orders_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_TABLE_ORDERS_BY_ID, api_call
        )

    async def get_table_orders_by_table(
        self, request: GetTableOrdersByTableRequest
    ) -> TableOrdersResponse:
        """Столовые заказы организаций по столам."""

        async def api_call() -> TableOrdersResponse:
            api = await self.get_orders_api()
            return await api.get_table_orders_by_table(
                get_table_orders_by_table_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_TABLE_ORDERS_BY_TABLE, api_call
        )
