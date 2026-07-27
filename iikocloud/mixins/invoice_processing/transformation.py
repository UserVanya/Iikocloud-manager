"""Invoice Processing transformation document core mixin — обёртки SDK."""

from iikocloud_client import (
    GetByIDRequest,
    ListRequest,
    TransformationDocumentCreateRequest,
    TransformationDocumentGetResponse,
    TransformationDocumentListItem,
    TransformationDocumentSaveResponse,
    TransformationDocumentUpdateRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class TransformationCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: акты переработки (transformation documents)."""

    async def create_inventory_transformation_document(
        self, request: TransformationDocumentCreateRequest
    ) -> TransformationDocumentSaveResponse:
        """Создать акт переработки."""

        async def api_call() -> TransformationDocumentSaveResponse:
            api = await self.get_transformation_document_api()
            return await api.create_inventory_transformation_document(
                transformation_document_create_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_INVENTORY_TRANSFORMATION_DOCUMENT, api_call
        )

    async def update_inventory_transformation_document(
        self, request: TransformationDocumentUpdateRequest
    ) -> TransformationDocumentSaveResponse:
        """Обновить акт переработки."""

        async def api_call() -> TransformationDocumentSaveResponse:
            api = await self.get_transformation_document_api()
            return await api.update_inventory_transformation_document(
                transformation_document_update_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_INVENTORY_TRANSFORMATION_DOCUMENT, api_call
        )

    async def get_inventory_transformation_document(
        self, request: GetByIDRequest
    ) -> TransformationDocumentGetResponse:
        """Акт переработки по id."""

        async def api_call() -> TransformationDocumentGetResponse:
            api = await self.get_transformation_document_api()
            return await api.get_inventory_transformation_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_INVENTORY_TRANSFORMATION_DOCUMENT, api_call
        )

    async def list_inventory_transformation_documents(
        self, request: ListRequest
    ) -> list[TransformationDocumentListItem]:
        """Список актов переработки за период."""

        async def api_call() -> list[TransformationDocumentListItem]:
            api = await self.get_transformation_document_api()
            return await api.list_inventory_transformation_documents(
                list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.LIST_INVENTORY_TRANSFORMATION_DOCUMENTS, api_call
        )

    async def post_inventory_transformation_document(
        self, request: GetByIDRequest
    ) -> TransformationDocumentSaveResponse:
        """Провести акт переработки."""

        async def api_call() -> TransformationDocumentSaveResponse:
            api = await self.get_transformation_document_api()
            return await api.post_inventory_transformation_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.POST_INVENTORY_TRANSFORMATION_DOCUMENT, api_call
        )

    async def unpost_inventory_transformation_document(
        self, request: GetByIDRequest
    ) -> TransformationDocumentSaveResponse:
        """Отменить проведение акта переработки."""

        async def api_call() -> TransformationDocumentSaveResponse:
            api = await self.get_transformation_document_api()
            return await api.unpost_inventory_transformation_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UNPOST_INVENTORY_TRANSFORMATION_DOCUMENT, api_call
        )

    async def cancel_inventory_transformation_document(
        self, request: GetByIDRequest
    ) -> TransformationDocumentSaveResponse:
        """Отменить (удалить) акт переработки."""

        async def api_call() -> TransformationDocumentSaveResponse:
            api = await self.get_transformation_document_api()
            return await api.cancel_inventory_transformation_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CANCEL_INVENTORY_TRANSFORMATION_DOCUMENT, api_call
        )
