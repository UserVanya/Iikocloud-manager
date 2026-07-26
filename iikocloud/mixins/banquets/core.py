"""Banquets & Reserves core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    AddOrderItemsToBanquetRequest,
    AddOrderPaymentsToBanquetRequest,
    CancelReserveRequest,
    ChangeBanquetOrderItemsRequest,
    ChangeReserveEstimatedStartTimeRequest,
    ChangeReserveTablesRequest,
    CorrelationIdResponse,
    CreateReserveRequest,
    GetOrganizationsRequest,
    GetOrganizationsResponse,
    GetRestaurantSectionsRequest,
    GetRestaurantSectionsResponse,
    GetRestaurantSectionsWorkloadRequest,
    GetRestaurantSectionsWorkloadResponse,
    GetTerminalGroupsByOrganizationsRequest,
    ReserveResponse,
    ReservesByIdRequest,
    ReservesResponse,
    TerminalGroupsResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class BanquetsCoreMixin(_ManagerBase):
    """Core-методы Banquets & Reserves API (резервы, банкеты, секции)."""

    async def get_reserve_available_organizations(
        self, request: GetOrganizationsRequest
    ) -> GetOrganizationsResponse:
        """Организации, доступные для резервирования."""

        async def api_call() -> GetOrganizationsResponse:
            api = await self.get_banquets_reserves_api()
            return await api.get_reserve_available_organizations(
                get_organizations_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_RESERVE_AVAILABLE_ORGANIZATIONS, api_call
        )

    async def get_reserve_terminal_groups(
        self, request: GetTerminalGroupsByOrganizationsRequest
    ) -> TerminalGroupsResponse:
        """Терминальные группы организаций, доступные для резервирования."""

        async def api_call() -> TerminalGroupsResponse:
            api = await self.get_banquets_reserves_api()
            return await api.get_reserve_terminal_groups(
                get_terminal_groups_by_organizations_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_RESERVE_TERMINAL_GROUPS, api_call
        )

    async def get_reserve_restaurant_sections(
        self, request: GetRestaurantSectionsRequest
    ) -> GetRestaurantSectionsResponse:
        """Секции (залы) ресторана со схемой столов."""

        async def api_call() -> GetRestaurantSectionsResponse:
            api = await self.get_banquets_reserves_api()
            return await api.get_reserve_restaurant_sections(
                get_restaurant_sections_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_RESERVE_RESTAURANT_SECTIONS, api_call
        )

    async def get_reserve_statuses_by_id(
        self, request: ReservesByIdRequest
    ) -> ReservesResponse:
        """Статусы резервов по их идентификаторам."""

        async def api_call() -> ReservesResponse:
            api = await self.get_banquets_reserves_api()
            return await api.get_reserve_statuses_by_id(reserves_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_RESERVE_STATUSES_BY_ID, api_call
        )

    async def get_restaurant_sections_workload(
        self, request: GetRestaurantSectionsWorkloadRequest
    ) -> GetRestaurantSectionsWorkloadResponse:
        """Загруженность секций ресторана с указанной даты."""

        async def api_call() -> GetRestaurantSectionsWorkloadResponse:
            api = await self.get_banquets_reserves_api()
            return await api.get_restaurant_sections_workload(
                get_restaurant_sections_workload_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_RESTAURANT_SECTIONS_WORKLOAD, api_call
        )

    async def create_reserve(self, request: CreateReserveRequest) -> ReserveResponse:
        """Создать резерв (банкет).

        Обязательные поля запроса: organization_id, phone, customer,
        estimated_start_time, duration_in_minutes, should_remind, table_ids.
        Успех создания проверяется по полю creation_status ответа.
        """

        async def api_call() -> ReserveResponse:
            api = await self.get_banquets_reserves_api()
            return await api.create_reserve(create_reserve_request=request)

        return await self.execute_with_retry(ApiMethod.CREATE_RESERVE, api_call)

    async def add_banquet_order_items(
        self, request: AddOrderItemsToBanquetRequest
    ) -> CorrelationIdResponse:
        """Добавить позиции в заказ банкета (команда, ответ — correlation_id)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_banquets_reserves_api()
            return await api.add_banquet_order_items(
                add_order_items_to_banquet_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_BANQUET_ORDER_ITEMS, api_call
        )

    async def add_banquet_order_payments(
        self, request: AddOrderPaymentsToBanquetRequest
    ) -> CorrelationIdResponse:
        """Добавить оплаты в заказ банкета (команда, ответ — correlation_id)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_banquets_reserves_api()
            return await api.add_banquet_order_payments(
                add_order_payments_to_banquet_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_BANQUET_ORDER_PAYMENTS, api_call
        )

    async def cancel_reserve(self, request: CancelReserveRequest) -> CorrelationIdResponse:
        """Отменить резерв (команда).

        Отменить можно только резерв в статусе New; cancel_reason обязателен.
        Ответ — correlation_id команды.
        """

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_banquets_reserves_api()
            return await api.cancel_reserve(cancel_reserve_request=request)

        return await self.execute_with_retry(ApiMethod.CANCEL_RESERVE, api_call)

    async def change_banquet_order_items(
        self, request: ChangeBanquetOrderItemsRequest
    ) -> CorrelationIdResponse:
        """Изменить состав заказа банкета (команда, ответ — correlation_id)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_banquets_reserves_api()
            return await api.change_banquet_order_items(
                change_banquet_order_items_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_BANQUET_ORDER_ITEMS, api_call
        )

    async def change_reserve_estimated_start_time(
        self, request: ChangeReserveEstimatedStartTimeRequest
    ) -> CorrelationIdResponse:
        """Перенести предполагаемое время начала резерва (команда)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_banquets_reserves_api()
            return await api.change_reserve_estimated_start_time(
                change_reserve_estimated_start_time_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_RESERVE_ESTIMATED_START_TIME, api_call
        )

    async def change_reserve_tables(
        self, request: ChangeReserveTablesRequest
    ) -> CorrelationIdResponse:
        """Изменить столы резерва (команда, ответ — correlation_id)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_banquets_reserves_api()
            return await api.change_reserve_tables(change_reserve_tables_request=request)

        return await self.execute_with_retry(
            ApiMethod.CHANGE_RESERVE_TABLES, api_call
        )
