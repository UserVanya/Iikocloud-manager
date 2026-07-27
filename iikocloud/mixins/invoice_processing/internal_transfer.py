"""Invoice Processing internal transfer core mixin — обёртки SDK."""

from iikocloud_client import (
    GetByIDRequest,
    InternalTransferCreateRequest,
    InternalTransferGetResponse,
    InternalTransferListItem,
    InternalTransferSaveResponse,
    InternalTransferUpdateRequest,
    ListRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class InternalTransferCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: документы внутреннего перемещения."""

    async def create_inventory_internal_transfer(
        self, request: InternalTransferCreateRequest
    ) -> InternalTransferSaveResponse:
        """Создать документ внутреннего перемещения."""

        async def api_call() -> InternalTransferSaveResponse:
            api = await self.get_internal_transfer_api()
            return await api.create_inventory_internal_transfer(
                internal_transfer_create_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_INVENTORY_INTERNAL_TRANSFER, api_call
        )

    async def update_inventory_internal_transfer(
        self, request: InternalTransferUpdateRequest
    ) -> InternalTransferSaveResponse:
        """Обновить документ внутреннего перемещения."""

        async def api_call() -> InternalTransferSaveResponse:
            api = await self.get_internal_transfer_api()
            return await api.update_inventory_internal_transfer(
                internal_transfer_update_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_INVENTORY_INTERNAL_TRANSFER, api_call
        )

    async def get_inventory_internal_transfer(
        self, request: GetByIDRequest
    ) -> InternalTransferGetResponse:
        """Документ внутреннего перемещения по id."""

        async def api_call() -> InternalTransferGetResponse:
            api = await self.get_internal_transfer_api()
            return await api.get_inventory_internal_transfer(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_INVENTORY_INTERNAL_TRANSFER, api_call
        )

    async def list_inventory_internal_transfers(
        self, request: ListRequest
    ) -> list[InternalTransferListItem]:
        """Список документов внутреннего перемещения за период."""

        async def api_call() -> list[InternalTransferListItem]:
            api = await self.get_internal_transfer_api()
            return await api.list_inventory_internal_transfers(list_request=request)

        return await self.execute_with_retry(
            ApiMethod.LIST_INVENTORY_INTERNAL_TRANSFERS, api_call
        )

    async def post_inventory_internal_transfer(
        self, request: GetByIDRequest
    ) -> InternalTransferSaveResponse:
        """Провести документ внутреннего перемещения."""

        async def api_call() -> InternalTransferSaveResponse:
            api = await self.get_internal_transfer_api()
            return await api.post_inventory_internal_transfer(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.POST_INVENTORY_INTERNAL_TRANSFER, api_call
        )

    async def unpost_inventory_internal_transfer(
        self, request: GetByIDRequest
    ) -> InternalTransferSaveResponse:
        """Отменить проведение документа внутреннего перемещения."""

        async def api_call() -> InternalTransferSaveResponse:
            api = await self.get_internal_transfer_api()
            return await api.unpost_inventory_internal_transfer(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UNPOST_INVENTORY_INTERNAL_TRANSFER, api_call
        )

    async def cancel_inventory_internal_transfer(
        self, request: GetByIDRequest
    ) -> InternalTransferSaveResponse:
        """Отменить (удалить) документ внутреннего перемещения."""

        async def api_call() -> InternalTransferSaveResponse:
            api = await self.get_internal_transfer_api()
            return await api.cancel_inventory_internal_transfer(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CANCEL_INVENTORY_INTERNAL_TRANSFER, api_call
        )
