"""Menu core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    AddProductsToStopListRequest,
    CalculateComboPriceRequest,
    CalculateComboPriceResponse,
    CheckStopListRequest,
    CheckStopListResponse,
    ClearStopListRequest,
    CorrelationIdResponse,
    ExternalMenuResponse,
    GetCombosInfoRequest,
    GetCombosInfoResponse,
    MenuRequest,
    MenusDataResponse,
    NomenclatureRequest,
    NomenclatureResponse,
    RemoveProductsFromStopListRequest,
    StopListsRequest,
    StopListsResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class MenuCoreMixin(_ManagerBase):
    """Core-методы Menu API."""

    async def get_external_menus(self) -> MenusDataResponse:
        """Получить список внешних меню.

        Returns:
            Ответ со списком внешних меню
        """

        async def api_call() -> MenusDataResponse:
            api = await self.get_menu_api()
            return await api.get_external_menus()

        return await self.execute_with_retry(
            ApiMethod.GET_EXTERNAL_MENUS, api_call
        )

    async def get_external_menu_by_id(
        self,
        menu_request: MenuRequest,
    ) -> ExternalMenuResponse:
        """Получить внешнее меню по ID.

        Args:
            menu_request: Параметры запроса MenuRequest

        Returns:
            Ответ с данными внешнего меню
        """

        async def api_call() -> ExternalMenuResponse:
            api = await self.get_menu_api()
            return await api.get_external_menu_by_id(
                menu_request=menu_request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_EXTERNAL_MENU_BY_ID, api_call
        )

    async def get_stop_lists(
        self,
        request: StopListsRequest,
    ) -> StopListsResponse:
        """Получить стоп-листы.

        Args:
            request: Параметры запроса StopListsRequest

        Returns:
            Ответ со стоп-листами
        """

        async def api_call() -> StopListsResponse:
            api = await self.get_menu_api()
            return await api.get_stop_lists(stop_lists_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_STOP_LISTS, api_call
        )

    async def add_products_to_stop_list(
        self,
        request: AddProductsToStopListRequest,
    ) -> CorrelationIdResponse:
        """Добавить продукты в стоп-лист (async-операция, iiko >= 8.6.1).

        Returns:
            CorrelationIdResponse — статус применения через /api/1/commands/status
        """

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_menu_api()
            return await api.add_products_to_stop_list(
                add_products_to_stop_list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_PRODUCTS_TO_STOP_LIST, api_call
        )

    async def remove_products_from_stop_list(
        self,
        request: RemoveProductsFromStopListRequest,
    ) -> CorrelationIdResponse:
        """Убрать продукты из стоп-листа (async-операция, iiko >= 8.6.1)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_menu_api()
            return await api.remove_products_from_stop_list(
                remove_products_from_stop_list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.REMOVE_PRODUCTS_FROM_STOP_LIST, api_call
        )

    async def clear_stop_list(
        self,
        request: ClearStopListRequest,
    ) -> CorrelationIdResponse:
        """Очистить стоп-лист терминальной группы (async-операция)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_menu_api()
            return await api.clear_stop_list(clear_stop_list_request=request)

        return await self.execute_with_retry(ApiMethod.CLEAR_STOP_LIST, api_call)

    async def check_products_in_stop_list(
        self,
        request: CheckStopListRequest,
    ) -> CheckStopListResponse:
        """Проверить позиции заказа на наличие в стоп-листе.

        items — DeliveryOrderCreateProductItem (type="Product").
        rejectedItems == None означает «ничего не в стоп-листе».
        """

        async def api_call() -> CheckStopListResponse:
            api = await self.get_menu_api()
            return await api.check_products_in_stop_list(
                check_stop_list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHECK_PRODUCTS_IN_STOP_LIST, api_call
        )

    async def get_nomenclature(
        self,
        request: NomenclatureRequest,
    ) -> NomenclatureResponse:
        """Номенклатура организации (группы, продукты, размеры).

        Дельта-синхронизация: start_revision=0 — полная выгрузка;
        далее — revision из предыдущего ответа. Если revision ответа
        == start_revision, меню не менялось (списки пустые).
        Лимит iiko: не более 5 организаций за раз от одного API-логина,
        не чаще раза в минуту.
        """

        async def api_call() -> NomenclatureResponse:
            api = await self.get_menu_api()
            return await api.get_nomenclature(nomenclature_request=request)

        return await self.execute_with_retry(ApiMethod.GET_NOMENCLATURE, api_call)

    async def get_combos_info(
        self,
        request: GetCombosInfoRequest,
    ) -> GetCombosInfoResponse:
        """Все комбо организации (категории и спецификации)."""

        async def api_call() -> GetCombosInfoResponse:
            api = await self.get_menu_api()
            return await api.get_combos_info(get_combos_info_request=request)

        return await self.execute_with_retry(ApiMethod.GET_COMBOS_INFO, api_call)

    async def calculate_combo_price(
        self,
        request: CalculateComboPriceRequest,
    ) -> CalculateComboPriceResponse:
        """Расчёт цены комбо по позициям.

        Если incorrectlyFilledGroups не пуст — price будет 0.
        """

        async def api_call() -> CalculateComboPriceResponse:
            api = await self.get_menu_api()
            return await api.calculate_combo_price(
                calculate_combo_price_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CALCULATE_COMBO_PRICE, api_call
        )
