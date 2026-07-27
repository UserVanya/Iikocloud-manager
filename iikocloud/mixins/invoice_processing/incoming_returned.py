"""Invoice Processing incoming returned invoice core mixin — обёртки SDK."""

from iikocloud_client import (
    GetByIDRequest,
    IncomingReturnedInvoiceCreateRequest,
    IncomingReturnedInvoiceGetResponse,
    IncomingReturnedInvoiceListItem,
    IncomingReturnedInvoiceSaveResponse,
    IncomingReturnedInvoiceUpdateRequest,
    ListRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class IncomingReturnedCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: входящие возвратные накладные."""

    async def create_inventory_incoming_returned_invoice(
        self, request: IncomingReturnedInvoiceCreateRequest
    ) -> IncomingReturnedInvoiceSaveResponse:
        """Создать входящую возвратную накладную."""

        async def api_call() -> IncomingReturnedInvoiceSaveResponse:
            api = await self.get_incoming_returned_invoice_api()
            return await api.create_inventory_incoming_returned_invoice(
                incoming_returned_invoice_create_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_INVENTORY_INCOMING_RETURNED_INVOICE, api_call
        )

    async def update_inventory_incoming_returned_invoice(
        self, request: IncomingReturnedInvoiceUpdateRequest
    ) -> IncomingReturnedInvoiceSaveResponse:
        """Обновить входящую возвратную накладную."""

        async def api_call() -> IncomingReturnedInvoiceSaveResponse:
            api = await self.get_incoming_returned_invoice_api()
            return await api.update_inventory_incoming_returned_invoice(
                incoming_returned_invoice_update_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_INVENTORY_INCOMING_RETURNED_INVOICE, api_call
        )

    async def get_inventory_incoming_returned_invoice(
        self, request: GetByIDRequest
    ) -> IncomingReturnedInvoiceGetResponse:
        """Входящая возвратная накладная по id."""

        async def api_call() -> IncomingReturnedInvoiceGetResponse:
            api = await self.get_incoming_returned_invoice_api()
            return await api.get_inventory_incoming_returned_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_INVENTORY_INCOMING_RETURNED_INVOICE, api_call
        )

    async def list_inventory_incoming_returned_invoices(
        self, request: ListRequest
    ) -> list[IncomingReturnedInvoiceListItem]:
        """Список входящих возвратных накладных за период."""

        async def api_call() -> list[IncomingReturnedInvoiceListItem]:
            api = await self.get_incoming_returned_invoice_api()
            return await api.list_inventory_incoming_returned_invoices(
                list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.LIST_INVENTORY_INCOMING_RETURNED_INVOICES, api_call
        )

    async def post_inventory_incoming_returned_invoice(
        self, request: GetByIDRequest
    ) -> IncomingReturnedInvoiceSaveResponse:
        """Провести входящую возвратную накладную."""

        async def api_call() -> IncomingReturnedInvoiceSaveResponse:
            api = await self.get_incoming_returned_invoice_api()
            return await api.post_inventory_incoming_returned_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.POST_INVENTORY_INCOMING_RETURNED_INVOICE, api_call
        )

    async def unpost_inventory_incoming_returned_invoice(
        self, request: GetByIDRequest
    ) -> IncomingReturnedInvoiceSaveResponse:
        """Отменить проведение входящей возвратной накладной."""

        async def api_call() -> IncomingReturnedInvoiceSaveResponse:
            api = await self.get_incoming_returned_invoice_api()
            return await api.unpost_inventory_incoming_returned_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UNPOST_INVENTORY_INCOMING_RETURNED_INVOICE, api_call
        )

    async def cancel_inventory_incoming_returned_invoice(
        self, request: GetByIDRequest
    ) -> IncomingReturnedInvoiceSaveResponse:
        """Отменить (удалить) входящую возвратную накладную."""

        async def api_call() -> IncomingReturnedInvoiceSaveResponse:
            api = await self.get_incoming_returned_invoice_api()
            return await api.cancel_inventory_incoming_returned_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CANCEL_INVENTORY_INCOMING_RETURNED_INVOICE, api_call
        )
