"""Invoice Processing disassemble document core mixin — обёртки SDK."""

from iikocloud_client import (
    DisassembleDocumentCreateRequest,
    DisassembleDocumentGetResponse,
    DisassembleDocumentListItem,
    DisassembleDocumentSaveResponse,
    DisassembleDocumentUpdateRequest,
    GetByIDRequest,
    ListRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class DisassembleCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: акты разборки (disassemble documents)."""

    async def create_inventory_disassemble_document(
        self, request: DisassembleDocumentCreateRequest
    ) -> DisassembleDocumentSaveResponse:
        """Создать акт разборки."""

        async def api_call() -> DisassembleDocumentSaveResponse:
            api = await self.get_disassemble_document_api()
            return await api.create_inventory_disassemble_document(
                disassemble_document_create_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_INVENTORY_DISASSEMBLE_DOCUMENT, api_call
        )

    async def update_inventory_disassemble_document(
        self, request: DisassembleDocumentUpdateRequest
    ) -> DisassembleDocumentSaveResponse:
        """Обновить акт разборки."""

        async def api_call() -> DisassembleDocumentSaveResponse:
            api = await self.get_disassemble_document_api()
            return await api.update_inventory_disassemble_document(
                disassemble_document_update_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_INVENTORY_DISASSEMBLE_DOCUMENT, api_call
        )

    async def get_inventory_disassemble_document(
        self, request: GetByIDRequest
    ) -> DisassembleDocumentGetResponse:
        """Акт разборки по id."""

        async def api_call() -> DisassembleDocumentGetResponse:
            api = await self.get_disassemble_document_api()
            return await api.get_inventory_disassemble_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_INVENTORY_DISASSEMBLE_DOCUMENT, api_call
        )

    async def list_inventory_disassemble_documents(
        self, request: ListRequest
    ) -> list[DisassembleDocumentListItem]:
        """Список актов разборки за период."""

        async def api_call() -> list[DisassembleDocumentListItem]:
            api = await self.get_disassemble_document_api()
            return await api.list_inventory_disassemble_documents(
                list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.LIST_INVENTORY_DISASSEMBLE_DOCUMENTS, api_call
        )

    async def post_inventory_disassemble_document(
        self, request: GetByIDRequest
    ) -> DisassembleDocumentSaveResponse:
        """Провести акт разборки."""

        async def api_call() -> DisassembleDocumentSaveResponse:
            api = await self.get_disassemble_document_api()
            return await api.post_inventory_disassemble_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.POST_INVENTORY_DISASSEMBLE_DOCUMENT, api_call
        )

    async def unpost_inventory_disassemble_document(
        self, request: GetByIDRequest
    ) -> DisassembleDocumentSaveResponse:
        """Отменить проведение акта разборки."""

        async def api_call() -> DisassembleDocumentSaveResponse:
            api = await self.get_disassemble_document_api()
            return await api.unpost_inventory_disassemble_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UNPOST_INVENTORY_DISASSEMBLE_DOCUMENT, api_call
        )

    async def cancel_inventory_disassemble_document(
        self, request: GetByIDRequest
    ) -> DisassembleDocumentSaveResponse:
        """Отменить (удалить) акт разборки."""

        async def api_call() -> DisassembleDocumentSaveResponse:
            api = await self.get_disassemble_document_api()
            return await api.cancel_inventory_disassemble_document(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CANCEL_INVENTORY_DISASSEMBLE_DOCUMENT, api_call
        )
