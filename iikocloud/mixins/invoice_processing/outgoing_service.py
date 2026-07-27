"""Invoice Processing outgoing service core mixin — обёртки SDK."""

from iikocloud_client import (
    GetByIDRequest,
    ListRequest,
    OutgoingServiceCreateRequest,
    OutgoingServiceGetResponse,
    OutgoingServiceListItem,
    OutgoingServiceSaveResponse,
    OutgoingServiceUpdateRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class OutgoingServiceCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: акты расхода услуг."""

    async def create_finance_outgoing_service(
        self, request: OutgoingServiceCreateRequest
    ) -> OutgoingServiceSaveResponse:
        """Создать акт расхода услуг."""

        async def api_call() -> OutgoingServiceSaveResponse:
            api = await self.get_outgoing_service_api()
            return await api.create_finance_outgoing_service(
                outgoing_service_create_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_FINANCE_OUTGOING_SERVICE, api_call
        )

    async def update_finance_outgoing_service(
        self, request: OutgoingServiceUpdateRequest
    ) -> OutgoingServiceSaveResponse:
        """Обновить акт расхода услуг."""

        async def api_call() -> OutgoingServiceSaveResponse:
            api = await self.get_outgoing_service_api()
            return await api.update_finance_outgoing_service(
                outgoing_service_update_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_FINANCE_OUTGOING_SERVICE, api_call
        )

    async def get_finance_outgoing_service(
        self, request: GetByIDRequest
    ) -> OutgoingServiceGetResponse:
        """Акт расхода услуг по id."""

        async def api_call() -> OutgoingServiceGetResponse:
            api = await self.get_outgoing_service_api()
            return await api.get_finance_outgoing_service(get_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_FINANCE_OUTGOING_SERVICE, api_call
        )

    async def list_finance_outgoing_services(
        self, request: ListRequest
    ) -> list[OutgoingServiceListItem]:
        """Список актов расхода услуг за период."""

        async def api_call() -> list[OutgoingServiceListItem]:
            api = await self.get_outgoing_service_api()
            return await api.list_finance_outgoing_services(list_request=request)

        return await self.execute_with_retry(
            ApiMethod.LIST_FINANCE_OUTGOING_SERVICES, api_call
        )

    async def post_finance_outgoing_service(
        self, request: GetByIDRequest
    ) -> OutgoingServiceSaveResponse:
        """Провести акт расхода услуг."""

        async def api_call() -> OutgoingServiceSaveResponse:
            api = await self.get_outgoing_service_api()
            return await api.post_finance_outgoing_service(get_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.POST_FINANCE_OUTGOING_SERVICE, api_call
        )

    async def unpost_finance_outgoing_service(
        self, request: GetByIDRequest
    ) -> OutgoingServiceSaveResponse:
        """Отменить проведение акта расхода услуг."""

        async def api_call() -> OutgoingServiceSaveResponse:
            api = await self.get_outgoing_service_api()
            return await api.unpost_finance_outgoing_service(get_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.UNPOST_FINANCE_OUTGOING_SERVICE, api_call
        )

    async def cancel_finance_outgoing_service(
        self, request: GetByIDRequest
    ) -> OutgoingServiceSaveResponse:
        """Отменить (удалить) акт расхода услуг."""

        async def api_call() -> OutgoingServiceSaveResponse:
            api = await self.get_outgoing_service_api()
            return await api.cancel_finance_outgoing_service(get_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.CANCEL_FINANCE_OUTGOING_SERVICE, api_call
        )
