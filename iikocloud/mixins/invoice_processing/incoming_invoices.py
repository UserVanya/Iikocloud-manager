"""Invoice Processing incoming invoices core mixin — обёртки SDK."""

from iikocloud_client import (
    AccountingTransactionUserResponse,
    GetByIDRequest,
    IncomingInvoice,
    IncomingInvoiceRequest,
    IncomingInvoiceSaveResponse,
    ListRequest,
    PayRequest,
    SetPaymentDateRequest,
    SetPaymentDateResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class IncomingInvoicesCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: приходные накладные (incoming invoices)."""

    async def create_inventory_incoming_invoice(
        self, request: IncomingInvoiceRequest
    ) -> IncomingInvoiceSaveResponse:
        """Создать приходную накладную."""

        async def api_call() -> IncomingInvoiceSaveResponse:
            api = await self.get_incoming_invoices_api()
            return await api.create_inventory_incoming_invoice(
                incoming_invoice_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_INVENTORY_INCOMING_INVOICE, api_call
        )

    async def update_inventory_incoming_invoice(
        self, request: IncomingInvoiceRequest
    ) -> IncomingInvoiceSaveResponse:
        """Обновить приходную накладную."""

        async def api_call() -> IncomingInvoiceSaveResponse:
            api = await self.get_incoming_invoices_api()
            return await api.update_inventory_incoming_invoice(
                incoming_invoice_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_INVENTORY_INCOMING_INVOICE, api_call
        )

    async def get_inventory_incoming_invoice(
        self, request: GetByIDRequest
    ) -> IncomingInvoice:
        """Приходная накладная по id."""

        async def api_call() -> IncomingInvoice:
            api = await self.get_incoming_invoices_api()
            return await api.get_inventory_incoming_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_INVENTORY_INCOMING_INVOICE, api_call
        )

    async def list_inventory_incoming_invoices(
        self, request: ListRequest
    ) -> list[IncomingInvoice]:
        """Список приходных накладных за период."""

        async def api_call() -> list[IncomingInvoice]:
            api = await self.get_incoming_invoices_api()
            return await api.list_inventory_incoming_invoices(list_request=request)

        return await self.execute_with_retry(
            ApiMethod.LIST_INVENTORY_INCOMING_INVOICES, api_call
        )

    async def post_inventory_incoming_invoice(
        self, request: GetByIDRequest
    ) -> IncomingInvoiceSaveResponse:
        """Провести приходную накладную."""

        async def api_call() -> IncomingInvoiceSaveResponse:
            api = await self.get_incoming_invoices_api()
            return await api.post_inventory_incoming_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.POST_INVENTORY_INCOMING_INVOICE, api_call
        )

    async def unpost_inventory_incoming_invoice(
        self, request: GetByIDRequest
    ) -> IncomingInvoiceSaveResponse:
        """Отменить проведение приходной накладной."""

        async def api_call() -> IncomingInvoiceSaveResponse:
            api = await self.get_incoming_invoices_api()
            return await api.unpost_inventory_incoming_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UNPOST_INVENTORY_INCOMING_INVOICE, api_call
        )

    async def cancel_inventory_incoming_invoice(
        self, request: GetByIDRequest
    ) -> IncomingInvoiceSaveResponse:
        """Отменить (удалить) приходную накладную."""

        async def api_call() -> IncomingInvoiceSaveResponse:
            api = await self.get_incoming_invoices_api()
            return await api.cancel_inventory_incoming_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CANCEL_INVENTORY_INCOMING_INVOICE, api_call
        )

    async def add_inventory_incoming_invoice_payment(
        self, request: PayRequest
    ) -> AccountingTransactionUserResponse:
        """Добавить оплату по приходной накладной."""

        async def api_call() -> AccountingTransactionUserResponse:
            api = await self.get_incoming_invoices_api()
            return await api.add_inventory_incoming_invoice_payment(
                pay_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_INVENTORY_INCOMING_INVOICE_PAYMENT, api_call
        )

    async def set_inventory_incoming_invoice_payment_date(
        self, request: SetPaymentDateRequest
    ) -> SetPaymentDateResponse:
        """Установить дату оплаты приходной накладной."""

        async def api_call() -> SetPaymentDateResponse:
            api = await self.get_incoming_invoices_api()
            return await api.set_inventory_incoming_invoice_payment_date(
                set_payment_date_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.SET_INVENTORY_INCOMING_INVOICE_PAYMENT_DATE, api_call
        )
