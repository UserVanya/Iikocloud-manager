"""Invoice Processing sales document core mixin — обёртки SDK."""

from iikocloud_client import (
    GetByIDRequest,
    ListRequest,
    SalesDocumentCreateRequest,
    SalesDocumentGetResponse,
    SalesDocumentListItem,
    SalesDocumentSaveResponse,
    SalesDocumentUpdateRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class SalesCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: документы продажи."""

    async def create_inventory_sales_document(
        self, request: SalesDocumentCreateRequest
    ) -> SalesDocumentSaveResponse:
        """Создать документ продажи."""

        async def api_call() -> SalesDocumentSaveResponse:
            api = await self.get_sales_document_api()
            return await api.create_inventory_sales_document(
                sales_document_create_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_INVENTORY_SALES_DOCUMENT, api_call
        )

    async def update_inventory_sales_document(
        self, request: SalesDocumentUpdateRequest
    ) -> SalesDocumentSaveResponse:
        """Обновить документ продажи."""

        async def api_call() -> SalesDocumentSaveResponse:
            api = await self.get_sales_document_api()
            return await api.update_inventory_sales_document(
                sales_document_update_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_INVENTORY_SALES_DOCUMENT, api_call
        )

    async def get_inventory_sales_document(
        self, request: GetByIDRequest
    ) -> SalesDocumentGetResponse:
        """Документ продажи по id."""

        async def api_call() -> SalesDocumentGetResponse:
            api = await self.get_sales_document_api()
            return await api.get_inventory_sales_document(get_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_INVENTORY_SALES_DOCUMENT, api_call
        )

    async def list_inventory_sales_documents(
        self, request: ListRequest
    ) -> list[SalesDocumentListItem]:
        """Список документов продажи за период."""

        async def api_call() -> list[SalesDocumentListItem]:
            api = await self.get_sales_document_api()
            return await api.list_inventory_sales_documents(list_request=request)

        return await self.execute_with_retry(
            ApiMethod.LIST_INVENTORY_SALES_DOCUMENTS, api_call
        )

    async def post_inventory_sales_document(
        self, request: GetByIDRequest
    ) -> SalesDocumentSaveResponse:
        """Провести документ продажи."""

        async def api_call() -> SalesDocumentSaveResponse:
            api = await self.get_sales_document_api()
            return await api.post_inventory_sales_document(get_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.POST_INVENTORY_SALES_DOCUMENT, api_call
        )

    async def unpost_inventory_sales_document(
        self, request: GetByIDRequest
    ) -> SalesDocumentSaveResponse:
        """Отменить проведение документа продажи."""

        async def api_call() -> SalesDocumentSaveResponse:
            api = await self.get_sales_document_api()
            return await api.unpost_inventory_sales_document(get_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.UNPOST_INVENTORY_SALES_DOCUMENT, api_call
        )

    async def cancel_inventory_sales_document(
        self, request: GetByIDRequest
    ) -> SalesDocumentSaveResponse:
        """Отменить (удалить) документ продажи."""

        async def api_call() -> SalesDocumentSaveResponse:
            api = await self.get_sales_document_api()
            return await api.cancel_inventory_sales_document(get_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.CANCEL_INVENTORY_SALES_DOCUMENT, api_call
        )
