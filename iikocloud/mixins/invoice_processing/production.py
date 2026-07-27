"""Invoice Processing production document core mixin — обёртки SDK."""

from iikocloud_client import (
    GetByIDRequest,
    ListRequest,
    ProductionDocumentCreateRequest,
    ProductionDocumentGetResponse,
    ProductionDocumentListItem,
    ProductionDocumentSaveResponse,
    ProductionDocumentUpdateRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class ProductionCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: акты производства (production documents)."""

    async def create_inventory_production_document(
        self, request: ProductionDocumentCreateRequest
    ) -> ProductionDocumentSaveResponse:
        """Создать акт производства."""

        async def api_call() -> ProductionDocumentSaveResponse:
            api = await self.get_production_document_api()
            return await api.create_inventory_production_document(
                production_document_create_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_INVENTORY_PRODUCTION_DOCUMENT, api_call
        )

    async def update_inventory_production_document(
        self, request: ProductionDocumentUpdateRequest
    ) -> ProductionDocumentSaveResponse:
        """Обновить акт производства."""

        async def api_call() -> ProductionDocumentSaveResponse:
            api = await self.get_production_document_api()
            return await api.update_inventory_production_document(
                production_document_update_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_INVENTORY_PRODUCTION_DOCUMENT, api_call
        )

    async def get_inventory_production_document(
        self, request: GetByIDRequest
    ) -> ProductionDocumentGetResponse:
        """Акт производства по id."""

        async def api_call() -> ProductionDocumentGetResponse:
            api = await self.get_production_document_api()
            return await api.get_inventory_production_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_INVENTORY_PRODUCTION_DOCUMENT, api_call
        )

    async def list_inventory_production_documents(
        self, request: ListRequest
    ) -> list[ProductionDocumentListItem]:
        """Список актов производства за период."""

        async def api_call() -> list[ProductionDocumentListItem]:
            api = await self.get_production_document_api()
            return await api.list_inventory_production_documents(
                list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.LIST_INVENTORY_PRODUCTION_DOCUMENTS, api_call
        )

    async def post_inventory_production_document(
        self, request: GetByIDRequest
    ) -> ProductionDocumentSaveResponse:
        """Провести акт производства."""

        async def api_call() -> ProductionDocumentSaveResponse:
            api = await self.get_production_document_api()
            return await api.post_inventory_production_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.POST_INVENTORY_PRODUCTION_DOCUMENT, api_call
        )

    async def unpost_inventory_production_document(
        self, request: GetByIDRequest
    ) -> ProductionDocumentSaveResponse:
        """Отменить проведение акта производства."""

        async def api_call() -> ProductionDocumentSaveResponse:
            api = await self.get_production_document_api()
            return await api.unpost_inventory_production_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UNPOST_INVENTORY_PRODUCTION_DOCUMENT, api_call
        )

    async def cancel_inventory_production_document(
        self, request: GetByIDRequest
    ) -> ProductionDocumentSaveResponse:
        """Отменить (удалить) акт производства."""

        async def api_call() -> ProductionDocumentSaveResponse:
            api = await self.get_production_document_api()
            return await api.cancel_inventory_production_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CANCEL_INVENTORY_PRODUCTION_DOCUMENT, api_call
        )
