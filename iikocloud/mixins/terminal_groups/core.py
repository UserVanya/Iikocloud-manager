"""Terminal groups core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    TerminalGroupsIsAliveRequest,
    TerminalGroupsIsAliveResponse,
    TerminalGroupsRequest,
    TerminalGroupsResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class TerminalGroupsCoreMixin(_ManagerBase):
    """Core-методы Terminal Groups API."""

    async def get_terminal_groups(
        self,
        request: TerminalGroupsRequest,
    ) -> TerminalGroupsResponse:
        """Получить терминальные группы.

        Args:
            request: Параметры запроса TerminalGroupsRequest

        Returns:
            Ответ со списком терминальных групп
        """

        async def api_call() -> TerminalGroupsResponse:
            api = await self.get_terminal_groups_api()
            return await api.get_terminal_groups(
                terminal_groups_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_TERMINAL_GROUPS, api_call
        )

    async def check_terminal_groups_availability(
        self,
        request: TerminalGroupsIsAliveRequest,
    ) -> TerminalGroupsIsAliveResponse:
        """Проверить доступность терминальных групп.

        Args:
            request: Параметры запроса TerminalGroupsIsAliveRequest

        Returns:
            Ответ о доступности терминальных групп
        """

        async def api_call() -> TerminalGroupsIsAliveResponse:
            api = await self.get_terminal_groups_api()
            return await api.check_terminal_groups_availability(
                terminal_groups_is_alive_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHECK_TERMINAL_GROUPS_AVAILABILITY, api_call
        )
