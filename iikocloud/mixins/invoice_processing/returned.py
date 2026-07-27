"""Invoice Processing returned invoice core mixin — обёртки SDK."""

from iikocloud_client import (
    GetByIDRequest,
    ListRequest,
    ReturnedInvoiceCreateRequest,
    ReturnedInvoiceGetResponse,
    ReturnedInvoiceListItem,
    ReturnedInvoiceSaveResponse,
    ReturnedInvoiceUpdateRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class ReturnedCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: исходящие возвратные накладные."""

    async def create_inventory_returned_invoice(
        self, request: ReturnedInvoiceCreateRequest
    ) -> ReturnedInvoiceSaveResponse:
        """Создать исходящую возвратную накладную."""

        async def api_call() -> ReturnedInvoiceSaveResponse:
            api = await self.get_returned_invoice_api()
            return await api.create_inventory_returned_invoice(
                returned_invoice_create_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_INVENTORY_RETURNED_INVOICE, api_call
        )

    async def update_inventory_returned_invoice(
        self, request: ReturnedInvoiceUpdateRequest
    ) -> ReturnedInvoiceSaveResponse:
        """Обновить исходящую возвратную накладную."""

        async def api_call() -> ReturnedInvoiceSaveResponse:
            api = await self.get_returned_invoice_api()
            return await api.update_inventory_returned_invoice(
                returned_invoice_update_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_INVENTORY_RETURNED_INVOICE, api_call
        )

    async def get_inventory_returned_invoice(
        self, request: GetByIDRequest
    ) -> ReturnedInvoiceGetResponse:
        """Исходящая возвратная накладная по id."""

        async def api_call() -> ReturnedInvoiceGetResponse:
            api = await self.get_returned_invoice_api()
            return await api.get_inventory_returned_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_INVENTORY_RETURNED_INVOICE, api_call
        )

    async def list_inventory_returned_invoices(
        self, request: ListRequest
    ) -> list[ReturnedInvoiceListItem]:
        """Список исходящих возвратных накладных за период."""

        async def api_call() -> list[ReturnedInvoiceListItem]:
            api = await self.get_returned_invoice_api()
            return await api.list_inventory_returned_invoices(list_request=request)

        return await self.execute_with_retry(
            ApiMethod.LIST_INVENTORY_RETURNED_INVOICES, api_call
        )

    async def post_inventory_returned_invoice(
        self, request: GetByIDRequest
    ) -> ReturnedInvoiceSaveResponse:
        """Провести исходящую возвратную накладную."""

        async def api_call() -> ReturnedInvoiceSaveResponse:
            api = await self.get_returned_invoice_api()
            return await api.post_inventory_returned_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.POST_INVENTORY_RETURNED_INVOICE, api_call
        )

    async def unpost_inventory_returned_invoice(
        self, request: GetByIDRequest
    ) -> ReturnedInvoiceSaveResponse:
        """Отменить проведение исходящей возвратной накладной."""

        async def api_call() -> ReturnedInvoiceSaveResponse:
            api = await self.get_returned_invoice_api()
            return await api.unpost_inventory_returned_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UNPOST_INVENTORY_RETURNED_INVOICE, api_call
        )

    async def cancel_inventory_returned_invoice(
        self, request: GetByIDRequest
    ) -> ReturnedInvoiceSaveResponse:
        """Отменить (удалить) исходящую возвратную накладную."""

        async def api_call() -> ReturnedInvoiceSaveResponse:
            api = await self.get_returned_invoice_api()
            return await api.cancel_inventory_returned_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CANCEL_INVENTORY_RETURNED_INVOICE, api_call
        )
