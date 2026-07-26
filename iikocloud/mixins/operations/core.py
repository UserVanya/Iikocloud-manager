"""Operations core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import GetCommandStatusRequest, GetCommandStatusResponse

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class OperationsCoreMixin(_ManagerBase):
    """Core-методы Operations API (статусы асинхронных команд)."""

    async def get_command_status(
        self,
        request: GetCommandStatusRequest,
    ) -> GetCommandStatusResponse:
        """Статус команды по correlation_id (Success/InProgress/Error).

        HTTP 410 — correlationId устарел, polling прекращать. SDK-исключение
        ApiException со status=410 пробрасывается вызывающему как есть
        (в проекте нет отдельного исключения для этой ситуации).
        """

        async def api_call() -> GetCommandStatusResponse:
            api = await self.get_operations_api()
            return await api.get_command_status(
                get_command_status_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_COMMAND_STATUS, api_call
        )
