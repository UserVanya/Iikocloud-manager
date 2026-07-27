"""Invoice Processing writeoff document core mixin — обёртки SDK."""

from iikocloud_client import (
    GetByIDRequest,
    ListRequest,
    WriteoffDocumentCreateRequest,
    WriteoffDocumentGetResponse,
    WriteoffDocumentListItem,
    WriteoffDocumentSaveResponse,
    WriteoffDocumentUpdateRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class WriteoffCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: акты списания (writeoff documents)."""

    async def create_inventory_writeoff_document(
        self, request: WriteoffDocumentCreateRequest
    ) -> WriteoffDocumentSaveResponse:
        """Создать акт списания."""

        async def api_call() -> WriteoffDocumentSaveResponse:
            api = await self.get_writeoff_document_api()
            return await api.create_inventory_writeoff_document(
                writeoff_document_create_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_INVENTORY_WRITEOFF_DOCUMENT, api_call
        )

    async def update_inventory_writeoff_document(
        self, request: WriteoffDocumentUpdateRequest
    ) -> WriteoffDocumentSaveResponse:
        """Обновить акт списания."""

        async def api_call() -> WriteoffDocumentSaveResponse:
            api = await self.get_writeoff_document_api()
            return await api.update_inventory_writeoff_document(
                writeoff_document_update_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_INVENTORY_WRITEOFF_DOCUMENT, api_call
        )

    async def get_inventory_writeoff_document(
        self, request: GetByIDRequest
    ) -> WriteoffDocumentGetResponse:
        """Акт списания по id."""

        async def api_call() -> WriteoffDocumentGetResponse:
            api = await self.get_writeoff_document_api()
            return await api.get_inventory_writeoff_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_INVENTORY_WRITEOFF_DOCUMENT, api_call
        )

    async def list_inventory_writeoff_documents(
        self, request: ListRequest
    ) -> list[WriteoffDocumentListItem]:
        """Список актов списания за период."""

        async def api_call() -> list[WriteoffDocumentListItem]:
            api = await self.get_writeoff_document_api()
            return await api.list_inventory_writeoff_documents(
                list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.LIST_INVENTORY_WRITEOFF_DOCUMENTS, api_call
        )

    async def post_inventory_writeoff_document(
        self, request: GetByIDRequest
    ) -> WriteoffDocumentSaveResponse:
        """Провести акт списания."""

        async def api_call() -> WriteoffDocumentSaveResponse:
            api = await self.get_writeoff_document_api()
            return await api.post_inventory_writeoff_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.POST_INVENTORY_WRITEOFF_DOCUMENT, api_call
        )

    async def unpost_inventory_writeoff_document(
        self, request: GetByIDRequest
    ) -> WriteoffDocumentSaveResponse:
        """Отменить проведение акта списания."""

        async def api_call() -> WriteoffDocumentSaveResponse:
            api = await self.get_writeoff_document_api()
            return await api.unpost_inventory_writeoff_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UNPOST_INVENTORY_WRITEOFF_DOCUMENT, api_call
        )

    async def cancel_inventory_writeoff_document(
        self, request: GetByIDRequest
    ) -> WriteoffDocumentSaveResponse:
        """Отменить (удалить) акт списания."""

        async def api_call() -> WriteoffDocumentSaveResponse:
            api = await self.get_writeoff_document_api()
            return await api.cancel_inventory_writeoff_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CANCEL_INVENTORY_WRITEOFF_DOCUMENT, api_call
        )
