"""Menu core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    ExternalMenuResponse,
    MenuRequest,
    MenusDataResponse,
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
