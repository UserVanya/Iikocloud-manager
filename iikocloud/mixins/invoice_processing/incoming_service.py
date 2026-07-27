"""Invoice Processing incoming service core mixin — обёртки SDK."""

from iikocloud_client import (
    GetByIDRequest,
    IncomingServiceCreateRequest,
    IncomingServiceGetResponse,
    IncomingServiceListItem,
    IncomingServiceSaveResponse,
    IncomingServiceUpdateRequest,
    ListRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class IncomingServiceCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: акты прихода услуг."""

    async def create_finance_incoming_service(
        self, request: IncomingServiceCreateRequest
    ) -> IncomingServiceSaveResponse:
        """Создать акт прихода услуг."""

        async def api_call() -> IncomingServiceSaveResponse:
            api = await self.get_incoming_service_api()
            return await api.create_finance_incoming_service(
                incoming_service_create_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_FINANCE_INCOMING_SERVICE, api_call
        )

    async def update_finance_incoming_service(
        self, request: IncomingServiceUpdateRequest
    ) -> IncomingServiceSaveResponse:
        """Обновить акт прихода услуг."""

        async def api_call() -> IncomingServiceSaveResponse:
            api = await self.get_incoming_service_api()
            return await api.update_finance_incoming_service(
                incoming_service_update_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_FINANCE_INCOMING_SERVICE, api_call
        )

    async def get_finance_incoming_service(
        self, request: GetByIDRequest
    ) -> IncomingServiceGetResponse:
        """Акт прихода услуг по id."""

        async def api_call() -> IncomingServiceGetResponse:
            api = await self.get_incoming_service_api()
            return await api.get_finance_incoming_service(get_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_FINANCE_INCOMING_SERVICE, api_call
        )

    async def list_finance_incoming_services(
        self, request: ListRequest
    ) -> list[IncomingServiceListItem]:
        """Список актов прихода услуг за период."""

        async def api_call() -> list[IncomingServiceListItem]:
            api = await self.get_incoming_service_api()
            return await api.list_finance_incoming_services(list_request=request)

        return await self.execute_with_retry(
            ApiMethod.LIST_FINANCE_INCOMING_SERVICES, api_call
        )

    async def post_finance_incoming_service(
        self, request: GetByIDRequest
    ) -> IncomingServiceSaveResponse:
        """Провести акт прихода услуг."""

        async def api_call() -> IncomingServiceSaveResponse:
            api = await self.get_incoming_service_api()
            return await api.post_finance_incoming_service(get_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.POST_FINANCE_INCOMING_SERVICE, api_call
        )

    async def unpost_finance_incoming_service(
        self, request: GetByIDRequest
    ) -> IncomingServiceSaveResponse:
        """Отменить проведение акта прихода услуг."""

        async def api_call() -> IncomingServiceSaveResponse:
            api = await self.get_incoming_service_api()
            return await api.unpost_finance_incoming_service(get_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.UNPOST_FINANCE_INCOMING_SERVICE, api_call
        )

    async def cancel_finance_incoming_service(
        self, request: GetByIDRequest
    ) -> IncomingServiceSaveResponse:
        """Отменить (удалить) акт прихода услуг."""

        async def api_call() -> IncomingServiceSaveResponse:
            api = await self.get_incoming_service_api()
            return await api.cancel_finance_incoming_service(get_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.CANCEL_FINANCE_INCOMING_SERVICE, api_call
        )
